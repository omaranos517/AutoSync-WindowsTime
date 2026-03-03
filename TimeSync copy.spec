# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['TimeSync.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
)

pyz = PYZ(a.pure)

# النسخة ذات الطرفية (CLI)
exe_console = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='timesync-cli',
    icon='icon.ico',
    console=True,
)

# النسخة بدون طرفية (Background)
exe_windowed = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='timesync-gui',
    icon='icon.ico',
    console=False,
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