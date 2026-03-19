import argparse
from config import APP_NAME

def get_parser():
    parser = argparse.ArgumentParser(
        prog="timesync",
        description=f"{APP_NAME} - Windows Time Synchronization Tool",
        formatter_class=argparse.RawTextHelpFormatter # للحفاظ على تنسيق النصوص في Help
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --- Command: now ---
    now_p = subparsers.add_parser("now", help="Sync time immediately")
    now_p.add_argument("--auto", action="store_true", help="Background sync mode")

    # --- Command: logs / status / about / version / help ---
    subparsers.add_parser("logs", help="Open logs file")
    subparsers.add_parser("status", help="Show current sync status")
    subparsers.add_parser("about", help="Show info about TimeSync")
    subparsers.add_parser("version", help="Show version")
    subparsers.add_parser("help", help="Show detailed commands list")
    
    # أوامر مخفية أو تقنية
    subparsers.add_parser("cancel", help=argparse.SUPPRESS) 
    subparsers.add_parser("disable-warning", help=argparse.SUPPRESS)

    # --- Commands with Actions (startup, resume, notify) ---
    for cmd_name in ["startup", "resume", "notify"]:
        cmd_p = subparsers.add_parser(cmd_name, help=f"Manage {cmd_name} features")
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