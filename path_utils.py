import sys
import os
from pathlib import Path
from config import APP_DIR

def get_current_exe_path():
    """مسار الملف الحالي الذي يعمل الآن"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable)
    return Path(__file__).resolve()


def get_gui_app_path():
    """المسار الذي يجب أن يكون فيه ملف الواجهة الرسومية بعد التثبيت"""
    return APP_DIR / "timesync-gui.exe"


def is_in_path():
    exe_dir = str(get_current_exe_path().parent)
    system_path = os.environ.get("PATH", "")
    return exe_dir.lower() in system_path.lower()
