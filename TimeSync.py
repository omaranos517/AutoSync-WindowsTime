import subprocess
import ctypes
import os
import sys
import shutil
import argparse
import winreg
from socket import create_connection
from pathlib import Path
from winotify import Notification, audio
from time import sleep, strftime
import json

APP_NAME = "TimeSync"
RESUME_TASK_NAME = "TimeSync_resume"
STARTUP_TASK_NAME = "TimeSync_startup"

INSTALL_DIR = Path(os.environ.get("ProgramFiles", "C:\\Program Files")) / APP_NAME
DATA_DIR = Path(os.environ.get("ProgramData", "C:\\ProgramData")) / APP_NAME
DATA_DIR.mkdir(parents=True, exist_ok=True)

SETTINGS_FILE = DATA_DIR / "settings.json"
CANCEL_FILE = DATA_DIR / "cancel.flag"
LOG_FILE = DATA_DIR / f"{APP_NAME}.log"

VERSION = "1.2.0"
AUTHOR = "Omar Anoss"
GITHUB = "https://github.com/omaranos517/AutoSync-WindowsTime"


# ==================================================
# SETTINGS
# ==================================================

def load_settings():
    default_settings = {"notifications": True, "show_warning_on_manual_sync": True}
    if not SETTINGS_FILE.exists():
        return default_settings
    try:
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    except:
        return default_settings

def save_settings(settings):
    try:
        INSTALL_DIR.mkdir(parents=True, exist_ok=True)
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f)
    except Exception as e:
        log("ERROR", f"Failed to save settings: {e}", console=True)

# ==================================================
# LOGGING
# ==================================================

def log(level, message, console=False):
    try:
        log_entry = {
            "type": level,
            "message": message,
            "datetime": strftime("%Y-%m-%d %H:%M:%S")
        }
        INSTALL_DIR.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
            f.flush()
    except Exception as e:
        print(f"❌ Failed to write log: {e}")
    
    if console:
        print(level + ": " + message)

# ==================================================
# ADMIN
# ==================================================

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def relaunch_as_admin():
    if is_admin():
        return

    print("💡 Tip: Run Terminal in Administrator mode for the best experience! 💻")
    
    # تحضير المسار والوسائط بشكل صحيح
    executable = sys.executable
    if getattr(sys, "frozen", False):
        args = sys.argv[1:]
    else:
        args = sys.argv
    
    params = " ".join([f'"{arg}"' for arg in args])
    
    # تنفيذ كمسؤول
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", executable, params, None, 1
    )
    sys.exit(0)
    
    
# ==================================================
# PATH INSTALL
# ==================================================

