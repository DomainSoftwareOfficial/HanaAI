@echo off
cd /d "%~dp0"
setlocal enabledelayedexpansion

:: Load the .env file
for /f "usebackq delims=" %%A in (../.env) do (
    set "LINE=%%A"
    for /f "tokens=1,2 delims==" %%B in ("!LINE!") do (
        if "%%B"=="YOUTUBE_URL" set "YOUTUBE_URL=%%C"
    )
)

:: Check if YOUTUBE_URL is set
if not defined YOUTUBE_URL (
    echo Error: YOUTUBE_URL not found in .env
    exit /b 1
)

:: Create a temporary Python script
set "TEMP_PY=%TEMP%\temp_youtube_chat.py"
(
echo import os
echo try:
echo.    from pytchat import LiveChat
echo except ImportError:
echo.    import subprocess
echo.    subprocess.run(["python", "-m", "pip", "install", "pytchat"], check=True)
echo.    from pytchat import LiveChat
echo.
echo url = os.getenv("Video-Url")
echo if not url:
echo.    print("Error: Video-Url not found.")
echo.    exit(1)
echo.
echo chat = LiveChat(url)
echo while chat.is_alive():
echo.    for c in chat.get().items:
echo.        print(f"{c.author.name}: {c.message}")
) > "%TEMP_PY%"

:: Activate virtual environment
call ../Environment/Scripts/activate.bat

:: Run the Python script
python "%TEMP_PY%"

:: Clean up
del "%TEMP_PY%"
endlocal
