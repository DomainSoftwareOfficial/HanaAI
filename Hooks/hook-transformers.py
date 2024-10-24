# hook-transformers.py
# Скрипт для включения файлов и подмодулей из пакета transformers

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Сбор моделей и дополнительных файлов из transformers
datas = collect_data_files('transformers')
datas += collect_data_files('huggingface_hub')

# Сбор всех подмодулей transformers
hiddenimports = collect_submodules('transformers')
hiddenimports += collect_submodules('transformers.models')