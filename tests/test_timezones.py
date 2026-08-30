import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

import config.settings as settings_module
import core.timezones as timezones_module

sys.modules.setdefault(
    "winotify",
    types.SimpleNamespace(Notification=object, audio=types.SimpleNamespace(Default=None)),
)

from core import actions


class TimezoneSettingsTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.settings_file = Path(self.temp_dir.name) / "settings.json"
        settings_module.SETTINGS_FILE = self.settings_file

    def test_default_timezone_is_available(self):
        with patch("core.timezones.get_online_timezone_info", return_value={"utc_offset": "+00:00"}):
            options = timezones_module.get_timezone_options()

        self.assertIn("UTC - UTC (UTC+00:00) [Etc/UTC]", options)

    def test_timezone_selection_is_not_saved_to_settings(self):
        settings = settings_module.load_settings()
        settings_module.save_settings(settings)

        self.assertNotIn("timezone", settings_module.load_settings())

        with (
            patch("core.timezones.get_online_timezone_info", return_value={"utc_offset": "+02:00"}),
            patch(
                "core.timezones.get_windows_timezone_current_offsets",
                return_value={
                    "Egypt Standard Time": "+01:00",
                    "South Africa Standard Time": "+02:00",
                },
            ),
            patch("subprocess.run") as run,
        ):
            actions.set_timezone("Egypt - Cairo (UTC+02:00) [Africa/Cairo]")

        run.assert_called_once_with(
            ["tzutil", "/s", "South Africa Standard Time"],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertNotIn("timezone", settings_module.load_settings())

    def test_timezone_uses_matching_windows_offset_when_preferred_is_wrong(self):
        with (
            patch("core.timezones.get_online_timezone_info", return_value={"utc_offset": "+02:00"}),
            patch(
                "core.timezones.get_windows_timezone_current_offsets",
                return_value={
                    "Egypt Standard Time": "+01:00",
                    "South Africa Standard Time": "+02:00",
                },
            ),
        ):
            timezone_id = timezones_module.resolve_windows_timezone_for_iana("Africa/Cairo")

        self.assertEqual(timezone_id, "South Africa Standard Time")


if __name__ == "__main__":
    unittest.main()
