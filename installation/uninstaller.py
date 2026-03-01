import winreg
import sys
import ctypes
import shutil
import subprocess
from path_utils import get_current_exe_path
from TimeSync import remove_startup_task, remove_resume_task
from admin import relaunch_as_admin
from config import INSTALL_DIR

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