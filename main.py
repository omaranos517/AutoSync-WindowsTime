import ctypes
import sys

from utils import (
    log,
    relaunch_as_admin,
    ensure_protocol_registered,
    normalize_protocol_args
    # remove_notification
    )
from config import APP_ID

# ==================================================
# MAIN FLOW
# ==================================================

def main():
    # A prior wait can have been interrupted by shutdown before it could remove its toast.
    # remove_notification("sync-wait", "sync-status")

    ensure_protocol_registered()
    normalize_protocol_args()

    if len(sys.argv) == 1:
        from ui import run_gui
        print("🚀 Starting TimeSync in GUI mode...")
        relaunch_as_admin()
        run_gui()
        return
    else:
        from cli.dispatcher import run_cli
        run_cli()

if __name__ == "__main__":
    # Set the process AppUserModelID for proper notification grouping in Windows 10/11. This is especially important if the app is not installed in Program Files and doesn't have a proper installer that sets the AppUserModelID.
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
    except Exception as e:
        log("WARNING", f"Failed to set process AppUserModelID: {e}", console=False)
        
    main()
