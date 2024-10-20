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
MARIAN_MODEL_PACKAGE = os.path.join(VENV_PATH, 'Lib', 'site-packages', 'transformers', 'models', 'marian')
TRANSFORMERS_PACKAGE = os.path.join(VENV_PATH, 'Lib', 'site-packages', 'transformers')

def build():
    
    pyinstaller_command = [
        PYTHON_EXECUTABLE,
        '-m', 'PyInstaller',
        '--onefile',
        '--name', 'stream',
        '--distpath', DIST_PATH,
        '--workpath', BUILD_PATH,
        '--specpath', SPEC_PATH,
        '--paths', APP_PATH,
        
        # Add required data and modules
        '--add-data', f'{EMOJI_PACKAGE}/unicode_codes/*.json;emoji/unicode_codes',
        '--add-data', f'{TORCH_PACKAGE};torch',  # Simplify the pattern
        '--add-data', f'{MARIAN_MODEL_PACKAGE};transformers/models/marian',
        '--add-data', f'{TRANSFORMERS_PACKAGE};transformers',
        '--add-data', f'{WHISPER_PACKAGE}/normalizers/*.json;whisper/normalizers',
        '--add-data', f'{WHISPER_PACKAGE}/assets/*.npz;whisper/assets',
        '--add-data', f'{WHISPER_PACKAGE}/assets/*.tiktoken;whisper/assets',
        
        # Handle hidden imports
        '--hidden-import', 'transformers.models.marian.modeling_marian',
        '--hidden-import', 'transformers.models.marian',
        '--hidden-import', 'transformers.utils',
        
        # Exclude the problematic overloads
        '--exclude-module', 'torch.jit._overload',
        '--exclude-module', 'torch.functional',   # Add this to exclude problematic functions
        
        '--additional-hooks-dir', os.path.join(CURRENT_DIR, 'Hooks'),
        os.path.join(APP_PATH, 'main.py')
    ]

    try:
        # Run PyInstaller
        subprocess.run(pyinstaller_command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Build failed with error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    build()