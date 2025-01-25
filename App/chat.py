import pytchat
import os
import sys
import threading
import asyncio
from model import load_model
from collections import deque
from dotenv import load_dotenv
from twitchio.ext import commands as twitch_commands
from datetime import datetime
import time
import re
import contextlib
import random
import json
import requests
import emoji

class YouTubeChatHandler:
    def __init__(self, video_id, mod_names):
        # Resolve the base path for PyInstaller
        self.base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        self.chat = pytchat.create(video_id=video_id, interruptable=False)
        self.mod_names = set(mod_names)
        self.queue = [deque(maxlen=1) for _ in range(3)]  # 3 separate deques for the top 3 chats
        self.super_chat_file = self.resource_path('../Data/Chat/Special/superchat.chloe')
        self.super_chat_username_file = self.resource_path('../Data/Chat/Special/superviewer.chloe')
        self.mod_chat_file = self.resource_path('../Data/Chat/Special/modmessage.hana')
        self.mod_chat_username_file = self.resource_path('../Data/Chat/Special/moderator.hana')
        self.chat_files = [
            self.resource_path('../Data/Chat/General/input1.hana'),
            self.resource_path('../Data/Chat/General/input2.hana'),
            self.resource_path('../Data/Chat/General/input3.hana')
        ]
        self.username_files = [
            self.resource_path('../Data/Chat/General/viewer1.hana'),
            self.resource_path('../Data/Chat/General/viewer2.hana'),
            self.resource_path('../Data/Chat/General/viewer3.hana')
        ]
        self._stop_event = threading.Event()

    def handle_chat(self, item):
        message = item.message
        username = item.author.name

        # Check for super chat
        if item.type == 'superChat':
            self.save_to_file(self.super_chat_file, message)
            self.save_to_file(self.super_chat_username_file, username)

        # Check if the user is a moderator
        elif username in self.mod_names:
            self.save_to_file(self.mod_chat_file, message)
            self.save_to_file(self.mod_chat_username_file, username)

        # Handle regular chat messages
        else:
            # Shift chats in the queue
            for i in range(2, 0, -1):
                if self.queue[i-1]:
                    self.queue[i].append(self.queue[i-1].pop())

            self.queue[0].append((username, message))

            # Save to respective files
            for i, q in enumerate(self.queue):
                if q:
                    self.save_to_file(self.chat_files[i], q[0][1])
                    self.save_to_file(self.username_files[i], q[0][0])

    def save_to_file(self, file_path, content):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"{content}\n")

    def start(self):
        while not self._stop_event.is_set() and self.chat.is_alive():
            for item in self.chat.get().sync_items():
                self.handle_chat(item)

    def stop(self):
        self._stop_event.set()

    def resource_path(self, relative_path):
        """Get path to resource relative to the executable's location."""
        # Get the directory of the executable if frozen (PyInstaller), else use script location
        base_path = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
        return os.path.join(base_path, relative_path)

