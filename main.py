import ctypes
import sys

from utils import log, relaunch_as_admin, ensure_protocol_registered, normalize_protocol_args
from config import APP_ID
from cli.parser import get_parser
from cli import actions

# ==================================================
# MAIN FLOW
# ==================================================

def main():
    actions.enable_ansi_colors()
    ensure_protocol_registered()
    normalize_protocol_args()

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
        "restart-pc": actions.cmd_restart_pc,
        "status": actions.cmd_status,
        "logs": actions.cmd_logs,
        "about": actions.cmd_about,
        "version": actions.cmd_version
    }

    action_commands = {
        "startup": actions.cmd_toggle_startup,
        "periodic": actions.cmd_toggle_periodic,
        "resume": actions.cmd_toggle_resume,
        "notify": actions.cmd_toggle_notify
    }

    if args.command:
        if args.command == "now":            
            silent = args.auto or args.silent
            actions.cmd_now(silent=silent, notify=silent)

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
