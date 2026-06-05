# Build Guide

This document explains how to build TimeSync from source using the current packaging files.

## Packaging Files

- `packaging/TimeSync.spec` - PyInstaller build definition
- `packaging/TimeSyncCompiler.iss` - Inno Setup installer definition
- `packaging/requirements.txt` - build dependencies

## 1) Prerequisites

- Windows 10/11
- Python 3.10+ (same architecture you target, usually x64)
- [Inno Setup](https://www.jrsoftware.org/isinfo.php) 6 (for `.iss` installer compilation)
- Optional: [upx.exe](https://github.com/upx/upx) in project root

## 2) Install Python dependencies

From the project root:

```powershell
python -m venv env
.\env\Scripts\Activate.ps1
pip install -r packaging/requirements.txt
```

## 3) Build executables with PyInstaller

From the project root, run:

```powershell
PyInstaller packaging/TimeSync.spec --clean
```

Expected output folder:

- `dist/TimeSync/`

That folder should contain (at minimum):

- `timesync-cli.exe`
- `timesync-gui.exe`
- packaged asset files from `assets/`

## 4) Build installer with Inno Setup

Compile this script:

- `packaging/TimeSyncCompiler.iss`

You can compile it from [Inno Setup](https://www.jrsoftware.org/isinfo.php) GUI, or via command line (if `ISCC.exe` is on PATH):

```powershell
ISCC packaging/TimeSyncCompiler.iss
```

Expected installer output:

- `output/TimeSync_<VERSION>_Setup.exe`

## 5) Notes about current build files

- `TimeSync.spec` resolves paths relative to the spec location, so run the command from project root as shown.
- `TimeSyncCompiler.iss` packages files from `dist/TimeSync/*`.
- Installer metadata (name/version/publisher) is defined at the top of `TimeSyncCompiler.iss`.
- Installer currently requires Administrator privileges (`PrivilegesRequired=admin`).
