import subprocess
import ctypes

from config import PROTOCOL
from admin import relaunch_as_admin

from .internet_check import is_internet_available

class SyncResult:
    def __init__(self, success, warning=None, warning_actions=None, error=""):
        self.success = success   # هل نجحت العملية؟ (True/False)
        self.warning = warning
        self.warning_actions = warning_actions if warning else []
        self.error = error       # ما هو نص الخطأ لو فشلت؟


def sync_windows_time() -> SyncResult:
    relaunch_as_admin()
    try:
        print("🔄 Syncing Windows time started...\n")

        subprocess.run(
            "sc config w32time start= auto",
            shell=True, check=True
        )

        subprocess.run("net stop w32time", shell=True)
        subprocess.run("net start w32time", shell=True)

        peers = (
            "time.google.com,0x1 "
            "pool.ntp.org,0x1 "
            "time.windows.com,0x1"
        )

        subprocess.run(
            f'w32tm /config /manualpeerlist:"{peers}" '
            "/syncfromflags:manual /update",
            shell=True, check=True
        )

        result = subprocess.run(
            "w32tm /resync",
            shell=True,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            return SyncResult(success=True)
        else:
            raise Exception("Failed to synchronize time using Windows Service.")
    except Exception as e:
    
        manual_success = manual_ntp_sync()

        if manual_success:
            return SyncResult(
                success=True,
                warning="Time synchronized manually (fallback mode).",
                warning_actions=[("Don't show again", f"{PROTOCOL}://disable-warning")]
            )
        else:
            return SyncResult(success=False, error="Failed to synchronize time.")


def set_system_time(dt_utc):
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


def manual_ntp_sync():
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

            set_system_time(ntp_time)
            return True
        except:
            continue

    return False


def check_internet_and_sync(auto_sync=True):
    if is_internet_available(auto_sync):
        return sync_windows_time()
    else: 
        return SyncResult(success=False, error="No internet connection available to synchronize time.")
