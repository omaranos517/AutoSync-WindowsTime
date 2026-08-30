import json

from config import SETTINGS_FILE


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
