# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src\\lawchecker\\main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('.\\icon\\icon.ico', '.'),
        ('.\\.env', '.'),
        ('.\\ui_bundle\\index.html', 'ui\\'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['.\\additional_runtime_hooks_lawchecker\\hook-lawchecker.py'],
    excludes=['lxml.objectify', 'lxml.sax', 'lxml.isoschematron', 'lxml.cssselect'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='LawChecker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon\\icon.ico'],
)
