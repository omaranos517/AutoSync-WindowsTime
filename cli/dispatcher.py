from .parser import get_parser
from utils.console import enable_ansi_colors
from .commands import COMMANDS, ACTION_COMMANDS, cmd_completion, cmd_timezone


def run_cli():
    enable_ansi_colors()
    parser = get_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        print("\n\nUse 'timesync help' for more information.\n\n")
        return

    elif args.command in COMMANDS:
        if args.command == "now":
            silent = args.auto or args.silent
            notify = args.notify
            COMMANDS[args.command](silent=silent, notify=notify)
        elif args.command == "cancel":
            COMMANDS[args.command](args.cancel_session)
        else:
            COMMANDS[args.command]()

    elif args.command in ACTION_COMMANDS:
        ACTION_COMMANDS[args.command](args.action or "status")

    elif args.command == "timezone":
        query = " ".join(args.timezone) if getattr(args, "timezone", None) else None
        cmd_timezone(args.tz_action or "status", query=query)

    elif args.command == "completion":
        cmd_completion(args.shell, install=args.install)
