import subprocess

from utils.admin import relaunch_as_admin
from utils import log, run_cmd
from config import APP_DIR, STARTUP_TASK_NAME, RESUME_TASK_NAME, PERIODIC_TASK_NAME

def _create_task(task_name: str, trigger_type: str, trigger_args: list[str], notify : bool = False):
    relaunch_as_admin()

    executable_path = APP_DIR / "timesync-gui.exe"  # Use the GUI version for startup to provide a better user experience on boot. The GUI will then launch the core sync process in the background and exit immediately, so it won't cause any noticeable delay during startup.
    # command = f'"{executable_path}" now --silent --notify' if notify else f'"{executable_path}" now --silent'
    try:
        run_cmd([
            "schtasks",
            "/create",
            "/tn", task_name,
            "/tr", f'"{executable_path}" now --silent' + (" --notify" if notify else ""),
            "/sc", trigger_type,
            *trigger_args,
            "/rl", "highest",
            "/f"
        ])
        log("INFO", f"Task '{task_name}' created in Task Scheduler (Admin Privileges)", console=False)

    except subprocess.CalledProcessError as e:
        log("ERROR", f"Failed to create task '{task_name}': {e}", console=True)


def _remove_task(task_name: str):
    relaunch_as_admin()

    try:
        run_cmd([
            "schtasks",
            "/delete",
            "/tn", task_name,
            "/f"
        ])
        log("INFO", f"Task '{task_name}' removed from Task Scheduler (Admin Privileges)", console=False)

    except subprocess.CalledProcessError as e:
        log("ERROR", f"Failed to remove task '{task_name}': {e}", console=True)


def create_startup_task():
    _create_task(STARTUP_TASK_NAME, "onlogon", ["/delay", "0000:00"])


def create_periodic_task():
    _create_task(PERIODIC_TASK_NAME, "hourly", ["/mo", "1"])


def create_resume_task():
    _create_task(RESUME_TASK_NAME, "onevent", ["/ec", "System", "/mo", '*[System[Provider[@Name=\'Power-Troubleshooter\'] and EventID=1]]'], True)


def remove_startup_task():
    _remove_task(STARTUP_TASK_NAME)


def remove_periodic_task():
    _remove_task(PERIODIC_TASK_NAME)


def remove_resume_task():
    _remove_task(RESUME_TASK_NAME)


def task_exists(task_name):
    try:
        result = run_cmd([
            "schtasks",
            "/query",
            "/tn", task_name
        ])
        return task_name in result.stdout
    except Exception:
        return False
