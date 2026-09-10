import subprocess
import ctypes

from config import PROTOCOL
from utils.admin import relaunch_as_admin
from utils import log, run_cmd

from .internet_check import is_internet_available
from .timezones import (
    get_current_windows_timezone_online_offset,
    set_windows_timezone_for_online_offset,
)

class SyncResult:
    def __init__(self, success: bool, warning: str = None, warning_actions: list = None, error: str = ""):
        self.success = success   # Whether the operation succeeded (True/False)
        self.warning = warning  # Warning message, if any
        self.warning_actions = warning_actions if warning else [] # Actions associated with the warning
        self.error = error       # Error message if the operation failed


def sync_windows_time(silent=True) -> SyncResult:
    relaunch_as_admin()
    try:
        print("🔄 Syncing Windows time started...\n")

        if _sync_with_timezone_correction(silent):
            return SyncResult(success=True)
        else:
            raise Exception("Initial sync failed.")
        
    except Exception as e:
        try:
            if fix_w32time_service(silent):
                if _sync_with_timezone_correction(silent):
                    return SyncResult(
                        success=True,
                        warning="windows time service was fixed. you may need to restart your PC for changes to take effect.",
                        warning_actions=[("Restart now", f"{PROTOCOL}://restart-pc")]
                    )
        except Exception as fix_error:
            print("We couldn't fix the w32time service automatically.")
            log("ERROR", f"Failed to fix w32time service: {fix_error}", console=True)
    
        if manual_ntp_sync():
            if _correct_windows_timezone_from_online_offset():
                manual_ntp_sync()
            return SyncResult(
                success=True,
                warning="Time synchronized manually (fallback mode).",
                warning_actions=[("Don't show again", f"{PROTOCOL}://disable-warning")]
            )
        else:
            return SyncResult(success=False, error="Failed to synchronize time.")


def _sync_with_timezone_correction(silent):
    """Synchronize, correct a detected online offset mismatch, then resync."""
    if not attempt_time_sync(silent):
        return False
    if _correct_windows_timezone_from_online_offset():
        return attempt_time_sync(silent)
    return True


def _correct_windows_timezone_from_online_offset():
    """Apply a Windows zone with TimeAPI's current offset, if needed."""
    timezone_info = get_current_windows_timezone_online_offset()
    if timezone_info is None:
        log("WARNING", "Could not verify the Windows time-zone offset online.", console=False)
        return False

    if timezone_info["matches"]:
        log(
            "INFO",
            f"Time-zone offset verified for {timezone_info['windows_id']} "
            f"({timezone_info['iana_timezone']}).",
            console=False,
        )
        return False

    target_id = set_windows_timezone_for_online_offset(timezone_info)
    if target_id is None:
        log(
            "WARNING",
            f"No installed Windows time zone matches TimeAPI's offset for "
            f"{timezone_info['iana_timezone']}.",
            console=True,
        )
        return False

    log(
        "INFO",
        f"Time zone changed from {timezone_info['windows_id']} to {target_id} "
        "to match TimeAPI's current offset.",
        console=True,
    )
    return True


def attempt_time_sync(silent) -> bool:
    try:
        run_cmd(["sc", "config", "w32time", "start=", "auto"], silent)

        run_cmd(["net", "stop", "w32time"], silent)
        run_cmd(["net", "start", "w32time"], silent)

        peers = (
            "time.google.com,0x1 "
            "pool.ntp.org,0x1 "
            "time.windows.com,0x1"
        )

        run_cmd(["w32tm", "/config", "/manualpeerlist:" + peers, "/syncfromflags:manual", "/update"], silent)

        run_cmd(["w32tm", "/resync", "/force"], silent)
        return True
        
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.strip() if e.stderr else str(e)
        raise RuntimeError(f"Resync failed with code: {stderr}")


def fix_w32time_service(silent) -> bool:    
    try:
        print("🔧 Attempting to fix w32time service...\n")

        run_cmd(["net", "stop", "w32time"], silent)
        run_cmd(["w32tm", "/unregister"], silent)
        run_cmd(["w32tm", "/register"], silent)
        run_cmd(["sc", "config", "w32time", "start=", "auto"], silent)
        run_cmd(["net", "start", "w32time"], silent)
        return True
    
    except Exception as e:
        print(f"Error while fixing w32time service: {e} \n Now attempting manual NTP synchronization...")
        return False


def _set_system_time(dt_utc):
    class SYSTEMTIME(ctypes.Structure):
        _fields_ = [
            ("wYear", ctypes.c_ushort),
            ("wMonth", ctypes.c_ushort),
            ("wDayOfWeek", ctypes.c_ushort),
            ("wDay", ctypes.c_ushort),
            ("wHour", ctypes.c_ushort),
            ("wMinute", ctypes.c_ushort),
            ("wSecond", ctypes.c_ushort),
            ("wMilliseconds", ctypes.c_ushort),
        ]

    system_time = SYSTEMTIME()
    system_time.wYear = dt_utc.year
    system_time.wMonth = dt_utc.month
    system_time.wDay = dt_utc.day
    system_time.wHour = dt_utc.hour
    system_time.wMinute = dt_utc.minute
    system_time.wSecond = dt_utc.second
    system_time.wMilliseconds = int(dt_utc.microsecond / 1000)

    ctypes.windll.kernel32.SetSystemTime(ctypes.byref(system_time))


def manual_ntp_sync() -> bool:
    print("⚠️  Windows Service synchronization failed. Trying to synchronize manually...\n")
    import ntplib
    from datetime import datetime, timezone

    peers = [
        "time.google.com",
        "pool.ntp.org",
        "time.windows.com"
    ]

    client = ntplib.NTPClient()

    for peer in peers:
        try:
            response = client.request(peer, version=3)
            ntp_time = datetime.fromtimestamp(response.tx_time, timezone.utc)

            _set_system_time(ntp_time)
            return True
        except:
            continue

    return False


def check_internet_and_sync(silent=True, notify=True):
    if is_internet_available(silent, notify=notify):
        return sync_windows_time(silent)
    else: 
        return SyncResult(success=False, error="No internet connection available to synchronize time.")
