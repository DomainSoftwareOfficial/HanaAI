import subprocess
import sys
from start import StartWindow  # Import the StartWindow class
import os

def edit_env_file():
    env_file = resource_path("../.env")
    
    # Open the .env file in the default editor
    try:
        # For Windows (uses notepad)
        subprocess.run(["notepad", env_file])
    except FileNotFoundError:
        try:
            # For Linux/macOS (uses nano)
            subprocess.run(["nano", env_file])
        except FileNotFoundError:
            print("Please install a text editor (notepad or nano) to edit the .env file.")

def resource_path(relative_path):
    """ Get the absolute path to the resource, works for dev and for PyInstaller """
    try:
        # If using PyInstaller, sys._MEIPASS will be set to the temporary folder where files are extracted
        base_path = sys._MEIPASS
    except AttributeError:
        # Otherwise, use the current directory
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

if __name__ == "__main__":
    # Open the .env file for editing
    edit_env_file()

    # Create and run the start window after editing
    start_window = StartWindow()
    start_window.mainloop()