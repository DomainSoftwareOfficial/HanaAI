@echo off
chcp 65001

:: Проверка установки Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python не установлен. Пожалуйста, установите Python и попробуйте снова.
    pause
    exit
)

:: Проверка наличия gtts и pydub
python -c "import gtts, pydub, random" 2>nul
if %errorlevel% neq 0 (
    echo Устанавливаем недостающие модули...
    pip install gtts pydub
)

:: Меню выбора языка
echo Выберите язык:
echo 1 - Английский (en)
echo 2 - Русский (ru)
echo 3 - Испанский (es)
echo 4 - Нидерландский (nl)
echo 5 - Норвежский (no)
echo 6 - Португальский (pt)
echo 7 - Украинский (uk)
echo 8 - Итальянский (it)
echo 9 - Финский (fi)
echo 10 - Румынский (ro)
echo 11 - Шведский (sv)
echo 12 - Словацкий (sk)
echo 13 - Чешский (cs)
echo 14 - Болгарский (bg)
echo 15 - Польский (pl)
echo 16 - Сербский (sr)
echo 17 - Турецкий (tr)
echo 18 - Датский (da)
echo 19 - Боснийский (bs)
echo 20 - Эстонский (et)
echo 21 - Хорватский (hr)
echo 22 - Французский (fr)
set /p "CHOICE=Введите номер языка: "

:: Установка кода языка
if "%CHOICE%"=="1" set LANG=en
if "%CHOICE%"=="2" set LANG=ru
if "%CHOICE%"=="3" set LANG=es
if "%CHOICE%"=="4" set LANG=nl
if "%CHOICE%"=="5" set LANG=no
if "%CHOICE%"=="6" set LANG=pt
if "%CHOICE%"=="7" set LANG=uk
if "%CHOICE%"=="8" set LANG=it
if "%CHOICE%"=="9" set LANG=fi
if "%CHOICE%"=="10" set LANG=ro
if "%CHOICE%"=="11" set LANG=sv
if "%CHOICE%"=="12" set LANG=sk
if "%CHOICE%"=="13" set LANG=cs
if "%CHOICE%"=="14" set LANG=bg
if "%CHOICE%"=="15" set LANG=pl
if "%CHOICE%"=="16" set LANG=sr
if "%CHOICE%"=="17" set LANG=tr
if "%CHOICE%"=="18" set LANG=da
if "%CHOICE%"=="19" set LANG=bs
if "%CHOICE%"=="20" set LANG=et
if "%CHOICE%"=="21" set LANG=hr
if "%CHOICE%"=="22" set LANG=fr

:: Проверка выбора
if not defined LANG (
    echo Ошибка: неверный выбор.
    pause
    exit
)

:: Ввод текста от пользователя
set /p "TEXT=Введите текст для преобразования в речь: "

:: Создание временного Python-скрипта
echo from gtts import gTTS > temporary.py
echo from pydub import AudioSegment >> temporary.py
echo import random >> temporary.py
echo tts = gTTS(text="%TEXT%", lang="%LANG%") >> temporary.py
echo tts.save("output.mp3") >> temporary.py
echo audio = AudioSegment.from_file("output.mp3") >> temporary.py
echo speed = random.uniform(1.1, 1.3) >> temporary.py
echo gainDB = (speed - 1.0) * -5 >> temporary.py
echo audio = audio._spawn(audio.raw_data, overrides={"frame_rate": int(audio.frame_rate * speed)}) >> temporary.py
echo audio = audio.set_frame_rate(44100) >> temporary.py
echo audio = audio + gainDB >> temporary.py
echo audio.export("output.mp3", format="mp3") >> temporary.py

:: Запуск Python-скрипта
python temporary.py

:: Очистка временных файлов
del temporary.py

:: Проверка и воспроизведение файла
if exist output.mp3 (
    start output.mp3
    echo Аудиофайл сохранен как output.mp3
) else (
    echo Ошибка: файл не был создан.
)

pause