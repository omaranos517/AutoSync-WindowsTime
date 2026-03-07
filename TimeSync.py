import subprocess
import ctypes
import sys
import argparse
from pathlib import Path
from time import sleep
from admin import relaunch_as_admin, is_admin
from settings import load_settings, save_settings
from utils import send_notification, log
from config import APP_DIR, APP_ID, STARTUP_TASK_NAME, RESUME_TASK_NAME, CANCEL_FILE, LOG_FILE, AUTHOR, VERSION, GITHUB

# ==================================================
# STARTUP TASK (TASK SCHEDULER)
# ==================================================

def create_startup_task(executable_path: Path = None):
    relaunch_as_admin()

    if executable_path is None:
        executable_path = APP_DIR / "timesync-gui.exe"  # Use the GUI version for startup to provide a better user experience on boot. The GUI will then launch the core sync process in the background and exit immediately, so it won't cause any noticeable delay during startup. This also allows us to show notifications if needed during startup sync.

    # إنشاء مهمة مجدولة تعمل مع دخول المستخدم بأعلى صلاحيات
    task_name = STARTUP_TASK_NAME

    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = 0

    cmd = (
        f'schtasks /create /tn "{task_name}" /tr "\\"{executable_path}\\" now --auto" '
        f'/sc onlogon /rl highest /f'
    )
    
    try:
        subprocess.run(cmd, shell=True, check=True, capture_output=True, startupinfo=startupinfo)
        log("INFO", "Startup task created in Task Scheduler (Admin Privileges)", console=True)
        
    except subprocess.CalledProcessError as e:
        log("ERROR", f"Failed to create startup task: {e}", console=True)


def create_resume_task(executable_path: Path = None):
    relaunch_as_admin()

    if executable_path is None:
        executable_path = APP_DIR / "timesync-gui.exe"  # Use the GUI version for resume to provide a better user experience on wake. The GUI will then launch the core sync process in the background and exit immediately, so it won't cause any noticeable delay during wake. This also allows us to show notifications if needed during resume sync.

    task_name = RESUME_TASK_NAME

    cmd = (
        f'schtasks /create /tn "{task_name}" '
        f'/tr "\\"{executable_path}\\" now --auto" '
        f'/sc onevent /ec System '
        f'/mo "*[System[Provider[@Name=\'Power-Troubleshooter\'] and EventID=1]]" '
        f'/rl highest /f'
    )

    try:
        subprocess.run(cmd, shell=True, check=True)
        log("INFO", "Resume task created in Task Scheduler (Admin Privileges)", console=True)
    except subprocess.CalledProcessError as e:
        log("ERROR", f"Failed to create resume task: {e}", console=True)


def remove_startup_task():
    relaunch_as_admin()

    task_name = STARTUP_TASK_NAME
    cmd = f'schtasks /delete /tn "{task_name}" /f'
    try:
        # كتم المخرجات لكي لا يظهر خطأ إذا كانت المهمة غير موجودة أصلاً
        subprocess.run(cmd, shell=True, check=True, capture_output=True)
        log("INFO", "Startup task removed successfully.", console=True)
    except subprocess.CalledProcessError:
        log("ERROR", "Startup task not found or already removed.", console=True)


def remove_resume_task():
    relaunch_as_admin()
    task_name = RESUME_TASK_NAME
    cmd = f'schtasks /delete /tn "{task_name}" /f'
    try:
        subprocess.run(cmd, shell=True, check=True, capture_output=True)
        log("INFO", "Resume task removed successfully.", console=True)
    except subprocess.CalledProcessError:
        log("ERROR", "Resume task not found or already removed.", console=True)


def startup_exists():
    task_name = STARTUP_TASK_NAME
    cmd = f'schtasks /query /tn "{task_name}"'
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return task_name in result.stdout
    except:
        return False


def resume_exists():
    task_name = RESUME_TASK_NAME
    cmd = f'schtasks /query /tn "{task_name}"'
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return task_name in result.stdout
    except:
        return False

# ==================================================
# TIME SYNC CORE
# ==================================================

def has_internet_connection():
    """تحقق مما إذا كان هناك اتصال بالإنترنت"""
    
    from socket import create_connection
    try:
        # محاولة الاتصال بـ DNS جوجل للتأكد من وجود إنترنت
        conn = create_connection(("8.8.8.8", 53), timeout=3)
        conn.close()
        return True
    except OSError:
        log("INFO", "No internet connection detected.", console=False)
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


