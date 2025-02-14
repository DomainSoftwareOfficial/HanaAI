@echo off
chcp 65001

:: Проверка установки Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python не установлен. Пожалуйста, установите Python и попробуйте снова.
    pause
    exit
)

:: Проверка наличия необходимых модулей
python -c "import pyttsx3, pydub, numpy, scipy" 2>nul
if %errorlevel% neq 0 (
    echo Устанавливаем недостающие модули...
    pip install pyttsx3 pydub numpy scipy
)

:: Ввод текста от пользователя
set /p "TEXT=Введите текст для преобразования в речь: "

:: Создание временного Python-скрипта
echo import pyttsx3 > temporary.py
echo from pydub import AudioSegment, effects >> temporary.py  # Добавлено для исправления ошибки с effects >> temporary.py
echo from scipy.signal import lfilter >> temporary.py
echo import io >> temporary.py
echo import numpy as np >> temporary.py
echo import os >> temporary.py  # Добавлено для исправления ошибки с os >> temporary.py
echo. >> temporary.py
echo PITCH_SHIFT = 0.9  # Пониженная тональность, но не так сильно >> temporary.py
echo. >> temporary.py
echo def formant_shift(audio, shift_factor=PITCH_SHIFT): >> temporary.py
echo     return audio._spawn(audio.raw_data, overrides={"frame_rate": int(audio.frame_rate * shift_factor)}).set_frame_rate(audio.frame_rate) >> temporary.py
echo. >> temporary.py
echo def chorus_effect(audio, delay_ms=20, depth=0.5): >> temporary.py
echo     samples = np.array(audio.get_array_of_samples(), dtype=np.float32) >> temporary.py
echo     delayed_samples = np.zeros_like(samples) >> temporary.py
echo     delay_samples = int(audio.frame_rate * (delay_ms / 1000)) >> temporary.py
echo     delayed_samples[delay_samples:] = samples[:-delay_samples] * depth >> temporary.py
echo     final_samples = np.clip(samples + delayed_samples, -32768, 32767).astype(np.int16) >> temporary.py
echo     return AudioSegment(final_samples.tobytes(), frame_rate=audio.frame_rate, sample_width=audio.sample_width, channels=audio.channels) >> temporary.py
echo. >> temporary.py
echo def mask_voice(audio_path): >> temporary.py
echo     if not os.path.isfile(audio_path): >> temporary.py
echo         raise ValueError("Файл не найден.") >> temporary.py
echo     audio = AudioSegment.from_file(audio_path, format="mp3") >> temporary.py
echo     audio = effects.normalize(audio) >> temporary.py
echo     audio = formant_shift(audio, shift_factor=PITCH_SHIFT) >> temporary.py
echo     audio = chorus_effect(audio) >> temporary.py
echo     low_pass_audio = audio.low_pass_filter(3000) >> temporary.py
echo     high_pass_audio = low_pass_audio.high_pass_filter(500) >> temporary.py
echo     final_audio = effects.normalize(high_pass_audio) >> temporary.py
echo     final_audio.export(audio_path, format="mp3") >> temporary.py
echo. >> temporary.py

:: Использование pyttsx3 для генерации речи с мужским голосом
echo engine = pyttsx3.init() >> temporary.py
echo voices = engine.getProperty('voices') >> temporary.py
echo engine.setProperty('voice', voices[0].id)  # Выбор первого мужского голоса (можно попробовать другие индексы для разных голосов) >> temporary.py
echo engine.save_to_file("%TEXT%", "output.wav") >> temporary.py
echo engine.runAndWait() >> temporary.py

:: Преобразование в mp3
echo audio = AudioSegment.from_wav("output.wav") >> temporary.py
echo audio.export("output.mp3", format="mp3") >> temporary.py
echo mask_voice("output.mp3") >> temporary.py

:: Запуск Python-скрипта
python temporary.py

:: Очистка временных файлов
del temporary.py

:: Удаление файла .wav
del output.wav

:: Проверка и воспроизведение файла
if exist output.mp3 (
    start output.mp3
    echo Аудиофайл сохранен как output.mp3
) else (
    echo Ошибка: файл не был создан.
)

pause