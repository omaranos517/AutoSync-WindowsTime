import os
import ctypes

from utils import log, is_admin
from utils.console import success_text, error_text, warning_text, info_text
from config import STARTUP_TASK_NAME, PERIODIC_TASK_NAME, RESUME_TASK_NAME, CANCEL_FILE, LOG_FILE
from config.settings import (
    load_settings,
    save_settings,
    get_current_windows_timezone,
    get_timezone_id,
    get_timezone_label,
    get_timezone_options,
)


def sync_time_action(silent : bool = False, notify : bool = False) -> str:
    """Main command to sync time immediately. Returns a status message indicating success, failure, or any warnings."""
    print(info_text("🔄 Syncing time now..."))
    from core.sync_engine import check_internet_and_sync
    from utils import send_notification

    result = check_internet_and_sync(silent=silent, notify=notify)

    if result.success:
        print(success_text("✅ Time synchronized successfully!"))
        log("SYNC_SUCCESS", "Time synchronized successfully.", console=False)
        
        if notify:
            send_notification(
                "Time Sync Success",
                "✅ Time synchronized successfully.",
                tag="sync-status",
                group="sync-status"
            )
        
        if result.warning:
            print(warning_text(f"⚠️ Warning: {result.warning}"))
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
        return "Success: Time synchronized successfully."
    else:
        print(error_text(f"❌ Time synchronization failed: {result.error}"))
        if notify:
            send_notification(
                "Time Sync Failed",
                f"❌ Time synchronization failed: {result.error}",
                tag="sync-status",
                group="sync-status"
            )
        log("SYNC_FAILED", f"Time synchronization failed: {result.error}", console=False)
        return f"Failed: {result.error}"


def get_status() -> dict:
    """Shows the current status of TimeSync, including whether it's running as administrator, if startup and resume tasks are enabled, and if notifications are on. Also provides a reminder about the graphical interface and where to find logs."""
    from core.task_scheduler import task_exists
    isAdmin = is_admin()
    startUp = task_exists(STARTUP_TASK_NAME)
    periodic = task_exists(PERIODIC_TASK_NAME)
    resume = task_exists(RESUME_TASK_NAME)
    notify = load_settings().get('notifications', True)
    current_timezone = get_current_windows_timezone()
    return {
        'isAdmin' : isAdmin,
        'startUp' : startUp,
        'periodic' : periodic,
        'resume' : resume,
        'notify' : notify,
        'timezone': get_timezone_label(current_timezone),
        'timezone_options': get_timezone_options(),
        }


def open_logs():
    """Opens the log file in the default text editor. If the log file doesn't exist, shows a warning message."""
    print(info_text("Logs file opening..."))
    try:
        if LOG_FILE.exists():
            os.startfile(LOG_FILE)
        else:
            print(warning_text("No logs found."))
    except Exception as e:
        print(error_text(f"Failed to open logs: {e}"))


def _toggle_feature(action, task_name, enable_fn, disable_fn, name):
    """Generic function to toggle a feature on/off based on the provided action. It checks the current state using exists_fn, enables or disables the feature accordingly, and then prints the new status."""
    from core.task_scheduler import task_exists
    if action == "enable":
        enable_fn()
    elif action == "disable":
        disable_fn()
    elif action == "status":
        pass
    else:  # toggle
        if task_exists(task_name):
            disable_fn()
        else:
            enable_fn()

    is_enabled = task_exists(task_name)
    status_text = success_text("enabled") if is_enabled else error_text("disabled")
    icon = "✅" if is_enabled else "❌"
    print(f"{icon} {name} {status_text}")


def toggle_startup(action=None):
    """Enables, disables, or shows the status of the startup sync feature. Uses the task scheduler to create or remove a task that runs TimeSync on Windows startup."""
    from core.task_scheduler import create_startup_task, remove_startup_task
    _toggle_feature(
        action,
        STARTUP_TASK_NAME,
        lambda: create_startup_task(),
        remove_startup_task,
        "Startup"
    )


def toggle_periodic(action=None):
    """Enables, disables, or shows the status of the periodic sync feature. Uses the task scheduler to create or remove a task that runs TimeSync every hour."""
    from core.task_scheduler import create_periodic_task, remove_periodic_task
    _toggle_feature(
        action,
        PERIODIC_TASK_NAME,
        lambda: create_periodic_task(),
        remove_periodic_task,
        "Periodic Sync"
    )


def toggle_resume(action=None):
    """Enables, disables, or shows the status of the resume on wake feature. Uses the task scheduler to create or remove a task that runs TimeSync when the computer wakes from sleep or hibernate."""
    from core.task_scheduler import create_resume_task, remove_resume_task
    _toggle_feature(
        action,
        RESUME_TASK_NAME,
        lambda: create_resume_task(),
        remove_resume_task,
        "Resume"
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
    is_enabled = settings["notifications"]
    status = success_text("enabled") if is_enabled else error_text("disabled")
    print(f"🔔 Notifications {status}.")

# ==================================================
# notifications actions
# ==================================================

def create_cancel_file():
    """Creates a cancel file that signals the background sync process to stop. If the file cannot be created, logs an error message."""
    try:
        CANCEL_FILE.touch()
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
    import subprocess

    timezone_id = get_timezone_id(timezone_name)
    try:
        subprocess.run(["tzutil", "/s", timezone_id], check=True, capture_output=True, text=True)
        log("INFO", f"Timezone changed to {timezone_id}", console=True)
        return get_timezone_label(timezone_id)
    except Exception as exc:
        log("ERROR", f"Failed to apply timezone with tzutil: {exc}", console=True)
        raise


def restart_pc():
    """
    Restart the PC immediately.
    Switches used:
    /r : restart
    /t 0 : remaining time (zero seconds)
    /f : force-close open applications to prevent the process from hanging
    """
    print("🔌 Restarting PC now...")
    try:
        ctypes.windll.shell32.ShellExecuteW(None, "open", "shutdown.exe", "/r /t 0 /f", None, 0)
    except Exception as e:
        log("ERROR", f"Failed to restart PC: {e}", console=True)