def sync_windows_time():
    relaunch_as_admin()
    try:
        is_auto = "--auto" in sys.argv

        if not is_auto:
            if not has_internet_connection():
                print("❌ No internet connection. Please connect to the internet and try again.")
                log("ERROR", "No internet connection detected in manual sync.", console=False)
                return
            
            print("🔄 Syncing Windows time...\n")
        else:
            hwnd = ctypes.windll.kernel32.GetConsoleWindow() # جلب معرف النافذة الحالية (التي هي الـ CMD السوداء)
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 0) # إخفاء النافذة (0 تعني SW_HIDE)

            connection = False
            for i in range(60):
                if CANCEL_FILE.exists():
                    CANCEL_FILE.unlink()
                    send_notification("Time Sync Cancelled", "❌ Sync process cancelled.")
                    log("INFO", "Time sync cancelled by user.", console=False)
                    return

                if has_internet_connection():
                    connection = True
                    break

                if i == 5:
                    cancel_vbs = str(APP_DIR / "ts-cancel.vbs")
                    send_notification(
                        "No Internet Connection",
                        "⏳ Waiting for internet connection...",
                        actions=[
                            ("Cancel", cancel_vbs)
                        ]
                    )

                sleep(10)
            
            if not connection:
                send_notification("No Internet Connection", "❌ No internet connection. Time sync failed.")
                log("ERROR", "No internet connection detected in auto sync.", console=False)
                return
                

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
            if is_auto:
                send_notification("Time Sync Success", "✅ Time synchronized successfully.")
                log("SYNC_SUCCESS", "Time synchronized successfully.", console=False)
            else:
                log("SYNC_SUCCESS", "Time synchronized successfully.", console=False)
                print("✅ Time synchronized successfully.")
        else:
            manual_success = manual_ntp_sync()

            if manual_success:
                if is_auto:
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
            else:
                if is_auto:
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

    except Exception as e:
        log("ERROR", f"Exception during time sync: {e}", console=True)

# ==================================================
# COMMANDS
# ==================================================

def commands_list():
    commands = {
        "now":       "Sync time immediately",
        "status":    "Show current status",
        "startup":   "Enable/disable startup sync",
        "resume":    "Enable/disable resume on wake (Sleep/hibernate)",
        "notify":    "Enable/disable notifications",
        "uninstall": "Remove TimeSync from your PC",
        "about":     "Show info about TimeSync",
        "version":   "Show version"
    }

    max_len = max(len(cmd) for cmd in commands.keys()) + 2

    print("\n=== TimeSync Commands ===\n")
    for command, description in commands.items():
        print(f"{command:<{max_len}} - {description}")

    print("\nUse 'timesync <command> -h' for more info on each command.")

    if not is_admin():
        print("\n⚠️ TimeSync is not running as Administrator. Some commands may not work As expected. Please run the terminal as Administrator for the best experience.")


def cmd_now():
    sync_windows_time()


def cmd_cancel():
    try:
        CANCEL_FILE.touch()
    except Exception as e:
        log("ERROR", f"Failed to create cancel file: {e}", console=False)


def cmd_status():
    print("\n=== TimeSync Status ===\n")

    print("🔐 Running as Administrator" if is_admin() else "⚠️ Not running as Administrator")
    print("🚀 Startup with Windows: Enabled" if startup_exists() else "🚫 Startup with Windows: Disabled")    
    print("💤 Sync on Wake: Enabled" if resume_exists() else "🚫 Sync on Wake: Disabled")
    print("🔔 Notifications: Enabled" if load_settings().get("notifications", True) else "🚫 Notifications: Disabled")
    print("\n💡 Just type 'timesync' without arguments to open the Graphical Interface")
    print("\nFor more details, check the log file at:", LOG_FILE)
    print("\n")


def cmd_startup_enable():
    create_startup_task(APP_DIR / "timesync-gui.exe")
    print("✅ Startup enabled")


def cmd_startup_disable():
    remove_startup_task()
    print("❌ Startup disabled")

def cmd_resume_enable():
    create_resume_task(APP_DIR / "timesync-gui.exe")
    print("✅ Resume enabled")

def cmd_resume_disable():
    remove_resume_task()
    print("❌ Resume disabled")

