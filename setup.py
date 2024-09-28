import os
import sys
import subprocess

def build():
    # Define paths for output
    current_dir = os.getcwd()  # Get current working directory
    dist_path = os.path.join(current_dir, 'Distribution')  # Specify your distribution directory
    build_path = os.path.join(current_dir, 'Build')  # Specify your build directory
    spec_path = '.\\Utilities\\Miscellaneous'

    # Define the PyInstaller command
    pyinstaller_command = [
        'pyinstaller',
        '--onefile',
        '--windowed' if sys.platform == "win32" else '',
        '--name', 'stream',
        '--distpath', dist_path,
        '--workpath', build_path,
        '--specpath', spec_path,  # Set the location for the .spec file
        'App/main.py'  # Path to your main Python script
    ]

    # Remove any empty strings from the command list
    pyinstaller_command = [arg for arg in pyinstaller_command if arg]

    # Run the PyInstaller command
    subprocess.run(pyinstaller_command)

if __name__ == '__main__':
    build()
