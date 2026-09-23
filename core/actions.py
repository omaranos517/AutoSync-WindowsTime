import os
import ctypes

from utils import log, is_admin, run_cmd
from config import STARTUP_TASK_NAME, PERIODIC_TASK_NAME, RESUME_TASK_NAME, CANCEL_FILE, LOG_FILE
from config.settings import load_settings, save_settings
from core.timezones import (
    get_current_windows_timezone,
    find_timezone_matches,
    get_timezone_id,
    get_timezone_label,
    get_timezone_options,
)


def sync_time_action(silent : bool = False, notify : bool = False) -> object:
    """Main command to sync time immediately. Returns a status message indicating success, failure, or any warnings."""
    from core.sync_engine import check_internet_and_sync
    from utils import send_notification

    result = check_internet_and_sync(silent=silent, notify=notify)

    if result.success:
        log("SYNC_SUCCESS", "Time synchronized successfully.", console=False)
        if notify:
            send_notification(
                "Time Sync Success",
                "✅ Time synchronized successfully.",
                tag="sync-status",
                group="sync-status"
            )
        
        if result.warning:
            if notify:
                send_notification(
                    "Time Sync Warning",
                    f"⚠️ {result.warning}",
                    actions=result.warning_actions,
                    tag="sync-warning",
                    group="sync-warning"
                )
            log("SYNC_WARNING", result.warning, console=False)
            return f"Warning: {result.warning}"
    else:
        if notify:
            send_notification(
                "Time Sync Failed",
                f"❌ Time synchronization failed: {result.error}",
                tag="sync-status",
                group="sync-status"
            )
        log("SYNC_FAILED", f"Time synchronization failed: {result.error}", console=False)

    return result


def get_status(include_timezone_options=True) -> dict:
    """Shows the current status of TimeSync, including whether it's running as administrator, if startup and resume tasks are enabled, and if notifications are on. Also provides a reminder about the graphical interface and where to find logs."""
    from core.task_scheduler import task_exists
    isAdmin = is_admin()
    startUp = task_exists(STARTUP_TASK_NAME)
    periodic = task_exists(PERIODIC_TASK_NAME)
    resume = task_exists(RESUME_TASK_NAME)
    notify = load_settings().get('notifications', True)
    current_timezone = get_current_windows_timezone()
    status = {
        'isAdmin' : isAdmin,
        'startUp' : startUp,
        'periodic' : periodic,
        'resume' : resume,
        'notify' : notify,
        'timezone': get_timezone_label(current_timezone),
        }
    if include_timezone_options:
        status['timezone_options'] = get_timezone_options()
    return status


def open_logs():
    """Opens the log file in the default text editor. If the log file doesn't exist, shows a warning message."""
    try:
        if LOG_FILE.exists():
            print("Logs file opening...")
            os.startfile(LOG_FILE)
        else:
            print("No logs found.")
    except Exception as e:
        print(f"Failed to open logs: {e}")


def _toggle_feature(action, task_name, enable_fn, disable_fn) -> bool:
    from core.task_scheduler import task_exists
    if action == "enable":
        enable_fn()
    elif action == "disable":
        disable_fn()
    elif action != "status":
        (disable_fn if task_exists(task_name) else enable_fn)()
    return task_exists(task_name)


def toggle_startup(action=None):
    """Enables, disables, or shows the status of the startup sync feature. Uses the task scheduler to create or remove a task that runs TimeSync on Windows startup."""
    from core.task_scheduler import create_startup_task, remove_startup_task
    return _toggle_feature(
        action,
        STARTUP_TASK_NAME,
        lambda: create_startup_task(),
        remove_startup_task,
    )


def toggle_periodic(action=None):
    """Enables, disables, or shows the status of the periodic sync feature. Uses the task scheduler to create or remove a task that runs TimeSync every hour."""
    from core.task_scheduler import create_periodic_task, remove_periodic_task
    return _toggle_feature(
        action,
        PERIODIC_TASK_NAME,
        lambda: create_periodic_task(),
        remove_periodic_task,
    )


def toggle_resume(action=None):
    """Enables, disables, or shows the status of the resume on wake feature. Uses the task scheduler to create or remove a task that runs TimeSync when the computer wakes from sleep or hibernate."""
    from core.task_scheduler import create_resume_task, remove_resume_task
    return _toggle_feature(
        action,
        RESUME_TASK_NAME,
        lambda: create_resume_task(),
        remove_resume_task,
    )


def toggle_notify(action=None):
    """Enables, disables, or shows the status of notifications. Updates the settings file to reflect the new state and prints the current status."""
    settings = load_settings()
    current = settings.get("notifications", True)
    
    if action == "enable":
        settings["notifications"] = True
    elif action == "disable":
        settings["notifications"] = False
    elif action != "status":
        # toggle
        settings["notifications"] = not current

    save_settings(settings)
    return settings["notifications"]

# ==================================================
# notifications actions
# ==================================================

def create_cancel_file(session_id=None):
    """Signal cancellation, optionally for one specific waiting sync session."""
    try:
        CANCEL_FILE.write_text(session_id or "", encoding="utf-8")
    except Exception as e:
        log("ERROR", f"Failed to create cancel file: {e}", console=False)


def disable_warning_action():
    """Updates the settings to disable warnings on manual sync. This is intended to be used as an action for a notification button, allowing users to easily turn off warnings if they find them annoying."""
    settings = load_settings()
    settings["show_warning_on_manual_sync"] = False
    save_settings(settings)
    log("INFO", "Warning on manual sync has been disabled.", console=False)


def set_timezone(timezone_name):
    """Apply the selected Windows timezone without saving it in app settings."""

    timezone_id = get_timezone_id(timezone_name)
    try:
        run_cmd(["tzutil", "/s", timezone_id])
        log("INFO", f"Timezone changed to {timezone_id}", console=True)
        return get_timezone_label(timezone_id)
    except Exception as exc:
        log("ERROR", f"Failed to apply timezone with tzutil: {exc}", console=True)
        raise


def get_timezone_status():
    windows_timezone_id = get_current_windows_timezone()
    return {
        "windows_id": windows_timezone_id,
        "label": get_timezone_label(windows_timezone_id),
    }


def list_timezones():
    return get_timezone_options()


def search_timezones(query):
    return find_timezone_matches(query)


def restart_pc():
    """
    Restart the PC immediately.
    Switches used:
    /r : restart
    /t 0 : remaining time (zero seconds)
    /f : force-close open applications to prevent the process from hanging
    """
    try:
        print("🔌 Restarting PC now...")
        ctypes.windll.shell32.ShellExecuteW(None, "open", "shutdown.exe", "/r /t 0 /f", None, 0)
    except Exception as e:
        log("ERROR", f"Failed to restart PC: {e}", console=True)
