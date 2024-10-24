# hook-emoji.py
# Скрипт для включения JSON-файлов emoji в сборку

from PyInstaller.utils.hooks import collect_data_files

# Сбор всех JSON-файлов из директории unicode_codes в пакете emoji
datas = collect_data_files('emoji', includes=['unicode_codes/*.json'])