class TwitchChatHandler(twitch_commands.Bot):
    def __init__(self, token, client_id, nick, prefix, initial_channels, mod_names):
        super().__init__(token=token, client_id=client_id, nick=nick, prefix=prefix, initial_channels=initial_channels)
        # Resolve the base path for PyInstaller
        self.base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        self.mod_names = set(mod_names)
        self.queue = [deque(maxlen=1) for _ in range(3)]  # 3 separate deques for the top 3 chats
        self.super_chat_file = self.resource_path('../Data/Chat/Special/superchat.chloe')
        self.super_chat_username_file = self.resource_path('../Data/Chat/Special/superviewer.chloe')
        self.mod_chat_file = self.resource_path('../Data/Chat/Special/modmessage.hana')
        self.mod_chat_username_file = self.resource_path('../Data/Chat/Special/moderator.hana')
        self.chat_files = [
            self.resource_path('../Data/Chat/General/input1.hana'),
            self.resource_path('../Data/Chat/General/input2.hana'),
            self.resource_path('../Data/Chat/General/input3.hana')
        ]
        self.username_files = [
            self.resource_path('../Data/Chat/General/viewer1.hana'),
            self.resource_path('../Data/Chat/General/viewer2.hana'),
            self.resource_path('../Data/Chat/General/viewer3.hana')
        ]
        self._stop_event = threading.Event()

    async def event_message(self, message):
        if self._stop_event.is_set():
            return  # Stop processing messages when the event is set
        await self.handle_chat(message)

    async def handle_chat(self, message):
        username = message.author.name
        content = message.content

        # Check for special messages (like Super Chat)
        if message.tags.get('badges') and 'broadcaster' in message.tags.get('badges'):
            self.save_to_file(self.super_chat_file, content)
            self.save_to_file(self.super_chat_username_file, username)

        # Check if the user is a moderator
        elif username in self.mod_names:
            self.save_to_file(self.mod_chat_file, content)
            self.save_to_file(self.mod_chat_username_file, username)

        # Handle regular chat messages
        else:
            # Shift chats in the queue
            for i in range(2, 0, -1):
                if self.queue[i-1]:
                    self.queue[i].append(self.queue[i-1].pop())

            self.queue[0].append((username, content))

            # Save to respective files
            for i, q in enumerate(self.queue):
                if q:
                    self.save_to_file(self.chat_files[i], q[0][1])
                    self.save_to_file(self.username_files[i], q[0][0])

    def save_to_file(self, file_path, content):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"{content}\n")

    def stop(self):
        self._stop_event.set()
        asyncio.run_coroutine_threadsafe(self.close(), self.loop)

    def run(self):
        # Start bot as normal
        super().run()

    def resource_path(self, relative_path):
        """Get path to resource relative to the executable's location."""
        # Get the directory of the executable if frozen (PyInstaller), else use script location
        base_path = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
        return os.path.join(base_path, relative_path)

