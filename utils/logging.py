import json
from time import strftime

from config import LOG_FILE

def log(level, message, console=False):
    try:
        log_entry = {
            "type": level,
            "message": message,
            "datetime": strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
            f.flush()
    except Exception as e:
        print(f"❌ Failed to write log: {e}")
    
    if console:
        print(level + ": " + message)
