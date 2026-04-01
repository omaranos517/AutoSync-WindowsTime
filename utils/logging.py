import json
from time import strftime

from config import LOG_FILE

MAX_LOG_LINES = 100

def log(level, message, console=False):
    try:
        lines = []
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
            while len(lines) >= MAX_LOG_LINES:
                lines.pop(0)
        except FileNotFoundError:
            print("The first log entry is being created.")

        log_entry = {
            "type": level,
            "message": message,
            "datetime": strftime("%Y-%m-%d %H:%M:%S")
        }

        lines.append(json.dumps(log_entry, ensure_ascii=False) + "\n")
        # إعادة كتابة كل السطور بعد القص
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.writelines(lines)

    except Exception as e:
        print(f"❌ Failed to write log: {e}")
    
    if console or level in ["ERROR", "WARNING"]:
        print(level + ": " + message)
        print("For more details, check the log file at: " + str(LOG_FILE))
