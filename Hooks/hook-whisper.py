# hook-whisper.py
# Скрипт для включения нормализаторов и ассетов из пакета whisper

from PyInstaller.utils.hooks import collect_data_files

# Сбор нормализаторов и ассетов из whisper
datas = collect_data_files('whisper', includes=['**/*.npz', '**/*.json', '**/*.txt', '**/*.tiktoken'])