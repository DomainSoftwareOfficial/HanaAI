# hook-torch.py
# Общий скрипт для обработки подмодулей и файлов для torch, torchvision, transformers, tqdm

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

def collect_package_data(package_name):
    """
    Сбор подмодулей и данных для заданного пакета.
    """
    hiddenimports = collect_submodules(package_name)
    datas = collect_data_files(package_name, include_py_files=True)
    return hiddenimports, datas

# Сбор данных и подмодулей для PyTorch
hiddenimports, datas = collect_package_data('torch')

# Явное добавление модулей TorchScript
hiddenimports += ['torch.jit', 'torch.jit._script', 'torch.jit._trace']
hiddenimports += ['torch.nn.functional', 'torch.optim']

# Если используется torchvision
hiddenimports += collect_submodules('torchvision')
datas += collect_data_files('torchvision')

# Если используется torchaudio
hiddenimports += collect_submodules('torchaudio')
datas += collect_data_files('torchaudio')

# Если необходимо, сбор NumPy, Protobuf, и TensorBoard
hiddenimports += collect_submodules('numpy')
hiddenimports += collect_submodules('protobuf')

# Включение поддержки CUDA, если применяется
hiddenimports += collect_submodules('torch.cuda')
datas += collect_data_files('torch.cuda')

# Сбор файлов TensorBoard, если требуется
hiddenimports += collect_submodules('tensorboard')
datas += collect_data_files('tensorboard')
