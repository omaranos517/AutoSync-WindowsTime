import subprocess
import ctypes
import os
import sys
import shutil
import argparse
import winreg
from pathlib import Path
import time

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
# CORE PATH LOGIC
# ==================================================

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
# INSTALLATION ACTIONS
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


def get_app_path():
    if getattr(sys, "frozen", False):
        return Path(sys.executable)
    return Path(__file__).resolve()


# ==================================================
# STARTUP SHORTCUT
# ==================================================

def startup_folder():
    return Path(os.getenv("APPDATA")) / \
        "Microsoft/Windows/Start Menu/Programs/Startup"


def create_startup_shortcut(script_path: Path = None):
    """
    ينشئ اختصار في مجلد Startup.
    إذا لم يُمرر script_path، يستخدم النسخة المثبتة في Program Files.
    """
    if script_path is None:
        script_path = get_installed_exe_path()

    startup = Path(os.getenv("APPDATA")) / "Microsoft/Windows/Start Menu/Programs/Startup"
    shortcut_path = startup / f"{script_path.stem}.lnk"

    vbs = f"""
Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = "{shortcut_path}"
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = "{script_path}"
oLink.WorkingDirectory = "{script_path.parent}"
oLink.Save
"""

    vbs_file = Path(script_path.parent) / "temp_shortcut.vbs"
    vbs_file.write_text(vbs)
    os.system(f'cscript //nologo "{vbs_file}"')
    vbs_file.unlink()
    print("✅ Startup shortcut created")


# ==================================================
# TIME SYNC
# ==================================================

def sync_windows_time():
    try:
        print("🔄 Syncing Windows time...\n")

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
            print("✅ Time synchronized successfully.")
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
    remove_from_path()
    remove_startup_shortcut()
    # إزالة الملف من Program Files
    target_path = get_installed_exe_path()
    if target_path.exists():
        try:
            target_path.unlink()
            print(f"🗑️ Removed installed file: {target_path}")
        except Exception as e:
            print(f"❌ Failed to remove installed file: {e}")
    print("🗑️ Uninstalled successfully")


def cmd_now():
    relaunch_as_admin()
    sync_windows_time()


def cmd_status():
    print("Admin:", is_admin())
    print("In PATH:", is_in_path())
    print("Startup:", startup_exists())


def cmd_startup_enable():
    relaunch_as_admin()
    create_startup_shortcut(get_installed_exe_path())
    print("✅ Startup enabled")


def cmd_startup_disable():
    relaunch_as_admin()
    remove_startup_shortcut()
    print("❌ Startup disabled")


# ==================================================
# REMOVE FROM SYSTEM PATH
# ==================================================

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



# ==================================================
# REMOVE STARTUP SHORTCUT
# ==================================================

def remove_startup_shortcut():
    exe_path = get_app_path()
    shortcut = startup_folder() / f"{exe_path.stem}.lnk"

    if shortcut.exists():
        shortcut.unlink()
        print("✅ Startup shortcut removed")
    else:
        print("❌ Startup shortcut not found")


# ==================================================
# CHECK IF IN PATH
# ==================================================

def is_in_path():
    exe_dir = str(get_app_path().parent)
    system_path = os.environ.get("PATH", "")
    return exe_dir.lower() in system_path.lower()

# ==================================================
# CHECK STARTUP STATUS
# ==================================================

def startup_exists():
    exe_path = get_app_path()
    shortcut = startup_folder() / f"{exe_path.stem}.lnk"
    return shortcut.exists()

# ==================================================
# FIRST RUN INSTALLER
# ==================================================

def first_run_installer():

    if len(sys.argv) > 1:
        return  # command mode

    if is_in_path():
        # البرنامج مثبت → نفذ المزامنة تلقائيًا
        cmd_now()
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
            create_startup_shortcut(get_installed_exe_path())
    
    elif choice == "2":
        cmd_now()
        print("Time synchronized without installation.")
        time.sleep(2)
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
    sub.add_parser("now")
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
