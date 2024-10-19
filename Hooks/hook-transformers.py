from PyInstaller.utils.hooks import copy_metadata, collect_data_files

# Include any metadata and files for the transformers library
datas = copy_metadata('transformers')

# Include the Marian model and other assets
datas += collect_data_files('transformers', include_py_files=True)