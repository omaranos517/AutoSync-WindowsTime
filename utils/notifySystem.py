from winotify import Notification, audio
from settings import load_settings
from config import APP_ID
from . import log

def send_notification(title, message, actions=None, warning=None):
    settings = load_settings()
    if not warning:
        if not settings.get("notifications", True):
            return

    try:
        notifier = Notification(
            app_id=APP_ID,
            title=title,
            msg=message,
            duration="short"
        )

        if actions:
            for label, launch in actions:
                notifier.add_actions(label=label, launch=launch)

        notifier.set_audio(audio.Default, loop=False)
        notifier.show()

    except Exception as e:
        log("ERROR", f"Failed to send notification: {e}", console=True)
