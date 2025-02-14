import os
import sys
import numpy as np
import whisper
import io
import re
import time
import emoji
import json
import requests
from gtts import gTTS
from pydub import AudioSegment, effects
from datetime import datetime
import shutil
import random
from audio import tts_en
from audio import tts_ru
from audio import tts_es
from audio import tts_ja
from audio import distort
from rvc import mainrvc
from model import load_model
from dotenv import load_dotenv

# Set to store previously accessed files
accessed_files = set()

def log_debug(message, width=150):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Prepare the log prefix (timestamp + INFO label)
        prefix = f"{timestamp} | INFO | "
        
        # Calculate the available width for the message (subtract prefix length from total width)
        available_width = width - len(prefix)

        # If the message is too long, truncate it and add ...{hidden}
        if len(message) > available_width:
            message = message[:available_width - len("...{скрытый}")] + "...{скрытый}"

        # Print the final log message with the prefix
        print(f"{prefix}{message}")

def load_whisper_model(model=None):
    """
    Loads the Whisper model if not already provided.

    Parameters:
        model (whisper.Whisper or None): A preloaded Whisper model or None.
    
    Returns:
        whisper.Whisper: The provided or newly loaded Whisper model.
    """
    if model is not None:
        print("Используется предоставленная модель Whisper.")
        return model
    
    print("Загрузка модели Whisper: large...")
    return whisper.load_model("large")

def get_oldest_mp3_file(folder_path):
    """
    Scans the given folder and returns the full path of the oldest .mp3 file 
    that has not been accessed before.

    Parameters:
        folder_path (str): The path to the folder containing .mp3 files.

    Returns:
        str or None: The full path to the oldest unaccessed .mp3 file, or None if no suitable file is found.
    """
    if not os.path.isdir(folder_path):
        raise ValueError("The provided path is not a valid directory.")

    # Get all unaccessed .mp3 files in the directory
    mp3_files = [
        os.path.join(folder_path, f) for f in os.listdir(folder_path)
        if f.lower().endswith('.mp3') and f not in accessed_files
    ]

    if not mp3_files:
        return None  # No unaccessed .mp3 files found

    # Find the oldest file based on creation time
    oldest_file = min(mp3_files, key=os.path.getctime)

    # Mark the file as accessed (store just the filename for robustness)
    accessed_files.add(os.path.basename(oldest_file))

    return oldest_file

def generate_random_number():
    """Generates a random number between 0 and 2."""
    return random.randint(0, 2)

def load_gguf_model(model_path=None):
    """
    Loads a GGUF model using llama.cpp.
    
    If no model path is provided, it loads a default model.
    """
    if model_path is None:
        log_debug("No GGUF model provided. Loading default model...")
        model_path = "../Utlities/Models//openhermes-2.5-neural-chat-7b-v3-2-7b.Q4_K_M.gguf"
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"GGUF model not found at {model_path}")
    
    log_debug(f"Загрузка GGUF модели из: {model_path}")
    
    model = load_model(model_path)
    
    return model

