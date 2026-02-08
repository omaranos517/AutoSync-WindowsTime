import subprocess
import ctypes
import os
import sys
import shutil
import argparse
import winreg
from pathlib import Path
from time import sleep

APP_NAME = "TimeSync"
INSTALL_DIR = Path(os.environ.get("ProgramFiles", "C:\\Program Files")) / APP_NAME

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

    print(f"✅ Successfully installed at {target_path}")
    print(f"🚀 You can now use '{APP_NAME.lower()}' in any CMD.")


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

def create_startup_task(script_path: Path = None):
    if script_path is None:
        script_path = get_installed_exe_path()

    # إنشاء مهمة مجدولة تعمل مع دخول المستخدم بأعلى صلاحيات
    task_name = "TimeSyncStartup"

    cmd = (
        f'schtasks /create /tn "{task_name}" /tr "\'{script_path}\' now --auto" '
        f'/sc onlogon /rl highest /f'
    )
    
    try:
        subprocess.run(cmd, shell=True, check=True, capture_output=True)
        print("✅ Startup task created in Task Scheduler (Admin Privileges)")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create task: {e}")


def remove_startup_task():
    task_name = "TimeSyncStartup"
    cmd = f'schtasks /delete /tn "{task_name}" /f'
    try:
        # كتم المخرجات لكي لا يظهر خطأ إذا كانت المهمة غير موجودة أصلاً
        subprocess.run(cmd, shell=True, check=True, capture_output=True)
        print("✅ Startup task removed successfully.")
    except subprocess.CalledProcessError:
        print("❌ Startup task not found or already removed.")


def startup_exists():
    task_name = "TimeSyncStartup"
    cmd = f'schtasks /query /tn "{task_name}"'
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return task_name in result.stdout
    except:
        return False

# ==================================================
# Notification
# ==================================================

def send_notification(title, message):
    """إرسال إشعار ويندوز باستخدام PowerShell"""
    powershell_cmd = f"""
    [Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms');
    [Reflection.Assembly]::LoadWithPartialName('System.Drawing');
    $notify = New-Object System.Windows.Forms.NotifyIcon;
    $notify.Icon = [System.Drawing.SystemIcons]::Information;
    $notify.Visible = $true;
    $notify.ShowBalloonTip(3000, '{title}', '{message}', [System.Windows.Forms.ToolTipIcon]::Info);
    """
    try:
        subprocess.run(["powershell", "-Command", powershell_cmd], capture_output=True)
    except:
        pass


# ==================================================
# TIME SYNC CORE
# ==================================================

def sync_windows_time():
    try:
        is_auto = "--auto" in sys.argv

        if not is_auto:
            print("🔄 Syncing Windows time...\n")
        else:
            sleep(8)  # ** delay for startup sync

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
                send_notification(APP_NAME, "✅ Time synchronized successfully.")
            else:
                print("✅ Time synchronized successfully.")
        else:
            if is_auto:
                send_notification(APP_NAME, "The time synchronization process failed.")
            else:
                print(result.stderr)

    except Exception as e:
        print("❌ Error:", e)

# ==================================================
# COMMANDS
# ==================================================

def cmd_install():
    relaunch_as_admin()
    install_logic()
    print("✅ Installed successfully")

def cmd_uninstall():
    relaunch_as_admin()
    
    print("🗑️ Starting uninstallation...")
    
    # 1. إزالة المهمة المجدولة (Startup)
    remove_startup_task()
    
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
        cmd_cleanup = f'timeout /t 2 /nobreak && rd /s /q "{INSTALL_DIR}"'
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


def cmd_now():
    relaunch_as_admin()
    sync_windows_time()


def cmd_status():
    print("Admin:", is_admin())
    print("In PATH:", is_in_path())
    print("Startup:", startup_exists())


def cmd_startup_enable():
    relaunch_as_admin()
    create_startup_task(get_installed_exe_path())
    print("✅ Startup enabled")


def cmd_startup_disable():
    relaunch_as_admin()
    remove_startup_task()
    print("❌ Startup disabled")

# ==================================================
# FIRST RUN INSTALLER
# ==================================================

def first_run_installer():

    if len(sys.argv) > 1:
        return  # command mode

    if is_in_path():
        cmd_now() # synchronize time on startup
        return  # already installed

    print("""
\n=== Windows Time Sync Tool ===\n

This program is not installed.
You can install it to use the 'timesync' command from any CMD, and you can set it to run automatically at Windows startup.
Please choose an option:

1) Install
2) Just Sync time now wothout installing
3) Exit
""")

    choice = input("Choose: ").strip()

    if choice == "1":
        cmd_install()
        print("Installation completed.")

        startup_choice = input(
            "Run automatically with Windows startup? (y/n): "
        ).lower().strip()

        if startup_choice == "y":
            create_startup_task(get_installed_exe_path())
            print("✅ Startup shortcut created.")
            sleep(2)
    
    elif choice == "2":
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

    sub.add_parser("status")

    startup = sub.add_parser("startup")
    startup_sub = startup.add_subparsers(dest="action")

    startup_sub.add_parser("enable")
    startup_sub.add_parser("disable")

    args = parser.parse_args()

    if args.command:
        # تنفيذ الأوامر مباشرة
        if args.command == "uninstall":
            cmd_uninstall()
        elif args.command == "now":
            cmd_now()
        elif args.command == "status":
            cmd_status()
        elif args.command == "startup":
            if args.action == "enable":
                cmd_startup_enable()
            elif args.action == "disable":
                cmd_startup_disable()
            else:
                parser.print_help()
    else:
        # إذا لم يتم تمرير أي args → run installer
        first_run_installer()


if __name__ == "__main__":
    main()
