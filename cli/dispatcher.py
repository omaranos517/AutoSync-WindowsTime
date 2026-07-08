from .parser import get_parser
from utils.console import enable_ansi_colors
from core import actions
from .commands import COMMANDS, ACTION_COMMANDS, cmd_completion


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
        notify = args.notify
        actions.sync_time_action(silent=silent, notify=notify)

    elif args.command in COMMANDS:
        COMMANDS[args.command]()

    elif args.command in ACTION_COMMANDS:
        ACTION_COMMANDS[args.command](args.action or "status")

    elif args.command == "completion":
        cmd_completion(args.shell, install=args.install)