from pathlib import Path
import os
from sys import executable

APP_NAME = "TimeSync"
APP_ID = "OmarAnoss.TimeSync"
PROTOCOL = "timesync"
STARTUP_TASK_NAME = "TimeSync_startup"
RESUME_TASK_NAME = "TimeSync_resume"
PERIODIC_TASK_NAME = "TimeSync_periodic"

APP_DIR = Path(executable).parent
DATA_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / APP_NAME
DATA_DIR.mkdir(parents=True, exist_ok=True)

SETTINGS_FILE = DATA_DIR / "settings.json"
CANCEL_FILE = DATA_DIR / "cancel.flag"
LOG_FILE = DATA_DIR / f"{APP_NAME}.log"

VERSION = "1.4.0"
AUTHOR = "Omar Anoss"
GITHUB = "https://github.com/omaranos517/AutoSync-WindowsTime"
