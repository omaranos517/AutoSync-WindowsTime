import json
import re
import subprocess
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from config import SETTINGS_FILE

COUNTRY_TIMEZONES = [
    ("UTC", "UTC", "Etc/UTC", "UTC"),
    ("Egypt", "Cairo", "Africa/Cairo", "Egypt Standard Time"),
    ("Saudi Arabia", "Riyadh", "Asia/Riyadh", "Arab Standard Time"),
    ("United Arab Emirates", "Abu Dhabi", "Asia/Dubai", "Arabian Standard Time"),
    ("Kuwait", "Kuwait City", "Asia/Kuwait", "Arab Standard Time"),
    ("Qatar", "Doha", "Asia/Qatar", "Arab Standard Time"),
    ("Bahrain", "Manama", "Asia/Bahrain", "Arab Standard Time"),
    ("Oman", "Muscat", "Asia/Muscat", "Arabian Standard Time"),
    ("Jordan", "Amman", "Asia/Amman", "Jordan Standard Time"),
    ("Lebanon", "Beirut", "Asia/Beirut", "Middle East Standard Time"),
    ("Syria", "Damascus", "Asia/Damascus", "Syria Standard Time"),
    ("Iraq", "Baghdad", "Asia/Baghdad", "Arabic Standard Time"),
    ("Yemen", "Sanaa", "Asia/Aden", "Arab Standard Time"),
    ("Libya", "Tripoli", "Africa/Tripoli", "Libya Standard Time"),
    ("Sudan", "Khartoum", "Africa/Khartoum", "Sudan Standard Time"),
    ("Morocco", "Rabat", "Africa/Casablanca", "Morocco Standard Time"),
    ("Tunisia", "Tunis", "Africa/Tunis", "W. Central Africa Standard Time"),
    ("Algeria", "Algiers", "Africa/Algiers", "W. Central Africa Standard Time"),
    ("United Kingdom", "London", "Europe/London", "GMT Standard Time"),
    ("France", "Paris", "Europe/Paris", "Romance Standard Time"),
    ("Germany", "Berlin", "Europe/Berlin", "W. Europe Standard Time"),
    ("Italy", "Rome", "Europe/Rome", "W. Europe Standard Time"),
    ("Spain", "Madrid", "Europe/Madrid", "Romance Standard Time"),
    ("Netherlands", "Amsterdam", "Europe/Amsterdam", "W. Europe Standard Time"),
    ("Greece", "Athens", "Europe/Athens", "GTB Standard Time"),
    ("Turkey", "Ankara", "Europe/Istanbul", "Turkey Standard Time"),
    ("Russia", "Moscow", "Europe/Moscow", "Russian Standard Time"),
    ("United States", "Washington, DC", "America/New_York", "Eastern Standard Time"),
    ("United States", "Chicago", "America/Chicago", "Central Standard Time"),
    ("United States", "Denver", "America/Denver", "Mountain Standard Time"),
    ("United States", "Los Angeles", "America/Los_Angeles", "Pacific Standard Time"),
    ("Canada", "Ottawa", "America/Toronto", "Eastern Standard Time"),
    ("Mexico", "Mexico City", "America/Mexico_City", "Central Standard Time (Mexico)"),
    ("Brazil", "Brasilia", "America/Sao_Paulo", "E. South America Standard Time"),
    ("Argentina", "Buenos Aires", "America/Argentina/Buenos_Aires", "Argentina Standard Time"),
    ("South Africa", "Pretoria", "Africa/Johannesburg", "South Africa Standard Time"),
    ("Nigeria", "Abuja", "Africa/Lagos", "W. Central Africa Standard Time"),
    ("Kenya", "Nairobi", "Africa/Nairobi", "E. Africa Standard Time"),
    ("India", "New Delhi", "Asia/Kolkata", "India Standard Time"),
    ("Pakistan", "Islamabad", "Asia/Karachi", "Pakistan Standard Time"),
    ("Bangladesh", "Dhaka", "Asia/Dhaka", "Bangladesh Standard Time"),
    ("China", "Beijing", "Asia/Shanghai", "China Standard Time"),
    ("Japan", "Tokyo", "Asia/Tokyo", "Tokyo Standard Time"),
    ("South Korea", "Seoul", "Asia/Seoul", "Korea Standard Time"),
    ("Singapore", "Singapore", "Asia/Singapore", "Singapore Standard Time"),
    ("Thailand", "Bangkok", "Asia/Bangkok", "SE Asia Standard Time"),
    ("Indonesia", "Jakarta", "Asia/Jakarta", "SE Asia Standard Time"),
    ("Philippines", "Manila", "Asia/Manila", "Singapore Standard Time"),
    ("Australia", "Canberra", "Australia/Sydney", "AUS Eastern Standard Time"),
    ("New Zealand", "Wellington", "Pacific/Auckland", "New Zealand Standard Time"),
]

_ONLINE_TIMEZONE_CACHE = {}
_WINDOWS_OFFSET_CACHE = None


def _timezone_label(country, capital, iana_timezone, offset):
    offset_text = f"UTC{offset}" if offset else "UTC offset online unavailable"
    return f"{country} - {capital} ({offset_text}) [{iana_timezone}]"


TIMEZONE_BY_IANA = {
    iana_timezone: {
        "country": country,
        "capital": capital,
        "iana_timezone": iana_timezone,
        "preferred_windows_id": preferred_windows_id,
    }
    for country, capital, iana_timezone, preferred_windows_id in COUNTRY_TIMEZONES
}
TIMEZONE_ID_TO_LABEL = {}
for country, capital, iana_timezone, preferred_windows_id in COUNTRY_TIMEZONES:
    TIMEZONE_ID_TO_LABEL.setdefault(preferred_windows_id, f"{country} - {capital} [{preferred_windows_id}]")