def get_current_exe_path():
    """مسار الملف الحالي الذي يعمل الآن"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable)
    return Path(__file__).resolve()

def get_installed_exe_path():
    """المسار الذي يجب أن يكون فيه الملف بعد التثبيت"""
    return INSTALL_DIR / get_current_exe_path().name

# ==================================================
# INSTALLATION AND UNINSTALLATION LOGIC
# ==================================================

def install_logic():
    """نقل الملف، إضافته للمسار، وإنشاء ملف تشغيل سريع"""
    relaunch_as_admin()

    current_path = get_current_exe_path()
    target_path = get_installed_exe_path()

    print(f"📂 Installing to: {INSTALL_DIR}...")

    # 1. إنشاء المجلد ونقل الملف
    try:
        INSTALL_DIR.mkdir(parents=True, exist_ok=True)
        # إذا كان الملف يعمل من نفس مكان التثبيت، لا تحاول نسخه
        if current_path.parent != INSTALL_DIR:
            shutil.copy2(current_path, target_path)
    except Exception as e:
        print(f"❌ Failed to copy files: {e}")
        return

    # 2. إنشاء ملف CLI wrapper (batch file) في مجلد التثبيت
    # لكي يعمل أمر 'timesync' مباشرة
    bat_content = f'@echo off\n"{target_path}" %*'
    (INSTALL_DIR / "timesync.bat").write_text(bat_content)

    # 3. إضافة مجلد التثبيت للـ PATH
    add_to_system_path(str(INSTALL_DIR))

    commands_to_wrap = {
        "ts-cancel.bat": "cancel",
        "ts-now.bat": "now",
        "ts-disable-warning.bat": "disable-warning"
    }
    
    for bat_name, cmd_arg in commands_to_wrap.items():
        bat_path = INSTALL_DIR / bat_name
        # نستخدم start لضمان تشغيلها بشكل منفصل
        bat_content = f'@echo off\n"{target_path}" {cmd_arg}'
        bat_path.write_text(bat_content)

    register_uninstall_info()

    print(f"✅ Successfully installed at {target_path}")
    print(f"🚀 You can now use '{APP_NAME.lower()}' in any CMD.")


def uninstall_logic():
    """
    إلغاء تثبيت التطبيق عن طريق حزف جميع الملفات التي انشأها وقت التثبيت
    """
    relaunch_as_admin()
    
    if input("Are you sure you want to uninstall TimeSync? (y/n): ").lower() != "y":
        print("Uninstallation cancelled.")
        return
    
    print("🗑️ Starting uninstallation...")
    
    # 1. إزالة المهمة المجدولة (Startup)
    remove_startup_task()
    remove_resume_task()
    
    # 2. إزالة المسار من بيئة النظام (PATH)
    remove_from_path()
    
    # 3. إعداد عملية مسح المجلد بالكامل
    target_exe = get_installed_exe_path()
    current_exe = get_current_exe_path()

    # إذا كان المستخدم يشغل البرنامج من مكان التثبيت، لا يمكننا مسحه مباشرة
    # سنقوم بإنشاء أمر CMD خارجي ينتظر إغلاق البرنامج ثم يمسح المجلد
    if current_exe.parent == INSTALL_DIR:
        print("⏳ Cleaning up after exit...")
        # أمر CMD يقوم بالانتظار لثانية ثم مسح المجلد بالكامل
        cmd_cleanup = f'timeout /t 3 /nobreak && rd /s /q "{INSTALL_DIR}"'
        subprocess.Popen(cmd_cleanup, shell=True)
        print("✅ Uninstallation scheduled. This window will close.")
        sys.exit(0)
    else:
        # إذا كان المستخدم يشغله من مكان آخر (مثل Downloads)، يمكننا المسح فوراً
        if INSTALL_DIR.exists():
            try:
                shutil.rmtree(INSTALL_DIR)
                print(f"🗑️ Removed directory: {INSTALL_DIR}")
            except Exception as e:
                print(f"❌ Failed to remove directory: {e}")
                
    print("✅ Uninstalled successfully.")


def add_to_system_path(path_to_add):
    reg_path = r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path, 0, winreg.KEY_READ | winreg.KEY_WRITE) as key:
        current_path, _ = winreg.QueryValueEx(key, "Path")
        if path_to_add.lower() in current_path.lower():
            return
        
        new_path = current_path.rstrip(';') + ";" + path_to_add
        winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)

    # إخبار الويندوز بتحديث البيئة فوراً
    ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001A, 0, "Environment", 0, 100, None)


def get_folder_size_kb(folder: Path):
    total = 0
    for root, dirs, files in os.walk(folder):
        for name in files:
            try:
                fp = Path(root) / name
                total += fp.stat().st_size
            except:
                pass
    return total // 1024


def register_uninstall_info():
    uninstall_key_path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\TimeSync"
    size_in_kb = get_folder_size_kb(INSTALL_DIR)

    with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, uninstall_key_path) as key:
        winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, APP_NAME)
        winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, VERSION)
        winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, AUTHOR)
        winreg.SetValueEx(key, "EstimatedSize", 0, winreg.REG_DWORD, size_in_kb)
        winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)

        winreg.SetValueEx(
            key,
            "UninstallString",
            0,
            winreg.REG_SZ,
            f'"{get_installed_exe_path()}" uninstall'
        )
        winreg.SetValueEx(
            key,
            "InstallLocation",
            0,
            winreg.REG_SZ,
            str(INSTALL_DIR)
        )
        winreg.SetValueEx(
            key,
            "DisplayIcon",
            0,
            winreg.REG_SZ,
            str(get_installed_exe_path())
        )


def remove_from_path():
    path_to_remove = str(INSTALL_DIR).rstrip("\\").lower()
    reg_path = r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"

    try:
        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            reg_path,
            0,
            winreg.KEY_READ | winreg.KEY_WRITE
        ) as key:

            current_path, reg_type = winreg.QueryValueEx(key, "Path")

            parts = [
                p.rstrip("\\").strip()
                for p in current_path.split(";")
                if p.rstrip("\\").strip().lower() != path_to_remove
            ]

            new_path = ";".join(parts)

            winreg.SetValueEx(key, "Path", 0, reg_type, new_path)

        ctypes.windll.user32.SendMessageTimeoutW(
            0xFFFF,
            0x001A,
            0,
            "Environment",
            0,
            100,
            None
        )

    except Exception as e:
        print("PATH cleanup failed:", e)

    try:
        winreg.DeleteKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"Software\Microsoft\Windows\CurrentVersion\Uninstall\TimeSync"
        )
    except FileNotFoundError:
        pass


def is_in_path():
    exe_dir = str(get_app_path().parent)
    system_path = os.environ.get("PATH", "")
    return exe_dir.lower() in system_path.lower()


def get_app_path():
    if getattr(sys, "frozen", False):
        return Path(sys.executable)
    return Path(__file__).resolve()


# ==================================================
# STARTUP TASK (TASK SCHEDULER)
# ==================================================

def create_startup_task(executable_path: Path = None):
    relaunch_as_admin()

    if executable_path is None:
        executable_path = get_installed_exe_path()

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
        executable_path = get_installed_exe_path()

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
# Notification
# ==================================================

def send_notification(title, message, actions=None):
    settings = load_settings()
    if not settings.get("notifications", True):
        return

    try:
        notifier = Notification(
            app_id="TimeSync",
            title=title,
            msg=message,
            duration="short"
        )

        if actions:
            for label, launch in actions:
                notifier.add_actions(label=label, launch=launch)

        notifier.set_audio(audio.Default, loop=False)
        notifier.show()

    except Exception as e:
        log("ERROR", f"Failed to send notification: {e}", console=True)

# ==================================================
# TIME SYNC CORE
# ==================================================

def has_internet_connection():
    """تحقق مما إذا كان هناك اتصال بالإنترنت"""
    try:
        # محاولة الاتصال بـ DNS جوجل للتأكد من وجود إنترنت
        conn = create_connection(("8.8.8.8", 53), timeout=3)
        conn.close()
        return True
    except OSError:
        log("WARNING", "No internet connection detected.", console=True)
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
                    cancel_bat = str(INSTALL_DIR / "ts-cancel.bat")
                    send_notification(
                        "No Internet Connection",
                        "⏳ Waiting for internet connection...",
                        actions=[
                            ("Cancel", cancel_bat)
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
                        disable_warning_bat = str(INSTALL_DIR / "ts-disable-warning.bat")
                        send_notification(
                                            "⚠️ Warning",
                                            "Windows has a problem with time sync, so TimeSync used a manual method to sync the time. Consider fixing Windows Time Service for better performance.",
                                            actions=[
                                                ("Don't show again", disable_warning_bat)
                                            ]
                                        )
                        log("WARNING", "Time synchronized manually (fallback mode). Windows Time Service may have issues.", console=False)
                else:
                    print("✅ Time synchronized manually (fallback mode).")
            else:
                if is_auto:
                    retry_bat = str(INSTALL_DIR / "ts-now.bat")
                    send_notification(
                        "Time Sync Failed",
                        "❌ Time sync failed.",
                        actions=[
                            ("Retry", retry_bat)
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

def cmd_install():
    install_logic()
    print("✅ Installed successfully")

def cmd_uninstall():
    uninstall_logic()
    print("✅ Uninstalled successfully")


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
    print("📌 Command available globally (you can use 'timesync' anywhere)" if is_in_path() else "❌ Command not available globally (not added to PATH)")
    print("🚀 Startup with Windows: Enabled" if startup_exists() else "🚫 Startup with Windows: Disabled")    
    print("💤 Resume on Wake: Enabled" if resume_exists() else "🚫 Resume on Wake: Disabled")
    print("🔔 Notifications: Enabled" if load_settings().get("notifications", True) else "🚫 Notifications: Disabled")
    print("\nFor more details, check the log file at:", LOG_FILE)
    print("\n")


def cmd_startup_enable():
    create_startup_task(get_installed_exe_path())
    create_resume_task(get_installed_exe_path())
    print("✅ Startup enabled")


def cmd_startup_disable():
    remove_startup_task()
    print("❌ Startup disabled")

def cmd_resume_enable():
    create_resume_task(get_installed_exe_path())
    print("✅ Resume enabled")

def cmd_resume_disable():
    remove_resume_task()
    print("❌ Resume disabled")

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
# FIRST RUN INSTALLER
# ==================================================

def first_run_installer():
    if len(sys.argv) > 1:
        return  # command mode

    if is_in_path():
        commands_list()
        return  # already installed

    relaunch_as_admin()
    import msvcrt
    def clear():
        os.system("cls")

    def menu(title, options):
        selected = 0

        # نحفظ أول حرف لكل خيار (lowercase)
        first_letters = [opt[0].lower() for opt in options]

        while True:
            clear()
            print(title)
            print()

            for i, option in enumerate(options):
                prefix = ">" if i == selected else " "
                print(f"{prefix} {i+1}. {option}")

            key = msvcrt.getch()

            # الأسهم
            if key == b'\xe0':
                key = msvcrt.getch()

                if key == b'H':      # up
                    selected = (selected - 1) % len(options)

                elif key == b'P':    # down
                    selected = (selected + 1) % len(options)

            # Enter
            elif key == b'\r':
                return selected

            # أرقام
            elif key.isdigit():
                index = int(key) - 1
                if 0 <= index < len(options):
                    return index

            # أول حرف
            else:
                char = key.decode(errors="ignore").lower()
                if char in first_letters:
                    selected = first_letters.index(char)
                    return selected

    choice = menu("=== Windows Time Sync Tool ===\n\nThis program is not installed.\nYou can install it to use the 'timesync' command from any CMD, and you can set it to run automatically at Windows startup.\nPlease choose an option:", 
                  [
                    "Install",
                    "Just Sync time now without installing",
                    "Exit"
                  ]
    )

    if choice == 0:
        cmd_install()
        print("Installation completed.")

        startup_choice = menu("Run automatically with Windows startup?", ["Yes", "No"])

        if startup_choice == 0:
            create_startup_task(get_installed_exe_path())
            create_resume_task(get_installed_exe_path())
            print("✅ Startup shortcut created.")
            sleep(2)
        else:
            print("❌ Startup shortcut not created.")

    elif choice == 1:
        cmd_now()
        print("Time synchronized without installation.")
        sleep(2)
    else:
        sys.exit(0)


# ==================================================
# MAIN FLOW
# ==================================================

def main():
    parser = argparse.ArgumentParser(
        prog="timesync",
        description="Windows Time Synchronization Tool"
    )

    sub = parser.add_subparsers(dest="command")

    sub.add_parser("uninstall")

    now_parser = sub.add_parser("now")
    now_parser.add_argument("--auto", action="store_true", help="Delayed sync for startup")

    sub.add_parser("cancel")
    sub.add_parser("disable-warning")

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

    if args.command:
        # تنفيذ الأوامر مباشرة
        if args.command == "uninstall":
            cmd_uninstall()
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
            settings = load_settings()
            if args.action == "status":
                status = "Enabled" if settings.get("notifications", True) else "Disabled"
                print(f"🔔 Notifications are: {status}")
            elif args.action == "enable":
                settings["notifications"] = True
                save_settings(settings)
                print("✅ Notifications enabled.")
            elif args.action == "disable":
                settings["notifications"] = False
                save_settings(settings)
                print("❌ Notifications disabled.")
        elif args.command == "about":
            cmd_about()
        elif args.command == "version":
            cmd_version()
    else:
        # إذا لم يتم تمرير أي args → run installer
        first_run_installer()


if __name__ == "__main__":
    main()