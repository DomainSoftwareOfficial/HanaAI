# setup.py
# Скрипт сборки приложения с использованием PyInstaller

import os
import sys
import subprocess

# Определение директорий для сборки
CURRENT_DIR = os.getcwd()
DIST_PATH = os.path.join(CURRENT_DIR, 'Distribution')
BUILD_PATH = os.path.join(CURRENT_DIR, 'Build')
SPEC_PATH = os.path.join(CURRENT_DIR, 'Utilities', 'Miscellaneous')
APP_PATH = os.path.join(CURRENT_DIR, 'App')

def build():
    """
    Функция для выполнения сборки приложения с использованием PyInstaller.
    """
    
    pyinstaller_command = [
        'pyInstaller',
        '--onefile',
        '--name', 'Stream',
        '--noconfirm',
        '--distpath', DIST_PATH,
        '--workpath', BUILD_PATH,
        '--specpath', SPEC_PATH,
        '--paths', APP_PATH,

        # Копирование метаданных для зависимостей
        '--copy-metadata', 'torch',
        '--copy-metadata', 'transformers',
        '--copy-metadata', 'tqdm',
        '--copy-metadata', 'huggingface-hub',
        '--copy-metadata', 'safetensors',
        '--copy-metadata', 'regex',
        '--copy-metadata', 'gtts',
        '--copy-metadata', 'numpy',
        '--copy-metadata', 'librosa',
        '--copy-metadata', 'soundfile',
        '--copy-metadata', 'openai-whisper',
        '--copy-metadata', 'PyAudio',
        '--copy-metadata', 'langdetect',
        '--copy-metadata', 'requests',
        '--copy-metadata', 'PyYAML',
        '--copy-metadata', 'tensorboardX',
        '--copy-metadata', 'faiss-cpu',
        '--copy-metadata', 'SentencePiece',
        '--copy-metadata', 'sacremoses',
        '--copy-metadata', 'tensorboard',
        '--copy-metadata', 'Pillow',
        '--copy-metadata', 'wavio',
        '--copy-metadata', 'filelock',
        '--copy-metadata', 'packaging',
        
        # Дополнительные хуки
        '--additional-hooks-dir', os.path.join(CURRENT_DIR, 'Hooks'),

        # Главный файл приложения
        os.path.join(APP_PATH, 'main.py')
    ]

    try:
        # Запуск PyInstaller для сборки
        subprocess.run(pyinstaller_command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Ошибка сборки: {e}")
        sys.exit(1)

if __name__ == '__main__':
    build()