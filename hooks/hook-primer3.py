from PyInstaller.utils.hooks import collect_data_files
datas = collect_data_files('primer3', subdir='src/libprimer3/primer3_config')