import sys
import os
from pathlib import Path
from config import APP_DIR

def get_current_exe_path():
    """مسار الملف الحالي الذي يعمل الآن"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable)
    return Path(__file__).resolve()


def get_installed_exe_path():
    """المسار الذي يجب أن يكون فيه الملف بعد التثبيت"""
    return APP_DIR / get_current_exe_path().name


def is_in_path():
    exe_dir = str(get_app_path().parent)
    system_path = os.environ.get("PATH", "")
    return exe_dir.lower() in system_path.lower()


def get_app_path():
    if getattr(sys, "frozen", False):
        return Path(sys.executable)
    return Path(__file__).resolve()