"""Read and apply only the time zones installed by Windows.

Windows owns the daylight-saving rules for its time-zone IDs. Keeping a
second, hand-maintained country/IANA table here made it possible for the UI to
offer a zone that did not match the user's installed Windows rules.
"""

import json
import re
import subprocess
import urllib.parse
import urllib.request
import xml.etree.ElementTree as element_tree
from datetime import datetime, timezone


_WINDOWS_TO_IANA_CACHE = None


def get_windows_timezone_options():
    """Return ``(display label, Windows ID)`` pairs reported by ``tzutil``."""
    try:
        result = subprocess.run(
            ["tzutil", "/l"], check=True, capture_output=True, text=True
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return []

    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return [
        (f"{lines[index]} [{lines[index + 1]}]", lines[index + 1])
        for index in range(0, len(lines) - 1, 2)
    ]


def get_timezone_options():
    """Return all and only the time zones currently available in Windows."""
    return [label for label, _windows_id in get_windows_timezone_options()]


def find_timezone_matches(query):
    """Search Windows' installed display names and IDs without static mappings."""
    normalized_query = (query or "").strip().lower()
    if not normalized_query:
        return []

    return [
        {"windows_id": windows_id, "label": label}
        for label, windows_id in get_windows_timezone_options()
        if normalized_query in label.lower() or normalized_query in windows_id.lower()
    ]


def _extract_bracket_value(selected_timezone):
    if selected_timezone:
        match = re.search(r"\[([^\[\]]+)\]$", selected_timezone)
        if match:
            return match.group(1).strip()
    return (selected_timezone or "").strip()


def get_timezone_id(selected_timezone):
    """Return a Windows ID from a generated label or a raw Windows ID."""
    return _extract_bracket_value(selected_timezone)


def get_timezone_label(windows_timezone_id):
    for label, timezone_id in get_windows_timezone_options():
        if timezone_id == windows_timezone_id:
            return label
    return windows_timezone_id or "UTC"


def get_current_windows_timezone():
    try:
        result = subprocess.run(
            ["tzutil", "/g"], check=True, capture_output=True, text=True
        )
        return result.stdout.strip() or "UTC"
    except (FileNotFoundError, subprocess.CalledProcessError):
        return "UTC"


def get_iana_timezone_for_windows_id(windows_timezone_id):
    """Resolve a Windows ID through CLDR's live Windows-to-IANA mapping."""
    global _WINDOWS_TO_IANA_CACHE
    if _WINDOWS_TO_IANA_CACHE is None:
        try:
            with urllib.request.urlopen(
                "https://raw.githubusercontent.com/unicode-org/cldr/main/"
                "common/supplemental/windowsZones.xml",
                timeout=5,
            ) as response:
                root = element_tree.fromstring(response.read())
            _WINDOWS_TO_IANA_CACHE = {
                item.attrib["other"]: item.attrib["type"].split()[0]
                for item in root.findall(".//mapZone[@territory='001']")
            }
        except (OSError, element_tree.ParseError):
            _WINDOWS_TO_IANA_CACHE = {}

    return _WINDOWS_TO_IANA_CACHE.get(windows_timezone_id)


def get_current_windows_timezone_online_offset():
    """Return TimeAPI's current offset for the active Windows time zone.

    The conversion is obtained from CLDR at runtime, not a hard-coded mapping.
    ``difference_minutes`` is positive when the online local time is ahead of
    the local time currently produced by Windows.
    """
    windows_id = get_current_windows_timezone()
    iana_timezone = get_iana_timezone_for_windows_id(windows_id)
    if not iana_timezone:
        return None

    url = "https://timeapi.io/api/Time/current/zone?" + urllib.parse.urlencode(
        {"timeZone": iana_timezone}
    )
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        online_time = datetime(
            payload["year"], payload["month"], payload["day"],
            payload["hour"], payload["minute"], payload["seconds"],
            int(payload.get("milliSeconds", 0)) * 1000,
        )
    except (KeyError, TypeError, ValueError, OSError, json.JSONDecodeError):
        return None

    utc_now = datetime.now(timezone.utc).replace(tzinfo=None)
    windows_now = datetime.now().replace(tzinfo=None)
    online_offset_minutes = round((online_time - utc_now).total_seconds() / 60)
    windows_offset_minutes = round((windows_now - utc_now).total_seconds() / 60)
    difference_minutes = online_offset_minutes - windows_offset_minutes
    return {
        "windows_id": windows_id,
        "iana_timezone": iana_timezone,
        "online_offset_minutes": online_offset_minutes,
        "windows_offset_minutes": windows_offset_minutes,
        "difference_minutes": difference_minutes,
        "matches": difference_minutes == 0,
        "dst_active": payload.get("dstActive"),
    }


def set_windows_timezone_for_online_offset(timezone_info):
    """Select an installed Windows zone whose current offset matches TimeAPI.

    Preference is given to an IANA zone in the same geographic area as the
    selected zone (for example, another ``Africa/*`` zone). This remains a
    runtime decision; the project does not ship a Windows/IANA mapping table.
    """
    if not timezone_info or timezone_info["matches"]:
        return None

    command = (
        "[System.TimeZoneInfo]::GetSystemTimeZones() | ForEach-Object { "
        "'{0}|{1}' -f $_.Id, [int]$_.GetUtcOffset([datetime]::UtcNow).TotalMinutes "
        "}"
    )
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None

    desired_offset = timezone_info["online_offset_minutes"]
    current_id = timezone_info["windows_id"]
    current_area = timezone_info["iana_timezone"].split("/", 1)[0]
    candidates = []
    for line in result.stdout.splitlines():
        try:
            windows_id, offset = line.strip().rsplit("|", 1)
            if windows_id != current_id and int(offset) == desired_offset:
                candidate_iana = get_iana_timezone_for_windows_id(windows_id) or ""
                same_area = candidate_iana.split("/", 1)[0] == current_area
                candidates.append((not same_area, windows_id))
        except ValueError:
            continue

    if not candidates:
        return None

    target_id = min(candidates)[1]
    try:
        subprocess.run(
            ["tzutil", "/s", target_id],
            check=True,
            capture_output=True,
            text=True,
        )
        return target_id
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
