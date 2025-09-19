# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src/ExpenditureControl.py'],
    pathex=[],
    binaries=[],
    datas=[('assets/samples/test_01.PDF', 'assets/samples/')],
    hiddenimports=['sklearn.neighbors._typedefs', 'sklearn.utils._weight_vector', 'pandas._libs.tslibs.timedeltas', 'sklearn.neighbors._quad_tree', 'sklearn.tree._utils', 'matplotlib.backends.backend_tkagg', 'tkinter', 'PIL._tkinter_finder'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ExpenditureControl',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets/icons/icon.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ExpenditureControl',
)
app = BUNDLE(
    coll,
    name='ExpenditureControl.app',
    icon='assets/icons/icon.icns',
    bundle_identifier=None,
)