def load_settings():
    default_settings = {
        "notifications": True,
        "show_warning_on_manual_sync": True,
    }
    if not SETTINGS_FILE.exists():
        return default_settings
    try:
        with open(SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
            if not isinstance(settings, dict):
                return default_settings
            settings.setdefault("notifications", True)
            settings.setdefault("show_warning_on_manual_sync", True)
            return settings
    except:
        return default_settings


def save_settings(settings):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f)


def get_timezone_options():
    options = []
    known_windows_ids = {preferred_windows_id for *_location, preferred_windows_id in COUNTRY_TIMEZONES}

    with ThreadPoolExecutor(max_workers=12) as executor:
        online_offsets = list(
            executor.map(
                lambda item: get_online_timezone_info(item[2]).get("utc_offset"),
                COUNTRY_TIMEZONES,
            )
        )

    for (country, capital, iana_timezone, _preferred_windows_id), offset in zip(COUNTRY_TIMEZONES, online_offsets):
        options.append(_timezone_label(country, capital, iana_timezone, offset))

    for label, windows_id in get_windows_timezone_options():
        if windows_id not in known_windows_ids:
            options.append(label)

    return options


def get_timezone_id(selected_timezone):
    return resolve_windows_timezone_id(selected_timezone)


def _extract_bracket_value(selected_timezone):
    if selected_timezone:
        match = re.search(r"\[([^\[\]]+)\]$", selected_timezone)
        if match:
            return match.group(1)
    return selected_timezone


def resolve_windows_timezone_id(selected_timezone):
    timezone_key = _extract_bracket_value(selected_timezone)
    if timezone_key in TIMEZONE_BY_IANA:
        return resolve_windows_timezone_for_iana(timezone_key)
    return timezone_key


def resolve_windows_timezone_for_iana(iana_timezone):
    timezone_info = TIMEZONE_BY_IANA[iana_timezone]
    preferred_windows_id = timezone_info["preferred_windows_id"]
    online_info = get_online_timezone_info(iana_timezone)
    target_offset = online_info.get("utc_offset")

    if not target_offset:
        return preferred_windows_id

    windows_offsets = get_windows_timezone_current_offsets()
    preferred_offset = windows_offsets.get(preferred_windows_id)
    if preferred_offset == target_offset:
        return preferred_windows_id

    for windows_id, current_offset in windows_offsets.items():
        if current_offset == target_offset:
            return windows_id

    return preferred_windows_id


def get_timezone_label(windows_timezone_id):
    return TIMEZONE_ID_TO_LABEL.get(windows_timezone_id, windows_timezone_id or "UTC")


def get_current_windows_timezone():
    try:
        result = subprocess.run(["tzutil", "/g"], check=True, capture_output=True, text=True)
        return result.stdout.strip() or "UTC"
    except (FileNotFoundError, subprocess.CalledProcessError):
        return "UTC"


def get_windows_timezone_options():
    try:
        result = subprocess.run(["tzutil", "/l"], check=True, capture_output=True, text=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        return []

    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    options = []
    for index in range(0, len(lines) - 1, 2):
        display_name = lines[index]
        windows_id = lines[index + 1]
        options.append((f"{display_name} [{windows_id}]", windows_id))
    return options


def get_online_timezone_info(iana_timezone):
    if iana_timezone in _ONLINE_TIMEZONE_CACHE:
        return _ONLINE_TIMEZONE_CACHE[iana_timezone]

    encoded_timezone = urllib.parse.quote(iana_timezone, safe="/")
    url = f"https://worldtimeapi.org/api/timezone/{encoded_timezone}"
    try:
        with urllib.request.urlopen(url, timeout=2) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception:
        payload = {}

    info = {
        "utc_offset": payload.get("utc_offset"),
        "dst": payload.get("dst"),
        "abbreviation": payload.get("abbreviation"),
        "timezone": payload.get("timezone") or iana_timezone,
    }
    _ONLINE_TIMEZONE_CACHE[iana_timezone] = info
    return info


def get_windows_timezone_current_offsets():
    global _WINDOWS_OFFSET_CACHE
    if _WINDOWS_OFFSET_CACHE is not None:
        return _WINDOWS_OFFSET_CACHE

    command = (
        "[System.TimeZoneInfo]::GetSystemTimeZones() | ForEach-Object { "
        "$offset = $_.GetUtcOffset([datetime]::UtcNow); "
        "'{0}|{1}' -f $_.Id, $offset.ToString() "
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
        _WINDOWS_OFFSET_CACHE = {}
        return _WINDOWS_OFFSET_CACHE

    offsets = {}
    for line in result.stdout.splitlines():
        if "|" not in line:
            continue
        windows_id, raw_offset = line.strip().split("|", 1)
        offsets[windows_id] = _normalize_windows_offset(raw_offset)

    _WINDOWS_OFFSET_CACHE = offsets
    return offsets


def _normalize_windows_offset(raw_offset):
    match = re.match(r"(-?)(\d{1,2}):(\d{2})(?::\d{2})?$", raw_offset.strip())
    if not match:
        return raw_offset
    sign, hours, minutes = match.groups()
    sign = "-" if sign else "+"
    return f"{sign}{int(hours):02d}:{minutes}"
