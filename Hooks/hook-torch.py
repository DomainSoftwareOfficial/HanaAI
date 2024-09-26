from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Collect all submodules from torch, torch.nn, torch.jit, etc.
hiddenimports = collect_submodules('torch')

# Optionally, collect data files if needed (e.g., .so, .dll files)
datas = collect_data_files('torch', include_py_files=True)