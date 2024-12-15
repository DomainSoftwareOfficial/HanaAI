@echo off
:: Ensure the script exits if any command fails
setlocal enabledelayedexpansion

:: Change directory to where the Python script is located
cd ..\App

:: Run the Python script
python chat.py

:: End script
endlocal