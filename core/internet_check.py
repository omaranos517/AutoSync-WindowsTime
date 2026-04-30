from socket import create_connection

from utils import log, send_notification
from config import PROTOCOL, CANCEL_FILE


def has_internet_connection():
    """Check if there is an internet connection available."""
    for target in [("8.8.8.8", 53), ("1.1.1.1", 53)]:
        for attempt in range(2):            
            try:
                with create_connection(target, timeout=5):
                    return True
            except (OSError, TimeoutError, ConnectionRefusedError):
                continue
    log("INFO", "No internet connection detected.", console=False)
    return False


def wait_for_internet(notify=True):
    """Wait for an internet connection to become available, with user cancellation support."""
    from time import sleep
    for i in range(300): # 10 minutes max wait
        if CANCEL_FILE.exists():
            CANCEL_FILE.unlink(missing_ok=True)
            if notify:
                send_notification(
                    "Time Sync Cancelled",
                    "❌ Sync process cancelled.",
                    tag="sync-cancelled",
                    group="sync-cancelled"
                )
            log("INFO", "Time sync cancelled by user.", console=False)
            return False

        if has_internet_connection():
            return True

        if notify and i == 5:
            send_notification(
                "No Internet Connection",
                "⏳ Waiting for internet connection...",
                actions=[
                    ("Cancel", f"{PROTOCOL}://cancel")
                ],
                tag="sync-status",
                group="sync-status"
            )

        sleep(2) # Wait before retrying
    
    return False


def is_internet_available(auto_sync=True, notify=True):
    """
    Internet Check:

    - Returns True immediately if a connection is found.

    - In automatic mode: Waits for a connection and returns the result.

    - In manual mode: Returns False immediately with a log.
    """
    # 1. Fast check: if internet is already available, return True immediately.
    if has_internet_connection():
        return True

    # 2. If there is no connection yet, decide behavior based on the run mode.
    if auto_sync:
        # Automatic mode: wait until connectivity appears or timeout/cancel occurs.
        result = wait_for_internet(notify=notify)
    else:
        # Manual mode: fail immediately.
        result = False

    # 3. Return the final availability result.
    return result
