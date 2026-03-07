# Build Guide (Current Packaging Files)

This document explains how to build TimeSync using the existing packaging files in this repository:

- `packaging/TimeSync.spec` (PyInstaller)
- `packaging/TimeSyncCompiler.iss` (Inno Setup installer)

## 1) Prerequisites

- Windows 10/11
- Python 3.10+ (same architecture you target, usually x64)
- Inno Setup 6 (for `.iss` installer compilation)
- Optional: `upx.exe` in project root

## 2) Install Python dependencies

From the project root:

```powershell
python -m pip install --upgrade pip
python -m pip install -r packaging/requirements.txt
```

## 3) Build executables with PyInstaller

From the project root, run:

```powershell
python -m PyInstaller packaging/TimeSync.spec --clean
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

You can compile it from Inno Setup GUI, or via command line (if `ISCC.exe` is on PATH):

```powershell
ISCC packaging/TimeSyncCompiler.iss
```

Expected installer output:

- `output/TimeSync_Setup.exe`

## 5) Notes about current build files

- `TimeSync.spec` resolves paths relative to the spec location, so run the command from project root as shown.
- `TimeSyncCompiler.iss` packages files from `dist/TimeSync/*`.
- Installer metadata (name/version/publisher) is defined at the top of `TimeSyncCompiler.iss`.
- Installer currently requires Administrator privileges (`PrivilegesRequired=admin`).

