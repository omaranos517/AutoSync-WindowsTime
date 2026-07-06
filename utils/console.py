import ctypes


class Color:
    DEFFAULT = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"


def enable_ansi_colors():
    try:
        handle = ctypes.windll.kernel32.GetStdHandle(-11)
        if handle == 0:
            return
        mode = ctypes.c_uint()
        if ctypes.windll.kernel32.GetConsoleMode(handle, ctypes.byref(mode)) == 0:
            return
        virtual_terminal = 0x0004
        if mode.value & virtual_terminal:
            return
        ctypes.windll.kernel32.SetConsoleMode(handle, mode.value | virtual_terminal)
    except Exception:
        pass


def colorize(text: str, color: str) -> str:
    return f"{color}{text}{Color.DEFFAULT}"


def success_text(text: str) -> str:
    return colorize(text, Color.GREEN)


def error_text(text: str) -> str:
    return colorize(text, Color.RED)


def warning_text(text: str) -> str:
    return colorize(text, Color.YELLOW)


def info_text(text: str) -> str:
    return colorize(text, Color.CYAN)


def enabled_disabled_text(enabled: bool) -> str:
    return success_text("Enabled") if enabled else error_text("Disabled")