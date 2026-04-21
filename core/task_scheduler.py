import subprocess
from pathlib import Path

from utils.admin import relaunch_as_admin
from utils import log
from config import APP_DIR, STARTUP_TASK_NAME, RESUME_TASK_NAME


def create_startup_task(executable_path: Path = None):
    relaunch_as_admin()

    if executable_path is None:
        executable_path = APP_DIR / "timesync-gui.exe"  # Use the GUI version for startup to provide a better user experience on boot. The GUI will then launch the core sync process in the background and exit immediately, so it won't cause any noticeable delay during startup. This also allows us to show notifications if needed during startup sync.

    # Create a scheduled task that runs at user logon with highest privileges.
    task_name = STARTUP_TASK_NAME

    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = 0

    try:
        subprocess.run([
            "schtasks",
            "/create",
            "/tn", task_name,
            "/tr", f'"{executable_path}" now --auto',
            "/sc", "onlogon",
            "/rl", "highest",
            "/f",
            "/delay", "0000:00"
        ], check=True, capture_output=True, text=True, startupinfo=startupinfo)

        log("INFO", "Startup task created in Task Scheduler (Admin Privileges)", console=False)
        
    except subprocess.CalledProcessError as e:
        log("ERROR", f"Failed to create startup task: {e}", console=True)


def create_resume_task(executable_path: Path = None):
    relaunch_as_admin()

    if executable_path is None:
        executable_path = APP_DIR / "timesync-gui.exe"  # Use the GUI version for resume to provide a better user experience on wake. The GUI will then launch the core sync process in the background and exit immediately, so it won't cause any noticeable delay during wake. This also allows us to show notifications if needed during resume sync.

    task_name = RESUME_TASK_NAME

    try:
        subprocess.run([
            "schtasks",
            "/create",
            "/tn", task_name,
            "/tr", f'"{executable_path}" now --auto',
            "/sc", "onevent",
            "/ec", "System",
            "/mo", '*[System[Provider[@Name=\'Power-Troubleshooter\'] and EventID=1]]',
            "/rl", "highest",
            "/f"
        ], check=True, capture_output=True, text=True)

        log("INFO", "Resume task created in Task Scheduler (Admin Privileges)", console=False)
    except subprocess.CalledProcessError as e:
        log("ERROR", f"Failed to create resume task: {e}", console=True)


def remove_startup_task():
    relaunch_as_admin()

    task_name = STARTUP_TASK_NAME
    try:
        # Suppress output so a missing task does not show noisy errors.
        subprocess.run([
            "schtasks",
            "/delete",
            "/tn", task_name,
            "/f"
        ], check=True, capture_output=True, text=True)
        log("INFO", "Startup task removed successfully.", console=False)
    except subprocess.CalledProcessError:
        log("ERROR", "Startup task not found or already removed.", console=True)


def remove_resume_task():
    relaunch_as_admin()
    task_name = RESUME_TASK_NAME
    try:
        subprocess.run([
            "schtasks",
            "/delete",
            "/tn", task_name,
            "/f"
        ], check=True, capture_output=True, text=True)
        log("INFO", "Resume task removed successfully.", console=False)
    except subprocess.CalledProcessError:
        log("ERROR", "Resume task not found or already removed.", console=True)


def task_exists(task_name):
    try:
        result = subprocess.run([
            "schtasks",
            "/query",
            "/tn", task_name
        ], capture_output=True, text=True)
        return task_name in result.stdout
    except Exception:
        return False
