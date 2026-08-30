from pathlib import Path

from core import actions
from config import APP_DIR, AUTHOR, VERSION, GITHUB, LOG_FILE
from utils.console import success_text, error_text, warning_text, info_text, enabled_disabled_text


# ==================================================
# CLI-ONLY COMMANDS
# ==================================================
# This module contains the command handlers that are used only by the
# command-line interface (CLI). It does not contain GUI-related logic.
# ==================================================


def print_status():
    status = actions.get_status(include_timezone_options=False)
    print("\n=== TimeSync Status ===\n")

    print(success_text("🔐 Running as Administrator") if status['isAdmin'] else warning_text("⚠️ Not running as Administrator"))
    print(f"🚀 Startup with Windows: {enabled_disabled_text(status['startUp'])}")
    print(f"🕐 Periodic Hourly Sync: {enabled_disabled_text(status['periodic'])}")
    print(f"💤 Sync on Wake: {enabled_disabled_text(status['resume'])}")
    print(f"🔔 Notifications: {enabled_disabled_text(status['notify'])}")
    print(f"🌍 Windows Time Zone: {status['timezone']}")
    print("\n💡 Just type 'timesync' without arguments to open the Graphical Interface")
    print("\nFor more details, check the log file at:", LOG_FILE)
    print("\n")


def cmd_about():
    """Prints information about the TimeSync tool, including version, author, and GitHub link, in a formatted box."""
    print(f"""
╔══════════════════════════════════════════════╗
║                  TimeSync Tool               ║
╠══════════════════════════════════════════════╣
║
║  Version  : {VERSION}
║  Author   : {AUTHOR}
║  GitHub   : {GITHUB}
║
╠══════════════════════════════════════════════╣
║        Windows Time Synchronization Tool     ║
╚══════════════════════════════════════════════╝
""")


def cmd_version():
    print(f"TimeSync v{VERSION}")


def cmd_timezone(action="status", query=None):
    """Manage Windows timezone from the CLI using the same backend as the GUI."""
    if action in (None, "status"):
        status = actions.get_timezone_status()
        print("\n=== Time Zone Status ===\n")
        print(f"Time Zone: {status['label']}")
        print("\n")
        return

    if action == "list":
        print("\n=== Supported Time Zones ===\n")
        for timezone in actions.list_timezones():
            print(f"- {timezone}")
        print("\n")
        return

    if action != "set":
        print(error_text(f"Unknown timezone action: {action}"))
        return

    query = (query or "").strip()
    if not query:
        print(error_text("Timezone query is required."))
        return

    matches = actions.search_timezones(query)
    if not matches:
        try:
            applied_timezone = actions.set_timezone(query)
            print(success_text(f"Time zone set to: {applied_timezone}"))
        except Exception as exc:
            print(error_text(f"Failed to set time zone: {exc}"))
        return

    if len(matches) > 1:
        print(warning_text(f"Multiple time zones matched '{query}':"))
        for match in matches:
            print(f"- {match['label']}")
        print(info_text("\nUse a more specific country, capital, or IANA timezone."))
        return

    selected_timezone = matches[0]["label"]
    try:
        applied_timezone = actions.set_timezone(selected_timezone)
        print(success_text(f"Time zone set to: {applied_timezone}"))
    except Exception as exc:
        print(error_text(f"Failed to set time zone: {exc}"))


# ==================================================
# AUTO COMMANDS
# ==================================================

TOP_LEVEL_COMMANDS = [
    "now",
    "logs",
    "help",
    "commands",
    "status",
    "startup",
    "resume",
    "notify",
    "timezone",
    "about",
    "version",
]

COMPLETION_COMMANDS = {
    "startup": ["status", "enable", "disable"],
    "periodic": ["status", "enable", "disable"],
    "resume": ["status", "enable", "disable"],
    "notify": ["status", "enable", "disable"],
    "timezone": ["status", "list", "set"],
}


def build_powershell_completion_script():
    """Builds a PowerShell script for command auto-completion based on the defined top-level commands and action commands."""
    top_commands = ", ".join(f"'{cmd}'" for cmd in TOP_LEVEL_COMMANDS)
    action_lines = []
    for name, actions_list in COMPLETION_COMMANDS.items():
        quoted_actions = ", ".join("'" + action + "'" for action in actions_list)
        action_lines.append(f"    {name} = @({quoted_actions})")
    action_map = "\n".join(action_lines)
    template_candidates = [
        APP_DIR / "timesync-completion.ps1",
        Path(__file__).resolve().parent / "assets" / "timesync-completion.ps1",
    ]

    template_path = next((path for path in template_candidates if path.exists()), None)
    if not template_path:
        raise FileNotFoundError("timesync-completion.ps1 template was not found.")

    template = template_path.read_text(encoding="utf-8")
    return (
        template
        .replace("__TOP_LEVEL_COMMANDS__", top_commands)
        .replace("__ACTION_MAP__", action_map)
    )


def cmd_completion(shell, install=False):
    """Generates and optionally installs the command auto-completion script for the specified shell. Currently supports PowerShell."""
    if shell != "powershell":
        return

    script = build_powershell_completion_script()

    if not install:
        print(script)
        return

    start_marker = "# >>> TimeSync autocomplete >>>"
    end_marker = "# <<< TimeSync autocomplete <<<"
    block = f"{start_marker}\n{script.rstrip()}\n{end_marker}\n"
    profile_paths = [
        Path.home() / "Documents" / "PowerShell" / "Microsoft.PowerShell_profile.ps1",
        Path.home() / "Documents" / "WindowsPowerShell" / "Microsoft.PowerShell_profile.ps1",
    ]

    installed_paths = []
    for profile_path in profile_paths:
        profile_path.parent.mkdir(parents=True, exist_ok=True)

        existing = profile_path.read_text(encoding="utf-8") if profile_path.exists() else ""
        if start_marker in existing and end_marker in existing:
            start_index = existing.index(start_marker)
            end_index = existing.index(end_marker) + len(end_marker)
            existing = existing[:start_index].rstrip() + "\n\n" + existing[end_index:].lstrip()

        new_content = existing.rstrip()
        if new_content:
            new_content += "\n\n"
        new_content += block

        profile_path.write_text(new_content, encoding="utf-8")
        installed_paths.append(profile_path)

    for profile_path in installed_paths:
        print(f"- {profile_path}")
    for profile_path in installed_paths:
        print(f". '{profile_path}'")


COMMANDS = {
    "cancel": actions.create_cancel_file,
    "disable-warning": actions.disable_warning_action,
    "restart-pc": actions.restart_pc,
    "status": print_status,
    "logs": actions.open_logs,
    "about": cmd_about,
    "version": cmd_version,
}

ACTION_COMMANDS = {
    "startup": actions.toggle_startup,
    "periodic": actions.toggle_periodic,
    "resume": actions.toggle_resume,
    "notify": actions.toggle_notify,
}
