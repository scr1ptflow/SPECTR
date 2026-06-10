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
