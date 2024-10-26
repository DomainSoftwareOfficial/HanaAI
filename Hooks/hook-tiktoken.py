# hook-tiktoken.py
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Collect all submodules in `tiktoken` and `tiktoken_ext`
hiddenimports = collect_submodules('tiktoken') + collect_submodules('tiktoken_ext')

# Collect any additional data files that may be required
datas = collect_data_files('tiktoken')