def call(folder_path, destination_folder='../Assets/Audio/Call/', whisper_model=None, gguf_model=None, language='en', speed_up_factor=1.2, gain_dB=5):
    """
    Processes the oldest .mp3 file in the folder by performing Whisper transcription,
    gTTS text-to-speech conversion with speedup and gainDB, and applying voice masking.
    AI response in the event of a roll of one or two.

    Parameters:
        folder_path (str): Path to the folder containing .wav files.
        destination_folder (str): Path to save the renamed processed file.
        whisper_model: Preloaded Whisper model. If None, loads one using llama.cpp.
        gguf_model: Preloaded GGUF model. If None, a default model is loaded.
        language (str): Language for text-to-speech conversion.
        speed_up_factor (float): Factor to speed up the audio.
        gain_dB (int): Decibel gain to increase the loudness of the output.
    
    Returns:
        None (Processed file is moved and renamed).
    """
    if whisper_model is None:
        log_debug("Модель Whisper не предоставлена. Загружаем модель по умолчанию...")
        whisper_model = load_whisper_model(whisper_model)

    processed_files = set()  # Track processed files to detect new ones
    first_roll = True  # Ensures first roll is 0 for new file processing

    while True:
        mp3_files = [f for f in os.listdir(folder_path) if f.endswith('.mp3')]
        initial_file_count = len(mp3_files)
        oldest_file = get_oldest_mp3_file(folder_path)
        caller = 'Caller'

        # Check if the oldest file is in processed files
        if not oldest_file or oldest_file in processed_files:
            log_debug(f"Файл {oldest_file} уже обработан или не найден.")
            time.sleep(2)  # Wait before checking again
            continue

        processed_files.add(oldest_file)  # Mark file as processed

        with open("../Data/Output/caller.txt", "w") as file:
            file.write(f"{os.path.abspath(oldest_file)}")

        # Run Whisper transcription
        result = whisper_model.transcribe(oldest_file)
        transcribed_text = result["text"]
        log_debug(f"Распознанный текст: {transcribed_text}")

        # Save the transcription as a .txt file with the same name as the audio
        transcription_path = os.path.splitext(oldest_file)[0] + ".txt"
        with open(transcription_path, "w", encoding="utf-8") as txt_file:
            txt_file.write(transcribed_text)

        log_debug(f"Транскрипция сохранена в: {transcription_path}")

        while True:
            random_number = 0 if first_roll else generate_random_number()
            first_roll = False  # Normal behavior resumes after first roll

            if random_number == 1:
                prompt = f'System: {caller} said: {transcribed_text}'
                response = respond(prompt, random_number, gguf_model)
                transcribed_text = response
                caller = 'Hana Busujima'


                if language == 'en':
                    tts_en(response)
                elif language == 'ja':
                    tts_ja(response)
                elif language == 'ru':
                    tts_ru(response)
                elif language == 'es':
                    tts_es(response)
                else:
                    tts_en(response)

                response_path = resource_path('../Assets/Audio/ai.wav')
                rvc_path = resource_path('../Assets/Audio/hana.wav')
                mainrvc(response_path, rvc_path)

                # Move and rename the processed file
                original_filename = os.path.basename(oldest_file)
                name, ext = os.path.splitext(original_filename)
                new_filename = f"{name}.hana.wav"
                new_file_path = os.path.join(destination_folder, new_filename)

                shutil.move(rvc_path, new_file_path)
                with open("../Data/Output/responder.txt", "w") as file:
                    file.write(f"{os.path.abspath(new_file_path)}")

                log_debug(f"Файл перемещен и переименован: {new_file_path}")

            elif random_number == 2:
                prompt = f'System: {caller} said: {transcribed_text}'
                response = respond(prompt, random_number, gguf_model)
                transcribed_text = response
                caller = 'Chloe Hayashi'

                if language == 'en':
                    tts_en(response)
                elif language == 'ja':
                    tts_ja(response)
                elif language == 'ru':
                    tts_ru(response)
                elif language == 'es':
                    tts_es(response)
                else:
                    tts_en(response)

                response_path = resource_path('../Assets/Audio/ai.wav')
                distort_path = resource_path('../Assets/Audio/chloe.wav')
                static_path = resource_path('../Assets/Audio/radio.mp3')
                distort(response_path, static_path, output_file_path=distort_path)

                # Move and rename the processed file
                original_filename = os.path.basename(oldest_file)
                name, ext = os.path.splitext(original_filename)
                new_filename = f"{name}.chloe.wav"
                new_file_path = os.path.join(destination_folder, new_filename)

                shutil.move(distort_path, new_file_path)
                with open("../Data/Output/responder.txt", "w") as file:
                    file.write(f"{os.path.abspath(new_file_path)}")

                log_debug(f"Файл перемещен и переименован: {new_file_path}")

            else:
                break  # Exit to process the new file

            # Check the file count again after processing
            new_file_count = len([f for f in os.listdir(folder_path) if f.endswith('.mp3')])
            if initial_file_count == new_file_count:
                pass
            else:
                log_debug("Обнаружен новый файл. Прерывание цикла для обработки нового файла...")
                break  # Exit to process the new file

