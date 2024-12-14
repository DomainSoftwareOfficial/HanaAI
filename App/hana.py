import re
import emoji
import customtkinter as ctk
import tkinter as tk
import os
import sys
from dotenv import load_dotenv
import requests
import json
from datetime import datetime
import time

class Ranting(ctk.CTkToplevel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.title("Вторичное окно")
        self.geometry("400x300")  # Window dimensions
        self.protocol("WM_DELETE_WINDOW", self.cleanup)  # Cleanup on close

        self.log_debug("Открыто вторичное окно.", width=150)

        # Top Textbox with round corners
        self.top_textbox = ctk.CTkTextbox(self, height=70, corner_radius=10)
        self.top_textbox.pack(fill="x", padx=10, pady=(10, 5))
        self.top_textbox.insert("1.0", "Введите текст сюда...")
        self.log_debug("Создан текстовый виджет для ввода текста.", width=150)

        # Middle Row
        middle_frame = ctk.CTkFrame(self)
        middle_frame.pack(fill="x", padx=10, pady=5)

        # Textbox in the middle with sharp corners and adjusted height
        self.middle_textbox = ctk.CTkTextbox(
            middle_frame, width=60, height=50, corner_radius=0
        )
        self.middle_textbox.pack(side="left", padx=(0, 5))
        self.middle_textbox.insert("1.0", "0")

        # Frame for increment and decrement buttons
        button_frame = ctk.CTkFrame(middle_frame)
        button_frame.pack(side="left", padx=(0, 5))

        # Increment/Decrement buttons stacked vertically
        ctk.CTkButton(
            button_frame, text="+", width=20, height=20, corner_radius=0, command=self.increment_value
        ).pack(pady=(0, 5))
        ctk.CTkButton(
            button_frame, text="-", width=20, height=20, corner_radius=0, command=self.decrement_value
        ).pack()

        # Submit button
        submit_button = ctk.CTkButton(
            middle_frame, text="Submit", height=50, corner_radius=0, command=self.on_submit
        )
        submit_button.pack(side="left", fill="x", expand=True, padx=(5, 0))

        # Bottom Row
        bottom_frame = ctk.CTkFrame(self, height=50)  # Explicitly set height for the section
        bottom_frame.pack(fill="x", padx=10, pady=10)  # No expand=True, maintain original height

        self.bottom_textboxes = []
        for i in range(4):
            tb = ctk.CTkTextbox(bottom_frame, width=85, height=30, corner_radius=0)
            tb.pack(side="left", padx=5, pady=(10, 10))  # Add equal padding for vertical centering within the fixed height
            tb.insert("1.0", "Текст")
            self.bottom_textboxes.append(tb)

    def log_debug(self, message, width=150):
        """Logs debug messages with Russian truncation support."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        prefix = f"{timestamp} | INFO | "
        available_width = width - len(prefix)
        if len(message) > available_width:
            message = message[:available_width - len("...{скрытый}")] + "...{скрытый}"
        print(f"{prefix}{message}")

    def on_submit(self):
        """Handle the Submit button click."""
        value = self.middle_textbox.get("1.0", "end-1c").strip()
        self.log_debug(f"Submitted value: {value}", width=150)

    def increment_value(self):
        """Increment the number in the middle textbox."""
        value = int(self.middle_textbox.get("1.0", "end-1c").strip())
        self.update_middle_textbox(value + 1)

    def decrement_value(self):
        """Decrement the number in the middle textbox."""
        value = int(self.middle_textbox.get("1.0", "end-1c").strip())
        self.update_middle_textbox(value - 1)

    def update_middle_textbox(self, value):
        """Update the value in the middle textbox."""
        self.middle_textbox.delete("1.0", "end")
        self.middle_textbox.insert("1.0", str(value))

    def cleanup(self):
        """Handle cleanup before window is destroyed."""
        self.destroy()

class Reading(ctk.CTkToplevel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.title("Reading Window")
        self.geometry("400x300")
        self.protocol("WM_DELETE_WINDOW", self.cleanup)

        # Top Textbox with rounded corners (height adjusted to match Ranting's top row)
        self.top_textbox = ctk.CTkTextbox(self, height=70, corner_radius=10)
        self.top_textbox.pack(fill="x", padx=10, pady=(10, 5))
        self.top_textbox.insert("1.0", "Enter text here...")

        # Middle Row with two equal-width buttons
        middle_frame = ctk.CTkFrame(self, height=50)  # Match height to button height
        middle_frame.pack(fill="x", padx=10, pady=5)

        # Two buttons of equal width (matching Ranting's layout)
        button_width = (400 - 30) / 2  # Subtracting padding from the window width
        self.button_1 = ctk.CTkButton(
            middle_frame, text="Button 1", width=button_width, height=50, corner_radius=0
        )
        self.button_1.pack(side="left", padx=(0, 5), pady=0)  # Remove additional padding to align with frame

        self.button_2 = ctk.CTkButton(
            middle_frame, text="Button 2", width=button_width, height=50, corner_radius=0
        )
        self.button_2.pack(side="right", padx=(5, 0), pady=0)

        # Bottom Row with textboxes (height adjusted to match Ranting's bottom row)
        bottom_frame = ctk.CTkFrame(self, height=50)  # Fixed height for the section
        bottom_frame.pack(fill="x", padx=10, pady=10)

        self.bottom_textboxes = []
        for i in range(4):
            tb = ctk.CTkTextbox(bottom_frame, width=85, height=30, corner_radius=0)
            tb.pack(side="left", padx=5, pady=(10, 10))  # Equal padding for vertical centering
            tb.insert("1.0", "Текст")
            self.bottom_textboxes.append(tb)

    def cleanup(self):
        """Handle cleanup before window is destroyed."""
        self.destroy()

class HWindow(ctk.CTkToplevel):
    def __init__(self, app):
        super().__init__()

        self.app = app
        self.title("Hana Chatter")
        self.geometry("400x300")
        ctk.set_appearance_mode("dark")  # Dark mode
        ctk.set_default_color_theme("green")  # Green accent

        self.attributes("-topmost", True)
        # Create a frame for the text box and text
        frame = ctk.CTkFrame(self)
        frame.pack(expand=True, fill="both", padx=10, pady=10)

        # Add text label above the text box
        label = ctk.CTkLabel(frame, text="Now Responding:")
        label.pack(pady=(10, 5))  # Padding above and below the label

        # Create a text box
        self.textbox = ctk.CTkTextbox(frame, width=300, height=150, wrap='none')
        self.textbox.pack(padx=10, pady=10)

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        self.destroy()

    def update_textbox(self, new_text):
        # Only update if the new_text is different from the current content
        current_text = self.textbox.get("1.0", tk.END).strip()
        if new_text != current_text:
            self.textbox.delete("1.0", tk.END)
            self.textbox.insert(tk.END, new_text)

def hana_ai(input_text, model=None):
    """Hana AI logic to handle both local GGUF model and fallback to WebUI."""

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

    log_debug("Запуск обработки Hana AI...")

    # Load environment variables (e.g., WebUI URL)
    load_dotenv()
    log_debug("Переменные окружения загружены.")

    chat_set = os.getenv('Instruction-Set')

    # Use resource_path to access files with PyInstaller compatibility
    instructions_path = resource_path("../Data/Input/profile.hana")
    memory_path = resource_path("../Data/Input/memory.txt")
    rag_path = resource_path("../Data/Input/results.txt")

    log_debug(f"Чтение файлов ввода: {instructions_path}, {memory_path}, {rag_path}")

    # Ensure files are read with UTF-8 encoding
    with open(instructions_path, "r", encoding='utf-8') as file:
        instructions = file.read()

    # Split the instructions into two parts: the first four lines and the rest
    instructions_lines = instructions.splitlines()
    instructions_pt1 = "\n".join(instructions_lines[:4])  # First four lines
    instructions_pt2 = "\n".join(instructions_lines[4:])  # The rest

    with open(memory_path, "r", encoding='utf-8') as file:
        memory = file.read()

    with open(rag_path, "r", encoding='utf-8') as file:
        rag = file.read()

    log_debug("Файлы успешно прочитаны.")

    if chat_set == 'Alpaca':
        prompt = f"{instructions_pt1}\n\n{rag}\n\n{instructions_pt2}\n\n{memory}\n{input_text}\n\n### Response:\nHana Busujima:"
    elif chat_set == 'ChatML':
        prompt = f"{instructions_pt1}\n\n{rag}\n\n{instructions_pt2}\n\n{memory}\n{input_text}<|im_end|>\n<|im_start|>assistant\nHana Busujima:"

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

            append_to_history_file(memory_path, input_text, new_result)

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

            append_to_history_file(memory_path, input_text, new_result)

            return new_result
        else:
            log_debug(f"Запрос к WebUI завершился с кодом: {response.status_code}")
            return "Failed to connect to WebUI."
    except Exception as e:
        log_debug(f"Ошибка подключения к WebUI: {e}")
        return "WebUI connection error."

def automata_ai(input_text, model=None):
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
    instructions_path = resource_path("../Data/Input/profile.automata")

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

def append_to_history_file(history_file_path, input_text, new_result):
    """Append the input and output to the history file, keeping only the last 12 lines (6 input-output pairs)."""
    # Clean up the new_result to ensure no leading/trailing spaces or newlines
    new_result = new_result.strip()

    # Create the new entry (input and output, separated by a newline)
    new_entry = f"{input_text}\nHana Busujima: {new_result}\n"

    # Read the current content of the history file
    if os.path.exists(history_file_path):
        with open(history_file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()
    else:
        lines = []

    # Append the new entry
    lines.append(new_entry)

    # Limit the file to 12 lines (6 input-output pairs)
    if len(lines) > 11:
        lines = lines[-11:]  # Keep only the last 12 lines, removing the oldest entries

    # Write the updated content back to the file
    with open(history_file_path, "w", encoding="utf-8") as file:
        file.writelines(lines)

def resource_path(relative_path):
    """Get path to resource relative to the executable's location."""
    # Get the directory of the executable if frozen (PyInstaller), else use script location
    base_path = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
    return os.path.join(base_path, relative_path)

if __name__ == "__main__":
    hana_ai("User: JoyKill asks: Hey, how are you!")