def cmd_toggle_notify(action=None):
    relaunch_as_admin()
    settings = load_settings()
    current = settings.get("notifications", True)
    
    if action == "enable":
        settings["notifications"] = True
    elif action == "disable":
        settings["notifications"] = False
    elif action == "status":
        pass  # لا حاجة لتغيير الإعدادات، فقط عرض الحالة الحالية
    else:
        # toggle
        settings["notifications"] = not current

    save_settings(settings)
    status = "enabled" if settings["notifications"] else "disabled"
    print(f"🔔 Notifications {status}.")

def cmd_about():
    print(f"""
╔══════════════════════════════════════════════╗
║                  TimeSync Tool               ║
╠══════════════════════════════════════════════╣
║
║  Version  : {VERSION}V
║  Author   : {AUTHOR}
║  GitHub   : {GITHUB}
║
╠══════════════════════════════════════════════╣
║        Windows Time Synchronization Tool     ║
╚══════════════════════════════════════════════╝
""")

def cmd_version():
    print(f"TimeSync v{VERSION}")

# ==================================================
# MAIN FLOW
# ==================================================

def main():
    parser = argparse.ArgumentParser(
        prog="timesync",
        description="Windows Time Synchronization Tool"
    )

    sub = parser.add_subparsers(dest="command")

    now_parser = sub.add_parser("now")
    now_parser.add_argument("--auto", action="store_true", help="Delayed sync for startup")

    sub.add_parser("cancel")
    sub.add_parser("disable-warning")

    sub.add_parser("help")
    sub.add_parser("commands")

    sub.add_parser("status")

    startup = sub.add_parser("startup")
    startup_sub = startup.add_subparsers(dest="action")

    startup_sub.add_parser("status")
    startup_sub.add_parser("enable")
    startup_sub.add_parser("disable")

    resume = sub.add_parser("resume")
    resume_sub = resume.add_subparsers(dest="action")

    resume_sub.add_parser("status")
    resume_sub.add_parser("enable")
    resume_sub.add_parser("disable")

    # إضافة قسم الإشعارات
    notify = sub.add_parser("notify")
    notify_sub = notify.add_subparsers(dest="action")

    notify_sub.add_parser("status")
    notify_sub.add_parser("enable")
    notify_sub.add_parser("disable")

    sub.add_parser("about")
    sub.add_parser("version")

    args = parser.parse_args()

    if "--auto" in sys.argv:
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)

    if len(sys.argv) == 1:
        from ui import run_gui
        print("🚀 Starting TimeSync in GUI mode...")
        relaunch_as_admin()
        run_gui()
        return

    if args.command:
        # تنفيذ الأوامر مباشرة
        if args.command in ["help", "commands"]:
            commands_list()
        elif args.command == "now":
            cmd_now()
        elif args.command == "cancel":
            cmd_cancel()
        elif args.command == "disable-warning":
            settings = load_settings()
            settings["show_warning_on_manual_sync"] = False
            save_settings(settings)
        elif args.command == "status":
            cmd_status()
        elif args.command == "startup":
            if args.action == "status":
                print("✅ startup enabled" if startup_exists() else "❌ startup disabled")
            elif args.action == "enable":
                cmd_startup_enable()
            elif args.action == "disable":
                cmd_startup_disable()
        elif args.command == "resume":
            if args.action == "status":
                print("✅ resume (Sleep/Hibernate) enabled" if resume_exists() else "❌ resume disabled")
            if args.action == "enable":
                cmd_resume_enable()
            elif args.action == "disable":
                cmd_resume_disable()
        elif args.command == "notify":
            if args.action == "status":
                cmd_toggle_notify("status")
            elif args.action == "enable":
                cmd_toggle_notify(args.action)
            elif args.action == "disable":
                cmd_toggle_notify(args.action)
        elif args.command == "about":
            cmd_about()
        elif args.command == "version":
            cmd_version()
    else:
        parser.print_help()
        print("\n\nUse 'timesync help' for more information.\n\n")


if __name__ == "__main__":
    # Set the process AppUserModelID for proper notification grouping in Windows 10/11. This is especially important if the app is not installed in Program Files and doesn't have a proper installer that sets the AppUserModelID.
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
    except Exception as e:
        log("WARNING", f"Failed to set process AppUserModelID: {e}", console=False)
        
    main()
