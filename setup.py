import os
import sys
import subprocess

CURRENT_DIR = os.getcwd()
VENV_PATH = os.path.join(CURRENT_DIR, 'Environment')
DIST_PATH = os.path.join(CURRENT_DIR, 'Distribution')
BUILD_PATH = os.path.join(CURRENT_DIR, 'Build')
SPEC_PATH = os.path.join(CURRENT_DIR, 'Utilities', 'Miscellaneous')
APP_PATH = os.path.join(CURRENT_DIR, 'App')
PYTHON_EXECUTABLE = os.path.join(VENV_PATH, 'Scripts', 'python.exe')

EMOJI_PACKAGE = os.path.join(VENV_PATH, 'Lib', 'site-packages', 'emoji')
WHISPER_PACKAGE = os.path.join(VENV_PATH, 'Lib', 'site-packages', 'whisper')
TORCH_PACKAGE = os.path.join(VENV_PATH, 'Lib', 'site-packages', 'torch')

def build():
    # Prepare PyInstaller command
    pyinstaller_command = [
        PYTHON_EXECUTABLE,
        '-m', 'PyInstaller',
        '--onefile',
        '--name', 'stream',
        '--distpath', DIST_PATH,
        '--workpath', BUILD_PATH,
        '--specpath', SPEC_PATH,
        '--paths', APP_PATH,
        '--add-data', f'{EMOJI_PACKAGE}/unicode_codes/*.json;emoji/unicode_codes',
        '--add-data', f'{TORCH_PACKAGE}/**/*.py;torch',
        '--add-data', f'{WHISPER_PACKAGE}/normalizers/*.json;whisper/normalizers',
        '--add-data', f'{WHISPER_PACKAGE}/assets/*.npz;whisper/assets',
        '--add-data', f'{WHISPER_PACKAGE}/assets/*.tiktoken;whisper/assets',
        '--hidden-import', 'transformers.models.marian.modeling_marian',
        '--exclude-module', 'torch.jit._overload',
        '--additional-hooks-dir', os.path.join(CURRENT_DIR, 'Hooks'),
        os.path.join(APP_PATH, 'main.py')
    ]

    '''
    # Platform-specific options (e.g., Windows)
    if sys.platform == "win32":
        pyinstaller_command.append('--windowed')
    '''
    try:
        # Run PyInstaller
        subprocess.run(pyinstaller_command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Build failed with error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    build()