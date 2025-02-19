@echo off
cd /d "%~dp0"
setlocal enabledelayedexpansion

:: Path to the input file
set "INPUT_FILE=../Data/Input/chat.txt"

:: Check if the file exists
if not exist "%INPUT_FILE%" (
    echo Error: chat.txt not found.
    exit /b 1
)

:: Read and print each line from the file every 5 seconds
for /f "delims=" %%A in (%INPUT_FILE%) do (
    echo %%A
    timeout /t 5 >nul
)

endlocal