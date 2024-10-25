# hook-torch.py
# Общий скрипт для обработки подмодулей и файлов для torch, torchvision, torchaudio

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

def collect_package_data(package_name):
    """
    Сбор подмодулей и .py файлов для заданного пакета.
    """
    hiddenimports = collect_submodules(package_name)
    # Collect .py and .pyd files for the package
    datas = collect_data_files(package_name, includes=['**/*.py', '**/*.pyd'])
    return hiddenimports, datas

# Сбор данных, подмодулей и .py файлов для PyTorch
hiddenimports, datas = collect_package_data('torch')

# Проверка наличия torchvision
try:
    import torchvision  # Проверяем, установлен ли torchvision
    torchvision_hiddenimports, torchvision_datas = collect_package_data('torchvision')
    hiddenimports += torchvision_hiddenimports
    datas += torchvision_datas
except ImportError:
    pass  # Если torchvision недоступен, игнорируем это

# Проверка наличия torchaudio
try:
    import torchaudio  # Проверяем, установлен ли torchaudio
    torchaudio_hiddenimports, torchaudio_datas = collect_package_data('torchaudio')
    hiddenimports += torchaudio_hiddenimports
    datas += torchaudio_datas
except ImportError:
    pass  # Если torchaudio недоступен, игнорируем это

# Сбор данных для NumPy, Protobuf и TensorBoard
numpy_hiddenimports, numpy_datas = collect_package_data('numpy')
hiddenimports += numpy_hiddenimports
datas += numpy_datas

protobuf_hiddenimports, protobuf_datas = collect_package_data('protobuf')
hiddenimports += protobuf_hiddenimports
datas += protobuf_datas

# Включение поддержки CUDA, если применяется
cuda_hiddenimports, cuda_datas = collect_package_data('torch.cuda')
hiddenimports += cuda_hiddenimports
datas += cuda_datas

# Сбор файлов TensorBoard, если требуется
tensorboard_hiddenimports, tensorboard_datas = collect_package_data('tensorboard')
hiddenimports += tensorboard_hiddenimports
datas += tensorboard_datas

# Удаляем дубликаты из скрытых импортов, если таковые имеются
hiddenimports = list(set(hiddenimports))
