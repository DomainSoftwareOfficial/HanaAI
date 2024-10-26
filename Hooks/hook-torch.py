from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules

# Collect all submodules from torch
hiddenimports = collect_submodules('torch')

# Collect all dynamic libraries from torch
binaries = collect_dynamic_libs('torch')

# Collect all data files for the torch library (including .py files)
datas = collect_data_files('torch', include_py_files=True)

# Optionally collect specific modules you know will be used
hiddenimports += [
    'torch.jit',
    'torch.jit.frontend',
    'torch.jit._trace',
    'torch.jit._script',
    'torch.jit._builtins',
    'torch.jit.utils',
    'torch.jit._fuser',
    'torch.jit.quantized',
    'torch.jit._traceback',
    'torch.jit._serialization',
]
