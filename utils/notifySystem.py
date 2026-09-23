from .app_logger import log
from config.settings import load_settings
from config import APP_ID

from datetime import datetime, timedelta
from winrt.windows.ui.notifications import ToastNotificationManager, ToastNotification
from winrt.windows.data.xml.dom import XmlDocument

def send_notification(title, message, actions=None, warning=None, tag=None, group=None):
    settings = load_settings()
    if not warning and not settings.get("notifications", True):
        return

    try:
        current_tag = tag or title
        current_group = group or APP_ID

        xml_content = f"""
        <toast>
            <visual>
                <binding template="ToastGeneric">
                    <text>{title}</text>
                    <text>{message}</text>
                </binding>
            </visual>
        """

        # Add actions if provided
        if actions:
            xml_content += "<actions>"
            for label, launch in actions:
                act_type = 'activationType="protocol"'
                xml_content += f'<action content="{label}" arguments="{launch}" {act_type}/>'
            xml_content += "</actions>"

        xml_content += "</toast>"


        xml_doc = XmlDocument()
        xml_doc.load_xml(xml_content)
        toast_obj = ToastNotification(xml_doc)

        toast_obj.tag = current_tag
        toast_obj.group = current_group

        # add expiration time for specific tags or groups
        if current_tag in ["sync-status", "sync-cancelled", "sync-wait"] or current_group in ["sync-status", "sync-cancelled"]:
            toast_obj.expiration_time = datetime.now() + timedelta(minutes=10)

        notifier = ToastNotificationManager.create_toast_notifier_with_id(APP_ID)
        notifier.show(toast_obj)

    except Exception as e:
        log("ERROR", f"Failed to send notification: {e}", console=False)


# def remove_notification(tag, group=None):
#     # INFO: Remove a toast that is no longer relevant (for example, a finished wait).
#     try:
#         #if group:
#         ToastNotificationManager.history.remove(tag, group, APP_ID)
#         #else:
#             #ToastNotificationManager.history.remove(tag)
#     except Exception as e:
#         log("WARNING", f"Failed to remove notification '{tag}' | '{APP_ID}': {e}", console=False)
