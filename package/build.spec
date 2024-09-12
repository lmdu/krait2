from PyInstaller.compat import is_win, is_darwin

block_cipher = None

if is_win:
    icon_file = ['../src/icons/logo.ico', '../src/icons/alogo.ico']
    datas = []

elif is_darwin:
    icon_file = '../src/icons/logo.icns'
    datas = [('../src/icons/alogo.icns', '.')]

else:
    icon_file = '../src/icons/logo.ico'
    datas = []


a = Analysis(['../src/main.py'],
             pathex=[],
             binaries=[],
             datas=datas,
             hiddenimports=[],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=['FixTk', 'tcl', 'tk', '_tkinter', 'tkinter', 'Tkinter', 'pymol.Qt', 'PyQt6'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
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
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None,
          icon=icon_file)
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas, 
               strip=False,
               upx=False,
               upx_exclude=[],
               name='Krait')

if is_darwin:
    app = BUNDLE(coll,
                 name='Krait.app',
                 icon=icon_file,
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
                    'UTExportedTypeDeclarations': [{
                        'UTTypeIdentifier': 'app.Krait.kpf',
                        'UTTypeTagSpecification': {
                            'public.filename-extension': ['kpf']
                        },
                        'UTTypeConformsTo': ['public.data'],
                        'UTTypeDescription': 'Krait Project File',
                        'UTTypeIconFile': 'alogo.icns'
                    }]
                })
