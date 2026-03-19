from winotify import Notification, audio

from . import log
from config.settings import load_settings
from config import APP_ID

def send_notification(title, message, actions=None, warning=None, tag=None, group=None):
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
        notifier.tag = tag or title
        notifier.group = group or APP_ID

        if actions:
            for label, launch in actions:
                notifier.add_actions(label=label, launch=launch)

        notifier.set_audio(audio.Default, loop=False)
        notifier.show()

    except Exception as e:
        log("ERROR", f"Failed to send notification: {e}", console=True)
