# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.compat import is_win, is_darwin

if is_win:
    icons = ['../src/icons/logo.ico', '../src/icons/alogo.ico']
    datas = []

elif is_darwin:
    icons = ['../src/icons/logo.icns']
    datas = [('../src/icons/alogo.icns', '.')]

else:
    icons = ['../src/icons/logo.ico']
    datas = []

a = Analysis(
    ['../src/main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=['hooks'],
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
    name='Krait',
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
    icon=icons,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Krait',
)

if is_darwin:
    app = BUNDLE(
        coll,
        name = 'Krait.app',
        icon = icons,
        bundle_identifier=None,
        info_plist={
            'CFBundleDocumentTypes': [
                {
                    'CFBundleTypeName': 'Krait Project File',
                    'CFBundleTypeIconFile': 'alogo.icns',
                    'CFBundleTypeRole': 'Editor',
                    'LSHandlerRank': 'Owner',
                    'LSItemContentTypes': ['app.Krait.kpf']
                }
            ],
            'UTExportedTypeDeclarations': [
                {
                    'UTTypeIdentifier': 'app.Krait.kpf',
                    'UTTypeTagSpecification': {
                        'public.filename-extension': ['kpf']
                    },
                    'UTTypeConformsTo': ['public.data'],
                    'UTTypeDescription': 'Krait Project File',
                    'UTTypeIconFile': 'alogo.icns'
            }]
        }
    )
