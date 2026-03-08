import ctypes
import sys
import argparse

from admin import relaunch_as_admin, is_admin
from settings import load_settings, save_settings
from utils import log
from config import APP_DIR, APP_ID, STARTUP_TASK_NAME, RESUME_TASK_NAME, CANCEL_FILE, LOG_FILE, AUTHOR, VERSION, GITHUB

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
        "uninstall":     "Remove TimeSync from your PC",
        "about":         "Show info about TimeSync",
        "version":       "Show version"
    }

    max_len = max(len(cmd) for cmd in commands.keys()) + 2

    print("\n=== TimeSync Commands ===\n")
    for command, description in commands.items():
        print(f"{command:<{max_len}} - {description}")

    print("\nUse 'timesync <command> -h' for more info on each command.")

    if not is_admin():
        print("\n⚠️ TimeSync is not running as Administrator. Some commands may not work As expected. Please run the terminal as Administrator for the best experience.")


def cmd_now():
    print("🔄 Syncing time now...")
    from core.sync_engine import check_internet_and_sync
    return check_internet_and_sync(auto_sync="--auto" in sys.argv)


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

    print("🔐 Running as Administrator" if is_admin() else "⚠️ Not running as Administrator")
    print("🚀 Startup with Windows: Enabled" if task_exists(STARTUP_TASK_NAME) else "🚫 Startup with Windows: Disabled")
    print("💤 Sync on Wake: Enabled" if task_exists(RESUME_TASK_NAME) else "🚫 Sync on Wake: Disabled")
    print("🔔 Notifications: Enabled" if load_settings().get("notifications", True) else "🚫 Notifications: Disabled")
    print("\n💡 Just type 'timesync' without arguments to open the Graphical Interface")
    print("\nFor more details, check the log file at:", LOG_FILE)
    print("\n")


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

    print(f"✅ {name} enabled" if exists_fn() else f"❌ {name} disabled")


def cmd_toggle_startup(action=None):
    from core.task_scheduler import task_exists, create_startup_task, remove_startup_task
    toggle_feature(
        action,
        lambda: task_exists(STARTUP_TASK_NAME),
        lambda: create_startup_task(APP_DIR / "timesync-gui.exe"),
        remove_startup_task,
        "Startup"
    )


def cmd_toggle_resume(action=None):
    from core.task_scheduler import task_exists, create_resume_task, remove_resume_task
    toggle_feature(
        action,
        lambda: task_exists(RESUME_TASK_NAME),
        lambda: create_resume_task(APP_DIR / "timesync-gui.exe"),
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
    status = "enabled" if settings["notifications"] else "disabled"
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

# ==================================================
# MAIN FLOW
# ==================================================

def main():
    parser = argparse.ArgumentParser(
        prog="timesync",
        description="Windows Time Synchronization Tool"
    )

    sub = parser.add_subparsers(dest="command")

    now_parser = sub.add_parser("now")
    now_parser.add_argument("--auto", action="store_true", help="Delayed sync for startup")

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

    sub.add_parser("about")
    sub.add_parser("version")

    args = parser.parse_args()

    if "--auto" in sys.argv:
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)

    if len(sys.argv) == 1:
        from ui import run_gui
        print("🚀 Starting TimeSync in GUI mode...")
        relaunch_as_admin()
        run_gui()
        return
        
    commands = {
        "cancel": cmd_cancel,
        "disable-warning": cmd_disable_warning,
        "help": commands_list,
        "commands": commands_list,
        "status": cmd_status,
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
