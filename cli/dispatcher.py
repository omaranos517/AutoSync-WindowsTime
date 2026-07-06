from .parser import get_parser
from utils.console import enable_ansi_colors
from core import actions


COMMANDS = {
    "cancel": actions.create_cancel_file,
    "disable-warning": actions.disable_warning_action,
    "restart-pc": actions.restart_pc,
    "status": actions.get_status,
    "logs": actions.open_logs,
    "about": actions.cmd_about,
    "version": actions.cmd_version,
}

ACTION_COMMANDS = {
    "startup": actions.toggle_startup,
    "periodic": actions.toggle_periodic,
    "resume": actions.toggle_resume,
    "notify": actions.toggle_notify,
}


def run_cli():
    enable_ansi_colors()
    parser = get_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        print("\n\nUse 'timesync help' for more information.\n\n")
        return

    if args.command == "now":
        silent = args.auto or args.silent
        actions.sync_time_action(silent=silent, notify=silent)

    elif args.command in COMMANDS:
        COMMANDS[args.command]()

    elif args.command in ACTION_COMMANDS:
        ACTION_COMMANDS[args.command](args.action or "status")

    elif args.command == "completion":
        actions.cmd_completion(args.shell, install=args.install)