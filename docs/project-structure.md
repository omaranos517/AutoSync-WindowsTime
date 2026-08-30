# Project Structure

This guide explains what each folder in the repository is for and where new files should go.

## Root

- `README.md` - the main landing page for the project
- `main.py` - the application entry point that launches the app
- `docs/` - full documentation
- `assets/` - icons, scripts, and packaged resources used by the app
- `cli/` - command-line parsing and command dispatch
- `config/` - application constants and settings
- `core/` - sync logic, internet checks, and Task Scheduler integration
- `ui/` - graphical user interface code
- `utils/` - shared helpers such as logging, admin elevation, and command execution
- `packaging/` - build scripts, installer scripts, and packaging requirements

## File-by-File Guide

### `assets/`

- `assets/icon.ico` - Windows app icon
- `assets/icon.png` - image asset version of the icon
- `assets/timesync.bat` - Windows launcher batch file
- `assets/timesync-completion.ps1` - PowerShell completion script

### `cli/`

- `cli/parser.py` - defines the command-line arguments and subcommands
- `cli/dispatcher.py` - routes parsed CLI commands to the appropriate handler or action
- `cli/commands.py` - contains the actual CLI command handlers and command mapping

### `config/`

- `config/constants.py` - application-wide constants such as names, paths, and metadata
- `config/settings.py` - reading and writing user settings

### `core/`

- `core/actions.py` - high-level actions such as syncing, status checks, and related operations
- `core/sync_engine.py` - the main sync flow and fallback logic
- `core/internet_check.py` - checks whether the machine is online before syncing
- `core/task_scheduler.py` - creates, removes, and checks scheduled tasks
- `core/timezones.py` - resolves country/capital time zones to Windows time zone IDs using live offset matching

### `ui/`

- `ui/gui.py` - main GUI window and app entry flow
- `ui/about_window.py` - about dialog and app information window

### `utils/`

- `utils/admin.py` - admin elevation helpers
- `utils/command_runner.py` - command execution helpers
- `utils/app_logger.py` - logging setup and log file handling
- `utils/console.py` - helper functions for enabling ANSI colors in the console and formatting text with success, error, warning, and info styles
- `utils/notifySystem.py` - Windows notification helpers
- `utils/protocol.py` - custom protocol handling for app actions

### `packaging/`

- `packaging/TimeSync.spec` - PyInstaller spec file
- `packaging/TimeSyncCompiler.iss` - Inno Setup installer script
- `packaging/requirements.txt` - build-time Python dependencies
- `packaging/version_info.txt` - version metadata used by the Windows packaging workflow

## Where To Put New Files

- New user-facing documentation belongs in `docs/`
- Technical design notes belong in `docs/architecture/`
- New shared Python helpers belong in `utils/`
- New sync-related logic belongs in `core/`
- New CLI commands belong in `cli/`
- New UI windows or widgets belong in `ui/`

## Suggested Rule

If a file answers "how do I use this?" place it in `docs/`.
If a file answers "how do I build or ship this?" place it in `docs/packaging/`.
If a file answers "how does this code work?" place it near the code it documents or in `docs/architecture/`.
