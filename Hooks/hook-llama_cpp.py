from PyInstaller.utils.hooks import collect_submodules, collect_dynamic_libs
import os

# Collect all submodules of `llama_cpp`
hiddenimports = collect_submodules('llama_cpp')

# Collect all dynamic libraries (.dll, .so, etc.) in `llama_cpp/lib`
binaries = collect_dynamic_libs('llama_cpp', '.dll')

# Optional: check for existence and alert user if not found
lib_path = os.path.join(os.path.dirname(__file__), "llama_cpp", "lib")
if not os.path.exists(lib_path):
    print(f"Warning: The llama_cpp library path '{lib_path}' does not exist. Ensure all DLLs are correctly placed.")
