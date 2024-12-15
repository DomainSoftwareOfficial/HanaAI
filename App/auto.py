import re
import emoji
import os
import sys
from dotenv import load_dotenv
import requests
import json
from datetime import datetime
import time

def emotion(input_text, model=None):
    """Automata logic to handle both local GGUF model and fallback to WebUI."""

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

    def remove_invalid_bytes(data):
        """Remove byte sequences represented as <0x..>."""
        return re.sub(r'<0x[0-9A-Fa-f]{1,2}>', '', data)

    log_debug("Запуск обработки Automata AI...")

    # Load environment variables (e.g., WebUI URL)
    load_dotenv()
    log_debug("Переменные окружения загружены.")

    chat_set = os.getenv('Instruction-Set')

    # Use resource_path to access files with PyInstaller compatibility
    instructions_path = resource_path("../Data/Input/profile.emote")

    log_debug(f"Чтение файлов ввода: {instructions_path}")

    # Ensure files are read with UTF-8 encoding
    with open(instructions_path, "r", encoding='utf-8') as file:
        instructions = file.read()

    # Split the instructions into two parts: the first four lines and the rest
    instructions_lines = instructions.splitlines()
    instructions_pt1 = "\n".join(instructions_lines[:4])  # First four lines
    instructions_pt2 = "\n".join(instructions_lines[4:])  # The rest

    log_debug("Файлы успешно прочитаны.")

    if chat_set == 'Alpaca':
        prompt = f"{instructions_pt1}\n{instructions_pt2}\nHana Busujima: {input_text}\n\n### Response:\nAutomata:"
    elif chat_set == 'ChatML':
        prompt = f"{instructions_pt1}\n{instructions_pt2}\nHana Busujima: {input_text}<|im_end|>\n<|im_start|>assistant\nAutomata:"

    log_debug(f"Сгенерирована подсказка с использованием {chat_set} набора инструкций.")

    # Check if a model is provided, use it; otherwise, fallback to WebUI
    if model is not None:
        log_debug("Предоставлена локальная модель GGUF. Использование локальной модели.")
        try:
            start_time = time.time()
            response = model(prompt, max_tokens=512, temperature=0.6, top_p=0.8, top_k=50)  # Adjust as needed
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
            "prompt": prompt,
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
        return "Fix the Webui."

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

def resource_path(relative_path):
    """Get path to resource relative to the executable's location."""
    # Get the directory of the executable if frozen (PyInstaller), else use script location
    base_path = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
    return os.path.join(base_path, relative_path)