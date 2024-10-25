# hook-transformers.py
# Скрипт для включения файлов и подмодулей из пакета transformers

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Сбор моделей и дополнительных файлов из transformers
datas = collect_data_files('transformers', includes=['**/*.py', '**/*.pyd'])
datas += collect_data_files('huggingface_hub', includes=['**/*.py', '**/*.pyd'])

# Сбор всех подмодулей из transformers
hiddenimports = collect_submodules('transformers')
hiddenimports += collect_submodules('transformers.models')

# Явное добавление проблемных моделей
problematic_models = [
    'transformers.models.albert',
    'transformers.models.marian',
    'transformers.models.bert',
    'transformers.models.roberta',
    'transformers.models.t5',
    'transformers.models.gpt2',
    'transformers.models.bart',
    'transformers.models.xlm_roberta',
]
hiddenimports += problematic_models

# Сбор утилит токенизации
hiddenimports += collect_submodules('transformers.tokenization_utils')

# Удаляем дубликаты из скрытых импортов, если таковые имеются
hiddenimports = list(set(hiddenimports))
