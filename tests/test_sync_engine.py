import sys
import types
import unittest
from unittest.mock import patch

sys.modules.setdefault(
    "winotify",
    types.SimpleNamespace(Notification=object, audio=types.SimpleNamespace(Default=None)),
)

from core import sync_engine


class SyncTimezoneCorrectionTests(unittest.TestCase):
    def test_resyncs_after_timezone_was_corrected(self):
        with (
            patch("core.sync_engine.attempt_time_sync", side_effect=[True, True]) as sync,
            patch("core.sync_engine._correct_windows_timezone_from_online_offset", return_value=True),
        ):
            self.assertTrue(sync_engine._sync_with_timezone_correction(silent=True))

        self.assertEqual(sync.call_count, 2)

    def test_does_not_resync_when_offset_already_matches(self):
        with (
            patch("core.sync_engine.attempt_time_sync", return_value=True) as sync,
            patch("core.sync_engine._correct_windows_timezone_from_online_offset", return_value=False),
        ):
            self.assertTrue(sync_engine._sync_with_timezone_correction(silent=True))

        sync.assert_called_once_with(True)


if __name__ == "__main__":
    unittest.main()
