from config import SETTINGS_FILE
import json

def load_settings():
    default_settings = {"notifications": True, "show_warning_on_manual_sync": True}
    if not SETTINGS_FILE.exists():
        return default_settings
    try:
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    except:
        return default_settings


def save_settings(settings):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f)
