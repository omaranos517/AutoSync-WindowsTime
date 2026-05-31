# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

block_cipher = None
spec_dir = Path(globals().get("SPECPATH", Path.cwd()))
project_root = spec_dir.parent

a = Analysis(
    [str(project_root / 'main.py')],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        (str(project_root / 'assets' / 'icon.ico'), '.'),
        (str(project_root / 'assets' / 'timesync.bat'), '.'),
        (str(project_root / 'assets' / 'timesync-completion.ps1'), '.'),
    ],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
)

pyz = PYZ(a.pure)

# Console build (CLI)
exe_console = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='timesync-cli',
    icon=str(project_root / 'assets' / 'icon.ico'),
    version=str(project_root / 'packaging' / 'version_info.txt'),
    console=True,
    contents_directory='.',
)

# Windowed build (background/GUI)
exe_windowed = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='timesync-gui',
    icon=str(project_root / 'assets' / 'icon.ico'),
    version=str(project_root / 'packaging' / 'version_info.txt'),
    console=False,
    contents_directory='.',
)

coll = COLLECT(
    exe_console,
    exe_windowed,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='TimeSync'
)
