import ctypes
import os
import sys
import argparse
from urllib.parse import urlparse, parse_qs
from pathlib import Path

from admin import relaunch_as_admin, is_admin
from settings import load_settings, save_settings
from utils import log
from config import APP_DIR, APP_ID, APP_NAME, PROTOCOL, STARTUP_TASK_NAME, RESUME_TASK_NAME, CANCEL_FILE, LOG_FILE, AUTHOR, VERSION, GITHUB


TOP_LEVEL_COMMANDS = [
    "now",
    "logs",
    "help",
    "commands",
    "status",
    "startup",
    "resume",
    "notify",
    "completion",
    "about",
    "version",
]

ACTION_COMMANDS = {
    "startup": ["status", "enable", "disable"],
    "resume": ["status", "enable", "disable"],
    "notify": ["status", "enable", "disable"],
}

ANSI_RESET = "\033[0m"
ANSI_COLORS = {
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "cyan": "\033[96m",
}


def _protocol_exe_path():
    candidate = APP_DIR / "timesync-gui.exe"
    if candidate.exists():
        return candidate
    return None


def enable_ansi_colors():
    if os.name != "nt":
        return

    try:
        handle = ctypes.windll.kernel32.GetStdHandle(-11)
        if handle == 0:
            return

        mode = ctypes.c_uint()
        if ctypes.windll.kernel32.GetConsoleMode(handle, ctypes.byref(mode)) == 0:
            return

        virtual_terminal = 0x0004
        if mode.value & virtual_terminal:
            return

        ctypes.windll.kernel32.SetConsoleMode(handle, mode.value | virtual_terminal)
    except Exception:
        pass


def colorize(text, color):
    return f"{ANSI_COLORS.get(color, '')}{text}{ANSI_RESET}"


def success_text(text):
    return colorize(text, "green")


def error_text(text):
    return colorize(text, "red")


def warning_text(text):
    return colorize(text, "yellow")


def info_text(text):
    return colorize(text, "cyan")


def enabled_disabled_text(enabled):
    return success_text("Enabled") if enabled else error_text("Disabled")


def ensure_protocol_registered():
    exe_path = _protocol_exe_path()
    if not exe_path:
        return

    try:
        import winreg

        base_key = fr"Software\Classes\{PROTOCOL}"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, base_key) as k:
            winreg.SetValueEx(k, None, 0, winreg.REG_SZ, f"URL:{APP_NAME} Protocol")
            winreg.SetValueEx(k, "URL Protocol", 0, winreg.REG_SZ, "")

        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, base_key + r"\DefaultIcon") as k:
            winreg.SetValueEx(k, None, 0, winreg.REG_SZ, f"{exe_path},1")

        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, base_key + r"\shell\open\command") as k:
            winreg.SetValueEx(k, None, 0, winreg.REG_SZ, f"\"{exe_path}\" \"%1\"")
    except Exception as e:
        log("WARNING", f"Failed to register protocol: {e}", console=False)


def normalize_protocol_args():
    if len(sys.argv) != 2:
        return

    raw = sys.argv[1]
    if not raw.startswith(f"{PROTOCOL}://"):
        return

    parsed = urlparse(raw)
    command = parsed.netloc or parsed.path.lstrip("/")
    if not command:
        return

    sys.argv = [sys.argv[0], command]
    if command == "now":
        query = parse_qs(parsed.query or "")
        if query.get("auto", ["0"])[0] == "1":
            sys.argv.append("--auto")

# ==================================================
# COMMANDS
# ==================================================

def commands_list():
    commands = {
        "now":           "Sync time immediately",
        "Commands/help": "Show Every available command",
        "status":        "Show current status",
        "startup":       "Enable/disable startup sync",
        "resume":        "Enable/disable resume on wake (Sleep/hibernate)",
        "notify":        "Enable/disable notifications",
        "completion":    "Print or install shell autocomplete",
        "logs":          "Open logs file",
        "about":         "Show info about TimeSync",
        "version":       "Show version"
    }

    max_len = max(len(cmd) for cmd in commands.keys()) + 2

    print("\n=== TimeSync Commands ===\n")
    for command, description in commands.items():
        print(f"{command:<{max_len}} - {description}")

    print("\nUse 'timesync <command> -h' for more info on each command.")

    if not is_admin():
        print(f"\n{warning_text('⚠️ TimeSync is not running as Administrator. Some commands may not work As expected. Please run the terminal as Administrator for the best experience.')}")


