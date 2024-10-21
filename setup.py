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
TQDM_PACKAGE = os.path.join(VENV_PATH, 'Lib', 'site-packages', 'tqdm')

def build():
    
    pyinstaller_command = [
        PYTHON_EXECUTABLE,
        '-m', 'PyInstaller',
        '--onefile',
        '--name', 'stream',
        '--noconfirm',
        '--distpath', DIST_PATH,
        '--workpath', BUILD_PATH,
        '--specpath', SPEC_PATH,
        '--paths', APP_PATH,
        
        # Add required data and modules
        '--add-data', f'{TQDM_PACKAGE};tqdm',
        '--add-data', f'{EMOJI_PACKAGE}/unicode_codes/*.json;emoji/unicode_codes',
        '--add-data', f'{TORCH_PACKAGE};torch',  # Simplify the pattern
        '--add-data', f'{MARIAN_MODEL_PACKAGE};transformers/models/marian',
        '--add-data', f'{TRANSFORMERS_PACKAGE};transformers',
        '--add-data', f'{WHISPER_PACKAGE}/normalizers/*.json;whisper/normalizers',
        '--add-data', f'{WHISPER_PACKAGE}/assets/*.npz;whisper/assets',
        '--add-data', f'{WHISPER_PACKAGE}/assets/*.tiktoken;whisper/assets',

        # Copy metadata for dependencies
        '--copy-metadata', 'torch',
        '--copy-metadata', 'tqdm',
        '--copy-metadata', 'regex',
        '--copy-metadata', 'sacremoses',
        '--copy-metadata', 'requests',
        '--copy-metadata', 'packaging',
        '--copy-metadata', 'filelock',
        '--copy-metadata', 'numpy',
        '--copy-metadata', 'tokenizers',
        '--copy-metadata', 'importlib_metadata',
        '--copy-metadata', 'huggingface-hub',

        # Handle hidden imports
        '--hidden-import', 'pytorch',
        '--hidden-import', 'sklearn.utils._cython_blas',
        '--hidden-import', 'sklearn.neighbors.typedefs',
        '--hidden-import', 'sklearn.neighbors.quad_tree',
        '--hidden-import', 'sklearn.tree',
        '--hidden-import', 'sklearn.tree._utils',
        '--hidden-import', 'transformers.models.marian.modeling_marian',
        '--hidden-import', 'transformers.models.marian',
        '--hidden-import', 'transformers.utils',

        # Exclude the problematic overloads
        '--exclude-module', 'torch.jit._overload',
        '--exclude-module', 'torch.functional',

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