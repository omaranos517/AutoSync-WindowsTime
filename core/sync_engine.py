import subprocess
import ctypes

from config import APP_DIR
from settings import load_settings
from admin import relaunch_as_admin
from utils import log, send_notification

from .internet_check import is_internet_available


def sync_windows_time(auto=False):
    relaunch_as_admin()
    try:
        if not auto:
            print("🔄 Syncing Windows time started...\n")
        else:
            hwnd = ctypes.windll.kernel32.GetConsoleWindow() # جلب معرف النافذة الحالية (التي هي الـ CMD السوداء)
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 0) # إخفاء النافذة (0 تعني SW_HIDE)

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
            if auto:
                send_notification("Time Sync Success", "✅ Time synchronized successfully.")
                log("SYNC_SUCCESS", "Time synchronized successfully.", console=False)
            else:
                log("SYNC_SUCCESS", "Time synchronized successfully.", console=False)
                print("✅ Time synchronized successfully.")
            return True
        else:
            manual_success = manual_ntp_sync()

            if manual_success:
                if auto:
                    send_notification("Time Sync", "✅ Time synchronized manually.")

                    # Show warning
                    settings = load_settings()
                    if settings.get("show_warning_on_manual_sync", True):
                        disable_warning_vbs = str(APP_DIR / "ts-disable-warning.vbs")
                        send_notification(
                                            "⚠️ Warning",
                                            "Windows has a problem with time sync, so TimeSync used a manual method to sync the time. Consider fixing Windows Time Service for better performance.",
                                            actions=[
                                                ("Don't show again", disable_warning_vbs)
                                            ],
                                            warning=True
                                        )
                        log("WARNING", "Time synchronized manually (fallback mode). Windows Time Service may have issues.", console=False)
                else:
                    print("✅ Time synchronized manually (fallback mode).")
                return True
            else:
                if auto:
                    retry_vbs = str(APP_DIR / "ts-now.vbs")
                    send_notification(
                        "Time Sync Failed",
                        "❌ Time sync failed.",
                        actions=[
                            ("Retry", retry_vbs)
                        ]
                    )
                else:
                    print(result.stderr)
                log("ERROR", f"Time sync failed: {result.stderr}", console=False)
                return False

    except Exception as e:
        log("ERROR", f"Exception during time sync: {e}", console=True)
        return False


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
        return sync_windows_time(auto=auto_sync)
    else: 
        return False