import os
import sys
import ctypes
from pathlib import Path

from utils import log, is_admin, _protocol_exe_path
from config import APP_DIR, STARTUP_TASK_NAME, RESUME_TASK_NAME, CANCEL_FILE, LOG_FILE, AUTHOR, VERSION, GITHUB
from config.settings import load_settings, save_settings


TOP_LEVEL_COMMANDS = [
    "now",
    "logs",
    "help",
    "commands",
    "status",
    "startup",
    "resume",
    "notify",
    "about",
    "version",
]

ACTION_COMMANDS = {
    "startup": ["status", "enable", "disable"],
    "resume": ["status", "enable", "disable"],
    "notify": ["status", "enable", "disable"],
}

class Color:
    DEFFAULT = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"


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
    return f"{color}{text}{Color.DEFFAULT}"


def success_text(text):
    return colorize(text, Color.GREEN)


def error_text(text):
    return colorize(text, Color.RED)


def warning_text(text):
    return colorize(text, Color.YELLOW)


def info_text(text):
    return colorize(text, Color.CYAN)


def enabled_disabled_text(enabled):
    return success_text("Enabled") if enabled else error_text("Disabled")


def commands_list():
    """Prints a list of available commands with descriptions. If not running as admin, shows a warning about potential limitations."""
    commands = {
        "now":           "Sync time immediately",
        "commands/help": "Show Every available command",
        "status":        "Show current status",
        "startup":       "Enable/disable startup sync",
        "resume":        "Enable/disable resume on wake (Sleep/hibernate)",
        "notify":        "Enable/disable notifications",
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


def cmd_now() -> str:
    """Main command to sync time immediately. Returns a status message indicating success, failure, or any warnings."""
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
            if "--auto" in sys.argv:
                send_notification(
                    "Time Sync Warning",
                    f"⚠️ {result.warning}",
                    actions=result.warning_actions,
                    tag="sync-warning",
                    group="sync-warning"
                )
            log("SYNC_WARNING", result.warning, console=False)
            return f"Warning: {result.warning}"
        return "Success: Time synchronized successfully."
    else:
        print(error_text(f"❌ Time synchronization failed: {result.error}"))
        send_notification(
            "Time Sync Failed",
            f"❌ Time synchronization failed: {result.error}",
            tag="sync-status",
            group="sync-status"
        )
        log("SYNC_FAILED", f"Time synchronization failed: {result.error}", console=False)
        return f"Failed: {result.error}"


def cmd_status():
    """Shows the current status of TimeSync, including whether it's running as administrator, if startup and resume tasks are enabled, and if notifications are on. Also provides a reminder about the graphical interface and where to find logs."""
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
    """Opens the log file in the default text editor. If the log file doesn't exist, shows a warning message."""
    print(info_text("Logs file opening..."))
    try:
        if LOG_FILE.exists():
            os.startfile(LOG_FILE)
        else:
            print(warning_text("No logs found."))
    except Exception as e:
        print(error_text(f"Failed to open logs: {e}"))


def toggle_feature(action, exists_fn, enable_fn, disable_fn, name):
    """Generic function to toggle a feature on/off based on the provided action. It checks the current state using exists_fn, enables or disables the feature accordingly, and then prints the new status."""
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
    """Enables, disables, or shows the status of the startup sync feature. Uses the task scheduler to create or remove a task that runs TimeSync on Windows startup."""
    from core.task_scheduler import task_exists, create_startup_task, remove_startup_task
    toggle_feature(
        action,
        lambda: task_exists(STARTUP_TASK_NAME),
        lambda: create_startup_task(_protocol_exe_path()),
        remove_startup_task,
        "Startup"
    )


def cmd_toggle_resume(action=None):
    """Enables, disables, or shows the status of the resume on wake feature. Uses the task scheduler to create or remove a task that runs TimeSync when the computer wakes from sleep or hibernate."""
    from core.task_scheduler import task_exists, create_resume_task, remove_resume_task
    toggle_feature(
        action,
        lambda: task_exists(RESUME_TASK_NAME),
        lambda: create_resume_task(_protocol_exe_path()),
        remove_resume_task,
        "Resume"
    )


def cmd_toggle_notify(action=None):
    """Enables, disables, or shows the status of notifications. Updates the settings file to reflect the new state and prints the current status."""
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
    """Prints information about the TimeSync tool, including version, author, and GitHub link, in a formatted box."""
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



# ==================================================
# AUTO COMANDS 
# ==================================================

def build_powershell_completion_script():
    """Builds a PowerShell script for command auto-completion based on the defined top-level commands and action commands. It loads a template script, replaces placeholders with the actual commands, and returns the final script content."""
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
    """Generates and optionally installs the command auto-completion script for the specified shell. Currently supports PowerShell. If install is True, it adds the script to the user's PowerShell profile; otherwise, it just prints the script content."""
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
# notifications actions
# ==================================================

def cmd_cancel():
    """Creates a cancel file that signals the background sync process to stop. If the file cannot be created, logs an error message."""
    try:
        CANCEL_FILE.touch()
    except Exception as e:
        log("ERROR", f"Failed to create cancel file: {e}", console=False)


def cmd_disable_warning():
    """Updates the settings to disable warnings on manual sync. This is intended to be used as an action for a notification button, allowing users to easily turn off warnings if they find them annoying."""
    settings = load_settings()
    settings["show_warning_on_manual_sync"] = False
    save_settings(settings)
    log("INFO", "Warning on manual sync has been disabled.", console=False)


def cmd_restart_pc():
    """
    Restart the PC immediately.
    Switches used:
    /r : restart
    /t 0 : remaining time (zero seconds)
    /f : force-close open applications to prevent the process from hanging
    """
    print("🔌 Restarting PC now...")
    try:
        ctypes.windll.shell32.ShellExecuteW(None, "open", "shutdown.exe", "/r /t 0 /f", None, 0)
    except Exception as e:
        log("ERROR", f"Failed to restart PC: {e}", console=True)
