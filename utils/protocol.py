import sys
from urllib.parse import urlparse, parse_qs

from config import PROTOCOL, APP_NAME, APP_DIR
from utils import log

def _protocol_exe_path():
    candidate = APP_DIR / "timesync-gui.exe"
    if candidate.exists():
        return candidate
    return None


def ensure_protocol_registered():
    exe_path = _protocol_exe_path()
    if not exe_path:
        return

    try:
        import winreg

        base_key = fr"Software\Classes\{PROTOCOL}"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, base_key) as k:
            winreg.SetValueEx(k, None, 0, winreg.REG_SZ, f"URL:{APP_NAME} Protocol")
            winreg.SetValueEx(k, "URL Protocol", 0, winreg.REG_SZ, "")

        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, base_key + r"\DefaultIcon") as k:
            winreg.SetValueEx(k, None, 0, winreg.REG_SZ, f"{exe_path},1")

        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, base_key + r"\shell\open\command") as k:
            winreg.SetValueEx(k, None, 0, winreg.REG_SZ, f"\"{exe_path}\" \"%1\"")
    except Exception as e:
        log("WARNING", f"Failed to register protocol: {e}", console=False)


def normalize_protocol_args():
    if len(sys.argv) != 2:
        return

    raw = sys.argv[1]
    if not raw.startswith(f"{PROTOCOL}://"):
        return

    parsed = urlparse(raw)
    command = parsed.netloc or parsed.path.lstrip("/")
    if not command:
        return

    sys.argv = [sys.argv[0], command]
    if command == "now":
        query = parse_qs(parsed.query or "")
        if query.get("auto", ["0"])[0] == "1":
            sys.argv.append("--auto")
