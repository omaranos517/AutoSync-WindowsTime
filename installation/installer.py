import winreg
import shutil
from pathlib import Path
import os
import ctypes
from path_utils import get_current_exe_path, get_installed_exe_path
from admin import relaunch_as_admin
from config import INSTALL_DIR, APP_NAME, AUTHOR, VERSION

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