def respond(prompt, name, model):
    """
    Processes a prompt based on environment instructions, model availability, and name constraints.

    Parameters:
        prompt (str): The input string prompt.
        name (int): An integer (must be between 0 and 2).
        model: The Llama model (can be None).

    Returns:
        Response (AI response).
    """
    # Print different messages based on the name integer
    if name == 1:
        responder = 'Hana Busujima'
        instructions_path = resource_path("../Data/Input/profile.hana")
    elif name == 2:
        responder = 'Chloe Hayashi'
        instructions_path = resource_path("../Data/Input/profile.chloe")
    elif name == 3:
        responder = 'Kaito Shibata'
        instructions_path = resource_path("../Data/Input/profile.kaito")

    # Check environment variable "instructions"
    load_dotenv()
    instructions_set = os.getenv("Instruction-Set")

    # Ensure files are read with UTF-8 encoding
    with open(instructions_path, "r", encoding='utf-8') as file:
        instructions = file.read()

    # Split the instructions into two parts: the first four lines and the rest
    instructions_lines = instructions.splitlines()
    instructions_pt1 = "\n".join(instructions_lines[:4])  # First four lines
    instructions_pt2 = "\n".join(instructions_lines[4:])  # The rest

    if instructions_set == 'Alpaca':
        new_prompt = f"{instructions_pt1}\n\n{instructions_pt2}\n{prompt}\n\n### Response:\n{responder}:"
    elif instructions_set == 'ChatML':
        new_prompt = f"{instructions_pt1}\n\n{instructions_pt2}\n{prompt}<|im_end|>\n<|im_start|>assistant\n{responder}:"

    # Check if model is None
    if model is not None:
        log_debug("Предоставлена локальная модель GGUF. Использование локальной модели.")
        try:
            start_time = time.time()
            response = model(new_prompt, max_tokens=512, temperature=0.6, top_p=0.8, top_k=50)
            end_time = time.time()
            elapsed_time = end_time - start_time

            # Process the response
            new_result = response['choices'][0]['text'].replace("\n", "")
            new_result = re.sub(r'\*.*?\*', '', new_result)  # Remove text between asterisks
            new_result = emoji.replace_emoji(new_result, replace='')  # Remove emojis

            new_result = truncate_at_newline(new_result)
            
            new_result = remove_invalid_bytes(new_result)

            log_debug(f"Ответ модели: {new_result} (Обработано за {elapsed_time:.2f} с.)")

            return new_result
        except Exception as e:
            log_debug(f"Ошибка при использовании модели GGUF: {e}")
            return "Error using the local model. Please check the model setup."
        
    # If no local model is provided, fallback to WebUI
    log_debug("Локальная модель не предоставлена. Переход на WebUI.")
    try:
        url = f"{os.getenv('Text-Generation')}/v1/completions"
        headers = {"Content-Type": "application/json"}
        data = {
            "prompt": new_prompt,
            "mode": "chat-instruct",
            "instruction_template": "Alpaca",
            "max_tokens": 512,
            "temperature": 0.6,
            "top_p": 0.8,
            "top_k": 50,
        }

        start_time = time.time()
        response = requests.post(url, headers=headers, json=data, verify=False)
        end_time = time.time()
        elapsed_time = end_time - start_time
        if response.status_code == 200:
            results = json.loads(response.content.decode('utf-8'))["choices"][0]["text"]
            new_result = results.replace("\n", "")
            new_result = re.sub(r'\*.*?\*', '', new_result)
            new_result = emoji.replace_emoji(new_result, replace='')

            new_result = truncate_at_newline(new_result)

            new_result = remove_invalid_bytes(new_result)

            log_debug(f"Ответ WebUI: {new_result} (Обработано за {elapsed_time:.2f} с.)")

            return new_result
        else:
            log_debug(f"Запрос к WebUI завершился с кодом: {response.status_code}")
            return "Failed to connect to WebUI."
    except Exception as e:
        log_debug(f"Ошибка подключения к WebUI: {e}")
        return "WebUI connection error."
    
def resource_path(relative_path):
    """Get path to resource relative to the executable's location."""
    # Get the directory of the executable if frozen (PyInstaller), else use script location
    base_path = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
    return os.path.join(base_path, relative_path)

# Helper function to truncate at newlines
def truncate_at_newline(text):
    """Truncate the text right before it encounters any newline sequences (<0x0A><0x0A> or <0x0A> in the output)."""
    # First, look for double newlines \n\n (corresponding to <0x0A><0x0A>)
    double_newline_pos = text.find('<0x0A><0x0A>')
    if double_newline_pos != -1:
        # Truncate everything after the first occurrence of <0x0A><0x0A>
        return text[:double_newline_pos].strip()
    
    # If no double newline is found, look for a single newline \n (corresponding to <0x0A>)
    single_newline_pos = text.find('<0x0A>')
    if single_newline_pos != -1:
        # Truncate everything after the first occurrence of <0x0A>
        return text[:single_newline_pos].strip()

    # If no newlines are found, return the original text
    return text.strip()

def remove_invalid_bytes(data):
        """Remove byte sequences represented as <0x..>."""
        return re.sub(r'<0x[0-9A-Fa-f]{1,2}>', '', data)

if __name__ == "__main__":
    folder_path = "../Assets/Audio/Call"

    llm_model = load_model('../Utilities/Models/openhermes-2.5-neural-chat-7b-v3-2-7b.Q4_K_M.gguf')

    if not os.path.isdir(folder_path):
        log_debug("Ошибка: Указанная папка недействительна.")
    else:
        # Step 1: Load Whisper model
        whisper_model = load_whisper_model()  

        # Step 2: Process the audio folder
        call(folder_path, whisper_model=whisper_model, gguf_model=llm_model)

        log_debug("Обработка завершена!")