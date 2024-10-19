# hook-torch.py

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect all the submodules of torch
hiddenimports = collect_submodules('torch')

# Collect the data files needed for PyTorch
datas = collect_data_files('torch')

# Collect additional files for torchvision if used
if 'torchvision' in hiddenimports:
    datas += collect_data_files('torchvision')

# Collect any additional files from other related packages
if 'torchaudio' in hiddenimports:
    datas += collect_data_files('torchaudio')
