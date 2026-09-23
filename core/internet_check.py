from socket import create_connection
from secrets import token_urlsafe
from time import time

from utils import (
    log,
    send_notification
    # remove_notification
)
from config import PROTOCOL, CANCEL_FILE


def has_internet_connection():
    """Check if there is an internet connection available."""
    for target in [("8.8.8.8", 53), ("1.1.1.1", 53)]:
        for attempt in range(2):
            try:
                with create_connection(target, timeout=5):
                    return True
            except (OSError, TimeoutError):
                continue
    return False


def wait_for_internet(notify=True):
    """Wait for an internet connection, allowing cancellation of this session only."""
    from time import sleep

    start_time = time()
    max_wait_time = start_time + 600  # Includes time spent asleep/hibernating.
    session_id = token_urlsafe(16)
    notify_sent = False

    # A click on an old toast creates a stale flag; discard it before this run starts.
    CANCEL_FILE.unlink(missing_ok=True)
    try:
        while time() < max_wait_time:
            if CANCEL_FILE.exists():
                cancelled_session = CANCEL_FILE.read_text(encoding="utf-8").strip()
                CANCEL_FILE.unlink(missing_ok=True)
                if not cancelled_session or cancelled_session == session_id:
                    if notify:
                        send_notification(
                            "Time Sync Cancelled",
                            "Sync process cancelled.",
                            tag="sync-cancelled",
                            group="sync-cancelled",
                        )
                    log("INFO", "Time sync cancelled by user.", console=False)
                    return False
                # This cancellation belongs to an older waiting notification.
                continue

            if has_internet_connection():
                return True

            if notify and not notify_sent and time() - start_time >= 180:
                notify_sent = True
                send_notification(
                    "No Internet Connection",
                    "⏳ Waiting for internet connection...",
                    actions=[("Cancel", f"{PROTOCOL}://cancel?session={session_id}")],
                    tag="sync-wait",
                    group="sync-status",
                )

            sleep(2)
        return False
    finally:
        # Do not leave an actionable waiting toast after this process stops.
        """
        if notify and notify_sent:
            remove_notification("sync-wait", "sync-status")
        """
        pass


def is_internet_available(auto_sync=True, notify=True):
    """
    Internet Check:

    - Returns True immediately if a connection is found.

    - In automatic mode: Waits for a connection and returns the result.

    - In manual mode: Returns False immediately with a log.
    """
    if has_internet_connection():
        return True
    if auto_sync and wait_for_internet(notify=notify):
        return True

    log("INFO", "No internet connection detected.", console=False)
    return False
