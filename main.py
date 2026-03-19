import ctypes
import sys

from utils import log, relaunch_as_admin, ensure_protocol_registered, normalize_protocol_args
from config import APP_ID
from cli.parser import get_parser
from cli import actions


# ==================================================
# COMMANDS
# ==================================================

# ==================================================
# MAIN FLOW
# ==================================================

def main():
    actions.enable_ansi_colors()
    ensure_protocol_registered()
    normalize_protocol_args()

    # parser = argparse.ArgumentParser(
    #     prog="timesync",
    #     description="Windows Time Synchronization Tool"
    # )

    # sub = parser.add_subparsers(dest="command")

    # now_parser = sub.add_parser("now")
    # now_parser.add_argument("--auto", action="store_true", help="Delayed sync for startup")

    # sub.add_parser("logs")

    # sub.add_parser("cancel")
    # sub.add_parser("disable-warning")

    # sub.add_parser("help")
    # sub.add_parser("commands")

    # sub.add_parser("status")

    # startup = sub.add_parser("startup")
    # startup_sub = startup.add_subparsers(dest="action")

    # startup_sub.add_parser("status")
    # startup_sub.add_parser("enable")
    # startup_sub.add_parser("disable")

    # resume = sub.add_parser("resume")
    # resume_sub = resume.add_subparsers(dest="action")

    # resume_sub.add_parser("status")
    # resume_sub.add_parser("enable")
    # resume_sub.add_parser("disable")

    # # إضافة قسم الإشعارات
    # notify = sub.add_parser("notify")
    # notify_sub = notify.add_subparsers(dest="action")

    # notify_sub.add_parser("status")
    # notify_sub.add_parser("enable")
    # notify_sub.add_parser("disable")

    # completion = sub.add_parser("completion")
    # completion.add_argument("shell", choices=["powershell"], help="Shell type")
    # completion.add_argument("--install", action="store_true", help="Install completion into your PowerShell profile")

    # sub.add_parser("about")
    # sub.add_parser("version")

    # args = parser.parse_args()

    parser = get_parser()
    args = parser.parse_args()

    if len(sys.argv) == 1:
        from ui import run_gui
        print("🚀 Starting TimeSync in GUI mode...")
        relaunch_as_admin()
        run_gui()
        return
        
    commands = {
        "cancel": actions.cmd_cancel,
        "disable-warning": actions.cmd_disable_warning,
        "help": actions.commands_list,
        "commands": actions.commands_list,
        "status": actions.cmd_status,
        "logs": actions.cmd_logs,
        "about": actions.cmd_about,
        "version": actions.cmd_version
    }

    action_commands = {
        "startup": actions.cmd_toggle_startup,
        "resume": actions.cmd_toggle_resume,
        "notify": actions.cmd_toggle_notify
    }

    if args.command:
        if args.command == "now":
            actions.cmd_now()

        elif args.command in commands:
            commands[args.command]()

        elif args.command in action_commands:
            action_commands[args.command](args.action or "status")

        elif args.command == "completion":
            actions.cmd_completion(args.shell, install=args.install)
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