def cmd_now():
    print(info_text("🔄 Syncing time now..."))
    from core.sync_engine import check_internet_and_sync
    from utils import send_notification

    result = check_internet_and_sync(auto_sync="--auto" in sys.argv)

    if result.success:
        print(success_text("✅ Time synchronized successfully!"))
        log("SYNC_SUCCESS", "Time synchronized successfully.", console=False)
        
        if "--auto" in sys.argv:
            send_notification(
                "Time Sync Success",
                "✅ Time synchronized successfully.",
                tag="sync-status",
                group="sync-status"
            )
        
        if result.warning:
            print(warning_text(f"⚠️ Warning: {result.warning}"))
            send_notification(
                "Time Sync Warning",
                f"⚠️ {result.warning}",
                actions=result.warning_actions,
                tag="sync-warning",
                group="sync-warning"
            )
            log("SYNC_WARNING", result.warning, console=False)
        return True
    else:
        print(error_text(f"❌ Time synchronization failed: {result.error}"))
        send_notification(
            "Time Sync Failed",
            f"❌ Time synchronization failed: {result.error}",
            tag="sync-status",
            group="sync-status"
        )
        log("SYNC_FAILED", f"Time synchronization failed: {result.error}", console=False)
        return False


def cmd_cancel():
    try:
        CANCEL_FILE.touch()
    except Exception as e:
        log("ERROR", f"Failed to create cancel file: {e}", console=False)


def cmd_disable_warning():
    settings = load_settings()
    settings["show_warning_on_manual_sync"] = False
    save_settings(settings)
    log("INFO", "Warning on manual sync has been disabled.", console=False)


def cmd_status():
    from core.task_scheduler import task_exists
    print("\n=== TimeSync Status ===\n")

    print(success_text("🔐 Running as Administrator") if is_admin() else warning_text("⚠️ Not running as Administrator"))
    print(f"🚀 Startup with Windows: {enabled_disabled_text(task_exists(STARTUP_TASK_NAME))}")
    print(f"💤 Sync on Wake: {enabled_disabled_text(task_exists(RESUME_TASK_NAME))}")
    print(f"🔔 Notifications: {enabled_disabled_text(load_settings().get('notifications', True))}")
    print("\n💡 Just type 'timesync' without arguments to open the Graphical Interface")
    print("\nFor more details, check the log file at:", LOG_FILE)
    print("\n")


def cmd_logs():
    print(info_text("Logs file opening..."))
    try:
        if LOG_FILE.exists():
            os.startfile(LOG_FILE)
        else:
            print(warning_text("No logs found."))
    except Exception as e:
        print(error_text(f"Failed to open logs: {e}"))


def toggle_feature(action, exists_fn, enable_fn, disable_fn, name):
    if action == "enable":
        enable_fn()
    elif action == "disable":
        disable_fn()
    elif action == "status":
        pass
    else:  # toggle
        if exists_fn():
            disable_fn()
        else:
            enable_fn()

    is_enabled = exists_fn()
    status_text = success_text("enabled") if is_enabled else error_text("disabled")
    icon = "✅" if is_enabled else "❌"
    print(f"{icon} {name} {status_text}")


def cmd_toggle_startup(action=None):
    from core.task_scheduler import task_exists, create_startup_task, remove_startup_task
    toggle_feature(
        action,
        lambda: task_exists(STARTUP_TASK_NAME),
        lambda: create_startup_task(_protocol_exe_path()),
        remove_startup_task,
        "Startup"
    )


def cmd_toggle_resume(action=None):
    from core.task_scheduler import task_exists, create_resume_task, remove_resume_task
    toggle_feature(
        action,
        lambda: task_exists(RESUME_TASK_NAME),
        lambda: create_resume_task(_protocol_exe_path()),
        remove_resume_task,
        "Resume"
    )


def cmd_toggle_notify(action=None):
    settings = load_settings()
    current = settings.get("notifications", True)
    
    if action == "enable":
        settings["notifications"] = True
    elif action == "disable":
        settings["notifications"] = False
    elif action != "status":
        # toggle
        settings["notifications"] = not current

    save_settings(settings)
    is_enabled = settings["notifications"]
    status = success_text("enabled") if is_enabled else error_text("disabled")
    print(f"🔔 Notifications {status}.")


def cmd_about():
    print(f"""
╔══════════════════════════════════════════════╗
║                  TimeSync Tool               ║
╠══════════════════════════════════════════════╣
║
║  Version  : {VERSION}V
║  Author   : {AUTHOR}
║  GitHub   : {GITHUB}
║
╠══════════════════════════════════════════════╣
║        Windows Time Synchronization Tool     ║
╚══════════════════════════════════════════════╝
""")

def cmd_version(): print(f"TimeSync v{VERSION}")


def build_powershell_completion_script():
    top_commands = ", ".join(f"'{cmd}'" for cmd in TOP_LEVEL_COMMANDS)
    action_lines = []
    for name, actions in ACTION_COMMANDS.items():
        quoted_actions = ", ".join("'" + action + "'" for action in actions)
        action_lines.append(f"    {name} = @({quoted_actions})")
    action_map = "\n".join(action_lines)
    template_candidates = [
        APP_DIR / "timesync-completion.ps1",
        Path(__file__).resolve().parent / "assets" / "timesync-completion.ps1",
    ]

    template_path = next((path for path in template_candidates if path.exists()), None)
    if not template_path:
        raise FileNotFoundError("timesync-completion.ps1 template was not found.")

    template = template_path.read_text(encoding="utf-8")
    return (
        template
        .replace("__TOP_LEVEL_COMMANDS__", top_commands)
        .replace("__ACTION_MAP__", action_map)
    )


