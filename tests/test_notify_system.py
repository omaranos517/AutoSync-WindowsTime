import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

# Keep import-time settings and logging isolated from the user's real AppData.
os.environ["LOCALAPPDATA"] = tempfile.mkdtemp(prefix="timesync-tests-")

from config import APP_ID
from utils import notifySystem


class SendNotificationTests(unittest.TestCase):
    def _send_with_mocks(self, **kwargs):
        xml_document = MagicMock()
        toast = MagicMock()
        notifier = MagicMock()

        with (
            patch("utils.notifySystem.load_settings", return_value={"notifications": True}),
            patch("utils.notifySystem.XmlDocument", return_value=xml_document),
            patch("utils.notifySystem.ToastNotification", return_value=toast),
            patch("utils.notifySystem.ToastNotificationManager") as manager,
        ):
            manager.create_toast_notifier_with_id.return_value = notifier
            notifySystem.send_notification("Time Sync Success", "Time synchronized.", **kwargs)

        return xml_document, toast, notifier, manager

    def test_uses_notifier_with_app_id(self):
        """Protect against calling the zero-argument WinRT overload by mistake."""
        _, _, notifier, manager = self._send_with_mocks()

        manager.create_toast_notifier_with_id.assert_called_once_with(APP_ID)
        manager.create_toast_notifier.assert_not_called()
        notifier.show.assert_called_once()

    def test_sets_group_tag_expiration_and_protocol_actions(self):
        xml_document, toast, notifier, manager = self._send_with_mocks(
            actions=[("Cancel", "timesync://cancel")],
            tag="sync-status",
            group="sync-status",
        )

        xml = xml_document.load_xml.call_args.args[0]
        self.assertIn('<action content="Cancel" arguments="timesync://cancel" activationType="protocol"/>', xml)
        self.assertEqual(toast.tag, "sync-status")
        self.assertEqual(toast.group, "sync-status")
        self.assertIsNotNone(toast.expiration_time)
        manager.create_toast_notifier_with_id.assert_called_once_with(APP_ID)
        notifier.show.assert_called_once_with(toast)

    def test_does_not_send_when_notifications_are_disabled(self):
        with (
            patch("utils.notifySystem.load_settings", return_value={"notifications": False}),
            patch("utils.notifySystem.XmlDocument") as xml_document,
        ):
            notifySystem.send_notification("Title", "Message")

        xml_document.assert_not_called()


if __name__ == "__main__":
    unittest.main()
