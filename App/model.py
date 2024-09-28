from llama_cpp import Llama
import os
import sys

_loaded_model = None  # Module-level variable to store the loaded model

def load_model(model_path, n_ctx=32768, n_threads=8):
    """
    Load the LLaMA model using llama.cpp Python bindings.

    Parameters:
        model_path (str): Path to the LLaMA model weights file (e.g., ggml model).
        n_ctx (int): Context size to use for the model (default is 512).
        n_threads (int): Number of threads for inference (default is 8).

    Returns:
        llama_model (Llama): Loaded LLaMA model object.
    """
    try:
        # Load the LLaMA model
        llama_model = Llama(model_path=model_path, n_ctx=n_ctx, n_threads=n_threads)
        print(f"Model loaded successfully from {model_path}")
        return llama_model
    except Exception as e:
        print(f"Error loading model: {e}")
        return None

def get_loaded_model():
    """Returns the loaded model, if it exists."""
    return _loaded_model

def resource_path(relative_path):
    """ Get the absolute path to the resource, works for dev and for PyInstaller """
    try:
        # If using PyInstaller, sys._MEIPASS will be set to the temporary folder where files are extracted
        base_path = sys._MEIPASS
    except AttributeError:
        # Otherwise, use the current directory
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
