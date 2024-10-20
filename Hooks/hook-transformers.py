# ./Hooks/hook-transformers.py

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect all the submodules of transformers
hiddenimports = collect_submodules('transformers')

# Collect all the data files needed for transformers, including config and model files
datas = collect_data_files('transformers')

# Collect data for specific submodules (if necessary, depending on your model)
datas += collect_data_files('transformers.models.marian')