class AutoChatHandler:
    def __init__(self, input_text, model_path=None, instructions_file="../Data/Input/profile.chat", output_file="../Data/Input/chat.txt", repetitions=1):
        """
        Initializes the AutoChatHandler.
        :param input_text: Text to process repeatedly.
        :param model_path: Path to the GGUF model file. If None, WebUI will be used.
        :param instructions_file: Path to the instructions file.
        :param output_file: Path to the output text file.
        :param repetitions: Number of times to run the AI.
        """
        self.simulation_event = threading.Event()  # Thread-safe control
        self.input_text = input_text
        self.model_path = model_path
        self.model = None  # Placeholder for the loaded model
        self.instructions_file = instructions_file
        self.output_file = output_file
        self.repetitions = repetitions
        self.line_processing_delay = random.uniform(5, 10)  # Initial delay in seconds

        # Load the model if a model path is provided
        if self.model_path:
            self.log_debug(f"Загрузка модели: {self.model_path}")
            self.model = load_model(self.model_path)
            if not self.model:
                self.log_debug("Ошибка при загрузке модели. Проверьте путь к файлу модели.")

    def log_debug(self, message, width=150):
        """Логирование сообщений с временными метками."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        prefix = f"{timestamp} | ИНФО | "
        available_width = width - len(prefix)
        if len(message) > available_width:
            message = message[:available_width - len("...{скрытый}")] + "...{скрытый}"
        print(f"{prefix}{message}")

    def run_ai(self, input_text):
        """
        Запуск AI на одном входном тексте и возврат результата.
        :param input_text: Текст для обработки.
        :return: Результат AI.
        """
        try:
            result = self.ai(input_text, model=self.model)
            return result
        except Exception as e:
            self.log_debug(f"Ошибка обработки ввода '{input_text}': {e}")
            return f"Ошибка: {e}"

    def ai(self, input_text, model=None):
        """Основная логика Hana AI для обработки с использованием локальной модели GGUF или WebUI."""
        def remove_invalid_bytes(data):
            return re.sub(r'<0x[0-9A-Fa-f]{1,2}>', '', data)

        self.log_debug("Запуск обработки Chat AI...")
        load_dotenv()
        self.log_debug("Переменные окружения загружены.")

        chat_set = os.getenv('Instruction-Set')
        instructions_path = self.resource_path(self.instructions_file)

        self.log_debug(f"Чтение файла инструкций: {instructions_path}")
        with open(instructions_path, "r", encoding='utf-8') as file:
            instructions = file.read()

        instructions_lines = instructions.splitlines()
        instructions_pt1 = "\n".join(instructions_lines[:4])
        instructions_pt2 = "\n".join(instructions_lines[4:])

        self.log_debug("Файл инструкций успешно прочитан.")

        if chat_set == 'Alpaca':
            prompt = f"{instructions_pt1}\n\n{instructions_pt2}\nUser: {input_text}\n\n### Response:\nAssistant:"
        elif chat_set == 'ChatML':
            prompt = f"{instructions_pt1}\n\n{instructions_pt2}\nUser: {input_text}<|im_end|>\n<|im_start|>assistant\nnAssistant:"

        self.log_debug(f"Сформирован запрос с использованием набора инструкций {chat_set}.")

        if model is not None:
            self.log_debug("Используется локальная модель GGUF.")
            try:
                start_time = time.time()
                response = model(prompt, max_tokens=512, temperature=0.6, top_p=0.8, top_k=50)
                elapsed_time = time.time() - start_time
                new_result = response['choices'][0]['text'].replace("\n", "")
                new_result = re.sub(r'\*.*?\*', '', new_result)
                new_result = emoji.replace_emoji(new_result, replace='')
                new_result = self.truncate_at_newline(new_result)
                new_result = remove_invalid_bytes(new_result)
                self.log_debug(f"Ответ модели: {new_result} (Обработано за {elapsed_time:.2f} секунд)")
                return new_result
            except Exception as e:
                self.log_debug(f"Ошибка при использовании локальной модели GGUF: {e}")
                return "Ошибка использования локальной модели. Проверьте настройки модели."

        self.log_debug("Локальная модель не предоставлена. Переход на WebUI.")
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
            elapsed_time = time.time() - start_time
            if response.status_code == 200:
                results = json.loads(response.content.decode('utf-8'))["choices"][0]["text"]
                new_result = results.replace("\n", "")
                new_result = re.sub(r'\*.*?\*', '', new_result)
                new_result = emoji.replace_emoji(new_result, replace='')
                new_result = self.truncate_at_newline(new_result)
                new_result = remove_invalid_bytes(new_result)
                self.log_debug(f"Ответ WebUI: {new_result} (Обработано за {elapsed_time:.2f} секунд)")
                return new_result
            else:
                self.log_debug(f"Запрос к WebUI завершился с кодом: {response.status_code}")
                return "Ошибка подключения к WebUI."
        except Exception as e:
            self.log_debug(f"Ошибка подключения к WebUI: {e}")
            return "Ошибка подключения к WebUI."

    def process_text_file(self, file_path):
        """
        Processes a text file line by line with a delay between each line. Each line is expected to have the format:
        [viewer]::[message]. The function removes the "::" and distributes the 'viewer'
        and 'message' parts across separate files in round-robin order.

        :param file_path: Path to the text file to be processed.
        """

        viewer_files = [os.path.join("../Data/Chat/General", f"viewer{i}.hana") for i in range(1, 4)]
        input_files = [os.path.join("../Data/Chat/General", f"input{i}.hana") for i in range(1, 4)]

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                lines = file.readlines()

            for i, line in enumerate(lines):
                if not self.simulation_event.is_set():  # Check thread-safe stop event
                    self.log_debug("Processing stopped due to simulation being disabled.")
                    break

                if "::" not in line:
                    self.log_debug(f"Invalid line format: {line.strip()}")
                    continue

                viewer_index = i % len(viewer_files)
                input_index = i % len(input_files)

                viewer, message = line.strip().split("::", 1)

                with open(viewer_files[viewer_index], "w", encoding="utf-8") as vf, \
                     open(input_files[input_index], "w", encoding="utf-8") as inf:
                    vf.write(viewer + "\n")
                    inf.write(message + "\n")

                self.log_debug(f"Processed line: {line.strip()}")
                time.sleep(self.line_processing_delay)

            self.log_debug("File successfully processed and data distributed.")

        except FileNotFoundError:
            self.log_debug(f"File {file_path} not found.")
        except Exception as e:
            self.log_debug(f"Error processing file {file_path}: {e}")
                
    def truncate_at_newline(self, text):
        """Обрезает текст перед последовательностью новой строки."""
        double_newline_pos = text.find('<0x0A><0x0A>')
        if double_newline_pos != -1:
            return text[:double_newline_pos].strip()
        single_newline_pos = text.find('<0x0A>')
        if single_newline_pos != -1:
            return text[:single_newline_pos].strip()
        return text.strip()

    def resource_path(self, relative_path):
        """Возвращает путь к ресурсу относительно расположения исполняемого файла."""
        base_path = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
        return os.path.join(base_path, relative_path)

    def append_to_file(self, text):
        """Добавляет текст к выходному файлу."""
        with open(self.output_file, "a", encoding="utf-8") as file:
            file.write(text + "\n")

    def run(self):
        """
        Continuously processes user input with the AI and writes results to the output file.
        """
        try:
            self.log_debug("AutoChatHandler запущен. Нажмите Ctrl+C для остановки.")
            while True:
                # Prompt for input
                self.input_text = input("Введите текст для обработки (или 'выход' для завершения): ").strip()
                if self.input_text.lower() in {"выход", "exit"}:
                    self.log_debug("Скрипт остановлен пользователем.")
                    break

                # Process input
                self.log_debug(f"Обработка ввода: {self.input_text}")
                result = self.run_ai(self.input_text)
                self.log_debug(f"Результат: {result}")

                # Write the result to the output file
                self.append_to_file(result)
                self.log_debug("Результат записан в файл.")
        except KeyboardInterrupt:
            self.log_debug("Скрипт остановлен пользователем с помощью Ctrl+C.")
        finally:
            self.log_debug("AutoChatHandler завершил работу.")

def list_models_in_folder(folder_path):
    """
    Lists GGUF model files in a specified folder.
    :param folder_path: Path to the folder containing GGUF models.
    :return: List of model file names.
    """
    temp_handler = AutoChatHandler(input_text="", model=None)  # Temporary handler for logging
    try:
        temp_handler.log_debug(f"Сканирование папки для моделей: {folder_path}")
        return [f for f in os.listdir(folder_path) if f.endswith('.gguf')]
    except FileNotFoundError:
        temp_handler.log_debug(f"Папка не найдена: {folder_path}")
        print(f"Папка не найдена: {folder_path}")
        return []

def get_model_files(models_directory):
    """Retrieve a list of model files in the specified directory."""
    return [f for f in os.listdir(models_directory) if f.endswith(".gguf")]

def automate_chat():
    # Scan the model directory for available models
    models_directory = "../Utilities/Models"
    model_files = get_model_files(models_directory)

    print("Выберите модель для использования:")
    for idx, model_file in enumerate(model_files, start=1):
        print(f"{idx}. {model_file}")
    print("0. Использовать WebUI")

    # Get user selection
    try:
        selection = int(input("Введите номер модели: "))
        if selection == 0:
            print("Используется WebUI.")
            selected_model = None
        elif 1 <= selection <= len(model_files):
            selected_model = os.path.join(models_directory, model_files[selection - 1])
            print(f"Вы выбрали модель: {selected_model}")
        else:
            print("Недопустимый выбор. Выход.")
            return
    except ValueError:
        print("Пожалуйста, введите допустимый номер. Выход.")
        return

    # Create and run AutoChatHandler
    input_text = input("Введите текст для обработки: ")
    handler = AutoChatHandler(input_text=input_text, model_path=selected_model)
    handler.run()

def youtube_chat():
    load_dotenv()
    video_id = os.getenv('Video-Url')
    mod_names = ["mod1", "mod2", "mod3"]  # Replace with actual moderator names
    handler = YouTubeChatHandler(video_id, mod_names)
    handler.start()


def twitch_chat():
    load_dotenv()
    token = os.getenv('Twitch-Token')
    client_id = os.getenv('Twitch-Client-ID')
    nick = os.getenv('Twitch-Nick')
    prefix = os.getenv('Twitch-Prefix')
    initial_channels = [os.getenv('Twitch-Channel')]
    mod_names = ["mod1", "mod2", "mod3"]  # Replace with actual moderator names

    bot = TwitchChatHandler(token=token, client_id=client_id, nick=nick, prefix=prefix, initial_channels=initial_channels, mod_names=mod_names)
    bot.run()

if __name__ == "__main__":
    automate_chat()