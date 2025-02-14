@echo off
chcp 65001

:: Set PYTHONPATH to project root so Python finds the App module
set PYTHONPATH=%CD%

:: Проверка установки Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python не установлен. Пожалуйста, установите Python и попробуйте снова.
    pause
    exit
)

:: Проверка наличия необходимых модулей
python -c "import gtts, pydub" 2>nul
if %errorlevel% neq 0 (
    echo Устанавливаем недостающие модули...
    pip install gtts pydub
)

:: Ввод текста от пользователя
set /p "USER_TEXT=Введите текст для преобразования в речь: "

:: Создание временного Python-скрипта
echo import sys, io, os, shutil > tts_processing.py
echo from gtts import gTTS >> tts_processing.py
echo from pydub import AudioSegment, effects >> tts_processing.py
echo sys.path.insert(0, '../App') >> tts_processing.py
echo from rvc import mainrvc >> tts_processing.py
echo from audio import normalize >> tts_processing.py
echo. >> tts_processing.py
echo SPEED_UP_FACTOR = 1.2 >> tts_processing.py
echo GAIN_DB = 5 >> tts_processing.py
echo OUTPUT_FILE_PATH = "./output.wav" >> tts_processing.py
echo RVC_OUTPUT_PATH = "../Assets/Audio/output.wav" >> tts_processing.py
echo. >> tts_processing.py
echo # Convert text to speech >> tts_processing.py
echo tts = gTTS(text="%USER_TEXT%", lang='en') >> tts_processing.py
echo with io.BytesIO() as temp_audio: >> tts_processing.py
echo     tts.write_to_fp(temp_audio) >> tts_processing.py
echo     temp_audio.seek(0) >> tts_processing.py
echo     audio = AudioSegment.from_file(temp_audio, format='mp3') >> tts_processing.py
echo. >> tts_processing.py
echo     # Apply speed-up and gain >> tts_processing.py
echo     processed_audio = audio.speedup(playback_speed=SPEED_UP_FACTOR) + GAIN_DB >> tts_processing.py
echo. >> tts_processing.py
echo     # Save processed audio to output.wav >> tts_processing.py
echo     processed_audio.export(OUTPUT_FILE_PATH, format="wav") >> tts_processing.py
echo. >> tts_processing.py
echo # Apply mainrvc processing (moves file to RVC_OUTPUT_PATH) >> tts_processing.py
echo mainrvc(OUTPUT_FILE_PATH, RVC_OUTPUT_PATH) >> tts_processing.py
echo. >> tts_processing.py
echo # Move output file back to current directory >> tts_processing.py
echo if os.path.exists(RVC_OUTPUT_PATH): >> tts_processing.py
echo     shutil.move(RVC_OUTPUT_PATH, OUTPUT_FILE_PATH) >> tts_processing.py
echo else: >> tts_processing.py
echo     print("Error: mainrvc did not generate output.") >> tts_processing.py
echo. >> tts_processing.py
echo # Run normalization on final output.wav >> tts_processing.py
echo normalize(OUTPUT_FILE_PATH) >> tts_processing.py

:: Запуск Python-скрипта
python tts_processing.py

:: Очистка временного файла
del tts_processing.py

pause