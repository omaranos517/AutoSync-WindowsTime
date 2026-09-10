import sys
import tempfile
import types
import unittest
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import MagicMock, call, patch

import config.settings as settings_module
import core.timezones as timezones_module

sys.modules.setdefault(
    "winotify",
    types.SimpleNamespace(Notification=object, audio=types.SimpleNamespace(Default=None)),
)

from core import actions


WINDOWS_TIMEZONES = (
    "(UTC) Coordinated Universal Time\nUTC\n"
    "(UTC+02:00) Cairo\nEgypt Standard Time\n"
)


class TimezoneSettingsTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.settings_file = Path(self.temp_dir.name) / "settings.json"
        settings_module.SETTINGS_FILE = self.settings_file

    def test_options_come_directly_from_windows(self):
        with patch("subprocess.run") as run:
            run.return_value.stdout = WINDOWS_TIMEZONES
            options = timezones_module.get_timezone_options()

        self.assertEqual(
            options,
            [
                "(UTC) Coordinated Universal Time [UTC]",
                "(UTC+02:00) Cairo [Egypt Standard Time]",
            ],
        )
        run.assert_called_once_with(
            ["tzutil", "/l"], check=True, capture_output=True, text=True
        )

    def test_timezone_selection_is_not_saved_to_settings(self):
        settings = settings_module.load_settings()
        settings_module.save_settings(settings)
        self.assertNotIn("timezone", settings_module.load_settings())

        with patch("subprocess.run") as run:
            actions.set_timezone("(UTC+02:00) Cairo [Egypt Standard Time]")

        self.assertEqual(
            run.call_args_list[0],
            call(
                ["tzutil", "/s", "Egypt Standard Time"],
                check=True,
                capture_output=True,
                text=True,
            ),
        )
        self.assertNotIn("timezone", settings_module.load_settings())

    def test_search_uses_windows_display_name_and_id(self):
        with patch("subprocess.run") as run:
            run.return_value.stdout = WINDOWS_TIMEZONES
            matches = timezones_module.find_timezone_matches("egypt standard")

        self.assertEqual(matches[0]["windows_id"], "Egypt Standard Time")

    def test_windows_id_is_resolved_from_live_cldr_mapping(self):
        xml = b"""<supplementalData><windowsZones><mapTimezones>
        <mapZone other='Egypt Standard Time' territory='001' type='Africa/Cairo'/>
        </mapTimezones></windowsZones></supplementalData>"""
        response = MagicMock()
        response.read.return_value = xml
        timezones_module._WINDOWS_TO_IANA_CACHE = None

        with patch("urllib.request.urlopen") as urlopen:
            urlopen.return_value.__enter__.return_value = response
            result = timezones_module.get_iana_timezone_for_windows_id(
                "Egypt Standard Time"
            )

        self.assertEqual(result, "Africa/Cairo")

    def test_online_offset_uses_resolved_iana_timezone(self):
        response = MagicMock()
        response.read.return_value = (
            b'{"year": 2026, "month": 1, "day": 1, "hour": 15, '
            b'"minute": 0, "seconds": 0, "milliSeconds": 0, "dstActive": true}'
        )

        class FixedDateTime(datetime):
            @classmethod
            def now(cls, tz=None):
                value = datetime(2026, 1, 1, 12, 0, 0)
                return value.replace(tzinfo=timezone.utc) if tz else value

        with (
            patch("core.timezones.get_current_windows_timezone", return_value="Egypt Standard Time"),
            patch("core.timezones.get_iana_timezone_for_windows_id", return_value="Africa/Cairo"),
            patch("core.timezones.datetime", FixedDateTime),
            patch("urllib.request.urlopen") as urlopen,
        ):
            urlopen.return_value.__enter__.return_value = response
            info = timezones_module.get_current_windows_timezone_online_offset()

        self.assertEqual(info["online_offset_minutes"], 180)
        self.assertEqual(info["difference_minutes"], 180)
        self.assertFalse(info["matches"])

    def test_matching_windows_zone_is_applied_for_online_offset(self):
        offsets = (
            "Egypt Standard Time|120\n"
            "Arab Standard Time|180\n"
            "E. Africa Standard Time|180\n"
        )
        info = {
            "matches": False,
            "online_offset_minutes": 180,
            "windows_id": "Egypt Standard Time",
            "iana_timezone": "Africa/Cairo",
        }
        with (
            patch("subprocess.run") as run,
            patch(
                "core.timezones.get_iana_timezone_for_windows_id",
                side_effect=lambda timezone_id: {
                    "Arab Standard Time": "Asia/Riyadh",
                    "E. Africa Standard Time": "Africa/Nairobi",
                }.get(timezone_id),
            ),
        ):
            run.return_value.stdout = offsets
            applied = timezones_module.set_windows_timezone_for_online_offset(info)

        self.assertEqual(applied, "E. Africa Standard Time")
        self.assertEqual(
            run.call_args_list[-1],
            call(
                ["tzutil", "/s", "E. Africa Standard Time"],
                check=True,
                capture_output=True,
                text=True,
            ),
        )


if __name__ == "__main__":
    unittest.main()
