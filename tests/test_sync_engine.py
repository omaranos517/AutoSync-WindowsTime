import sys
import types
import unittest
from unittest.mock import patch

sys.modules.setdefault(
    "winotify",
    types.SimpleNamespace(Notification=object, audio=types.SimpleNamespace(Default=None)),
)

from core import sync_engine
from core import timezones


class SyncTimezoneCorrectionTests(unittest.TestCase):
    def test_restores_preferred_timezone_when_its_offset_matches_again(self):
        settings = {
            "timezone_fallback": {
                "preferred_timezone": "Egypt Standard Time",
                "fallback_timezone": "E. Africa Standard Time",
            }
        }
        with (
            patch(
                "core.timezones.get_current_windows_timezone_online_offset",
                return_value={
                    "windows_id": "E. Africa Standard Time",
                    "matches": True,
                },
            ),
            patch(
                "core.timezones.get_windows_timezone_online_offset",
                return_value={"online_offset_minutes": 120},
            ),
            patch(
                "core.timezones.get_windows_timezone_offsets",
                return_value={"Egypt Standard Time": 120},
            ),
            patch("core.timezones.load_settings", return_value=settings),
            patch("core.timezones.save_settings") as save_settings,
            patch("core.timezones.run_cmd") as run_cmd,
        ):
            self.assertTrue(timezones.reconcile_windows_timezone())

        run_cmd.assert_called_once_with(["tzutil", "/s", "Egypt Standard Time"])
        self.assertNotIn("timezone_fallback", settings)
        save_settings.assert_called_once_with(settings)

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
