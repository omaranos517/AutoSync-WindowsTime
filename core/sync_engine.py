import subprocess
import ctypes

from config import PROTOCOL
from utils.admin import relaunch_as_admin
from utils import log, run_cmd

from .internet_check import is_internet_available

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

        if attempt_time_sync(silent):
            return SyncResult(success=True)
        else:
            raise Exception("Initial sync failed.")
        
    except Exception as e:
        try:
            if fix_w32time_service(silent):
                if attempt_time_sync(silent):
                    return SyncResult(
                        success=True,
                        warning="windows time service was fixed. you may need to restart your PC for changes to take effect.",
                        warning_actions=[("Restart now", f"{PROTOCOL}://restart-pc")]
                    )
        except Exception as fix_error:
            print("We couldn't fix the w32time service automatically.")
            log("ERROR", f"Failed to fix w32time service: {fix_error}", console=True)
    
        if manual_ntp_sync():
            return SyncResult(
                success=True,
                warning="Time synchronized manually (fallback mode).",
                warning_actions=[("Don't show again", f"{PROTOCOL}://disable-warning")]
            )
        else:
            return SyncResult(success=False, error="Failed to synchronize time.")


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
        raise RuntimeError(f"Resync failed with code: {e.stderr.strip()}")


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
