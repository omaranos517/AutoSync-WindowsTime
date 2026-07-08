import argparse
from config import APP_NAME

def get_parser():
    parser = argparse.ArgumentParser(
        prog="timesync",
        description=f"{APP_NAME} - Windows Time Synchronization Tool",
        formatter_class=argparse.RawTextHelpFormatter # Preserve help text formatting
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --- Command: now ---
    now_p = subparsers.add_parser("now", help="Sync time immediately")
    now_p.add_argument("--auto", action="store_true", help="Background sync mode")
    now_p.add_argument("--silent", action="store_true", help="Background sync mode")
    now_p.add_argument("--notify", action="store_true", help="Background sync mode")

    # --- Command: logs / status / about / version / help ---
    subparsers.add_parser("status", help="Show current sync status")
    subparsers.add_parser("logs", help="Open logs file")
    subparsers.add_parser("about", help="Show info about TimeSync")
    subparsers.add_parser("version", help="Show version")
    
    # --- Hidden Commands ---
    subparsers.add_parser("cancel") 
    subparsers.add_parser("disable-warning")
    subparsers.add_parser("restart-pc")

    # --- Commands with Actions (startup, resume, notify) ---
    for cmd_name, cmd_help in {"startup" : "This feature manages the startup sync task", "periodic" : "This feature manages the periodic sync task", "resume" : "This feature manages the resume sync task", "notify" : "This feature manages the notifications for TimeSync"}.items():
        cmd_p = subparsers.add_parser(cmd_name, help=cmd_help)
        cmd_p.add_argument(
            "action",
            nargs="?",
            choices=["status", "enable", "disable"],
            default="status",
            help="Action to perform"
        )

    # --- Command: completion ---
    comp_p = subparsers.add_parser("completion", help="Shell autocomplete setup")
    comp_p.add_argument("shell", choices=["powershell"], help="Target shell")
    comp_p.add_argument("--install", action="store_true", help="Install to profile")

    return parser
