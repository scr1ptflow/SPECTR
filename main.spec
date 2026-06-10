# -*- mode: python ; coding: utf-8 -*-

import os

a = Analysis(
    ['main.pyw'],
    pathex=['.'],
    binaries=[],
    datas=[],
    hiddenimports=[
        'ctypes',
        'ctypes.wintypes',
        'tkinter',
        'tkinter.ttk',
        'PIL',
        'PIL.Image',
        'plugins.exobiology.predictor',
        'plugins.jump_tracker.route_view',
        'plugins.jump_tracker.follow_route',
        'plugins.jump_tracker.ed_api',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

a.datas += Tree('plugins', prefix='plugins')
a.datas += Tree('assets', prefix='assets')
a.datas += Tree('data', prefix='data')

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    name='SPECTR',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# --- Post-build: create deploy zip ---
import zipfile as zfmod

dist_dir = os.path.dirname(exe.name)
if not os.path.isdir(dist_dir):
    dist_dir = 'dist'

exe_path = os.path.join(dist_dir, 'SPECTR.exe')
zip_path = 'SPECTR.zip'

if os.path.isfile(exe_path):
    with zfmod.ZipFile(zip_path, 'w', zfmod.ZIP_DEFLATED) as zf:
        zf.write(exe_path, 'SPECTR.exe')
    print(f"Created {zip_path}")