def cmd_completion(shell, install=False):
    if shell != "powershell":
        print(error_text(f"Unsupported shell: {shell}"))
        return

    script = build_powershell_completion_script()

    if not install:
        print(script)
        return

    start_marker = "# >>> TimeSync autocomplete >>>"
    end_marker = "# <<< TimeSync autocomplete <<<"
    block = f"{start_marker}\n{script.rstrip()}\n{end_marker}\n"
    profile_paths = [
        Path.home() / "Documents" / "PowerShell" / "Microsoft.PowerShell_profile.ps1",
        Path.home() / "Documents" / "WindowsPowerShell" / "Microsoft.PowerShell_profile.ps1",
    ]

    installed_paths = []
    for profile_path in profile_paths:
        profile_path.parent.mkdir(parents=True, exist_ok=True)

        existing = profile_path.read_text(encoding="utf-8") if profile_path.exists() else ""
        if start_marker in existing and end_marker in existing:
            start_index = existing.index(start_marker)
            end_index = existing.index(end_marker) + len(end_marker)
            existing = existing[:start_index].rstrip() + "\n\n" + existing[end_index:].lstrip()

        new_content = existing.rstrip()
        if new_content:
            new_content += "\n\n"
        new_content += block

        profile_path.write_text(new_content, encoding="utf-8")
        installed_paths.append(profile_path)

    print(success_text("PowerShell autocomplete installed to:"))
    for profile_path in installed_paths:
        print(f"- {profile_path}")
    print(info_text("Restart PowerShell, or run one of:"))
    for profile_path in installed_paths:
        print(f". '{profile_path}'")

# ==================================================
# MAIN FLOW
# ==================================================

def main():
    enable_ansi_colors()
    ensure_protocol_registered()
    normalize_protocol_args()

    parser = argparse.ArgumentParser(
        prog="timesync",
        description="Windows Time Synchronization Tool"
    )

    sub = parser.add_subparsers(dest="command")

    now_parser = sub.add_parser("now")
    now_parser.add_argument("--auto", action="store_true", help="Delayed sync for startup")

    sub.add_parser("logs")

    sub.add_parser("cancel")
    sub.add_parser("disable-warning")

    sub.add_parser("help")
    sub.add_parser("commands")

    sub.add_parser("status")

    startup = sub.add_parser("startup")
    startup_sub = startup.add_subparsers(dest="action")

    startup_sub.add_parser("status")
    startup_sub.add_parser("enable")
    startup_sub.add_parser("disable")

    resume = sub.add_parser("resume")
    resume_sub = resume.add_subparsers(dest="action")

    resume_sub.add_parser("status")
    resume_sub.add_parser("enable")
    resume_sub.add_parser("disable")

    # إضافة قسم الإشعارات
    notify = sub.add_parser("notify")
    notify_sub = notify.add_subparsers(dest="action")

    notify_sub.add_parser("status")
    notify_sub.add_parser("enable")
    notify_sub.add_parser("disable")

    completion = sub.add_parser("completion")
    completion.add_argument("shell", choices=["powershell"], help="Shell type")
    completion.add_argument("--install", action="store_true", help="Install completion into your PowerShell profile")

    sub.add_parser("about")
    sub.add_parser("version")

    args = parser.parse_args()

    if "--auto" in sys.argv:
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)

    if len(sys.argv) == 1:
        from ui import run_gui
        print(info_text("🚀 Starting TimeSync in GUI mode..."))
        relaunch_as_admin()
        run_gui()
        return
        
    commands = {
        "cancel": cmd_cancel,
        "disable-warning": cmd_disable_warning,
        "help": commands_list,
        "commands": commands_list,
        "status": cmd_status,
        "logs": cmd_logs,
        "about": cmd_about,
        "version": cmd_version
    }

    action_commands = {
        "startup": cmd_toggle_startup,
        "resume": cmd_toggle_resume,
        "notify": cmd_toggle_notify
    }

    if args.command:
        if args.command == "now":
            cmd_now()

        elif args.command in commands:
            commands[args.command]()

        elif args.command in action_commands:
            action_commands[args.command](args.action or "status")

        elif args.command == "completion":
            cmd_completion(args.shell, install=args.install)
    else:
        parser.print_help()
        print("\n\nUse 'timesync help' for more information.\n\n")


if __name__ == "__main__":
    # Set the process AppUserModelID for proper notification grouping in Windows 10/11. This is especially important if the app is not installed in Program Files and doesn't have a proper installer that sets the AppUserModelID.
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
    except Exception as e:
        log("WARNING", f"Failed to set process AppUserModelID: {e}", console=False)
        
    main()
