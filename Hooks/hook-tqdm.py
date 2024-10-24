# hook-tqdm.py
# Скрипт для включения всех файлов данных для tqdm

from PyInstaller.utils.hooks import collect_data_files

# Сбор всех файлов данных для tqdm
datas = collect_data_files('tqdm')
