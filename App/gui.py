import os
import sys
import time
import customtkinter as ctk
import random
import threading
import whisper
import logging
import emoji
import shutil
import queue
import re
import unicodedata
from datetime import datetime
from dotenv import load_dotenv
from chloe import CWindow
from hana import HWindow
from hana import hana_ai
from chloe import chloe_ai
from chloe import ImageGenerator
from chat import YouTubeChatHandler
from chat import TwitchChatHandler
from audio import translate
from audio import record_audio
from audio import distort
from audio import tts_en
from audio import tts_es
from audio import tts_ja
from audio import tts_ru
from rvc import mainrvc
from audio import play
from rag import mainrag
from model import load_model

logging.getLogger("httpcore").setLevel(logging.CRITICAL)
logging.getLogger("httpx").setLevel(logging.CRITICAL)
logging.getLogger("hpack").setLevel(logging.CRITICAL)
logging.getLogger("numba").setLevel(logging.CRITICAL)
logging.getLogger("urllib3").setLevel(logging.CRITICAL)
logging.getLogger("gtts").setLevel(logging.CRITICAL)


class TextBoxFrame(ctk.CTkFrame):
    def __init__(self, parent, file_path):
        super().__init__(parent)

        self.file_path = file_path

        # Ensure the file exists
        self.ensure_file_exists()

        self.textbox = ctk.CTkTextbox(self, width=300, height=100, wrap='none')  # Disable line wrapping
        self.textbox.pack(padx=10, pady=10)
        self.load_content()
        self.textbox.bind('<KeyRelease>', self.save_content)  # Bind to key release event
        
        # Start a thread to monitor file changes
        self.monitor_thread = threading.Thread(target=self.monitor_file, daemon=True)
        self.monitor_thread.start()
        
    def ensure_file_exists(self):
        try:
            if not os.path.exists(self.file_path):
                # Create the directory if it doesn't exist
                os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
                # Create an empty file
                with open(self.file_path, 'w', encoding='utf-8') as file:
                    file.write("")
        except Exception as e:
            self.log_debug(f"Ошибка при сохранении содержимого: {e}")

    def load_content(self):
        try:
            with open(self.file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            self.textbox.delete("1.0", ctk.END)
            self.textbox.insert(ctk.END, content)
            self.textbox.see(ctk.END)  # Ensure the content is visible
        except Exception as e:
            self.log_debug(f"Ошибка при сохранении содержимого: {e}")

    def save_content(self, event=None):
        try:
            content = self.textbox.get("1.0", ctk.END).strip()  # Strip trailing newlines
            with open(self.file_path, 'w', encoding='utf-8') as file:
                file.write(content)
        except Exception as e:
            self.log_debug(f"Ошибка при сохранении содержимого: {e}")

    def monitor_file(self):
        last_modified = os.path.getmtime(self.file_path)
        while True:
            try:
                time.sleep(1)
                current_modified = os.path.getmtime(self.file_path)
                if current_modified != last_modified:
                    last_modified = current_modified
                    self.load_content()
            except Exception as e:
                self.log_debug(f"Ошибка при сохранении содержимого: {e}")

    def log_debug(self, message, width=150):
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

class App(ctk.CTk):
    def __init__(self, microphone_index=None, output_device_index=None, selected_platform="None", selected_llm=None):
        super().__init__()

        self.clear_last_lines()
        self.after_ids = []
        self.fancy_log("⚙️ ИНИЦИАЛИЗАЦИЯ", "Запуск Панели Управления...")

        self.title("Chat Control Panel")
        self.geometry("640x800")  # Increased height to accommodate the new layout
        ctk.set_appearance_mode("dark")  # Dark mode
        ctk.set_default_color_theme("green")  # Green accent

        self.selected_mic_index = microphone_index
        self.selected_platform = selected_platform
        self.selected_output_device_index = output_device_index

        self.image_generator = ImageGenerator(self)

        self.fancy_log("🔊 НАСТРОЙКИ ЗВУКА", f"Воспроизведение звука на устройстве с индексом: {self.selected_output_device_index}")
        self.fancy_log("🌐 НАСТРОЙКИ ПЛАТФОРМЫ", f"Используемые сервисы: {self.selected_platform}")
        self.fancy_log("🎙️ НАСТРОЙКИ МИКРОФОНА", f"Ввод звука на устройстве с индексом: {self.selected_mic_index}")


        self.folder_to_clear = self.resource_path('../Data/Output')
        self.protected_files = [
            self.resource_path('../Data/Output/voice.txt'),
            self.resource_path('../Data/Output/music.txt')
        ]
        self.delete_all_files_in_folder(self.folder_to_clear)
        self.fancy_log("🗑️ ОЧИСТКА ПАПКИ", f"Очистил папку: {self.folder_to_clear}")

        self.slider1_file = self.resource_path('../Data/Output/voice.txt')
        self.slider2_file = self.resource_path('../Data/Output/music.txt')

        self.after_id = None
        self.youtube_handler = None
        self.twitch_handler = None
        self.picker_thread = None
        self.monitor_thread = None
        self.handler_thread = None
        self.draw_queue = queue.Queue()  # Queue to manage !draw commands
        self.draw_thread = None  # Thread for processing draw commands
        self.processing = False  # To track if the thread is processing
        self.chloe_window_active = False
        self.hana_window_active = False
        self.mic_on_active = False  # Initialize the attribute
        self.stop_mic_processing = False  # Flag to stop mic processing
        self.last_spin_time = 0      # Initialize the last spin command time
        self.last_headpat_time = 0   # Initialize the last headpat command time
        self.random_picker_running = False
        self.monitor_file_running = False

        self.known_emotes = []

        # Resolve the base path for PyInstaller
        self.base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))

        self.spin_file = self.resource_path('../Data/Output/spin.txt')
        self.headpat_file = self.resource_path('../Data/Output/spin.txt')
        superchat_path = self.resource_path('../Data/Chat/Special/superchat.chloe')
        superviewer_path = self.resource_path('../Data/Chat/Special/superviewer.chloe')

        # Clear superchat.chloe file
        try:
            with open(superchat_path, 'w', encoding='utf-8') as superchat_file:
                superchat_file.write('')  # Empty the file content
            self.fancy_log("📂 ОЧИСТКА ФАЙЛА", f"Файл {superchat_path} успешно очищен.")
        except Exception as e:
            self.fancy_log("❌ ОШИБКА", f"Не удалось очистить файл {superchat_path}: {e}")

        # Clear superviewer.chloe file
        try:
            with open(superviewer_path, 'w', encoding='utf-8') as superviewer_file:
                superviewer_file.write('')  # Empty the file content
            self.fancy_log("📂 ОЧИСТКА ФАЙЛА", f"Файл {superviewer_path} успешно очищен.")
        except Exception as e:
            self.fancy_log("❌ ОШИБКА", f"Не удалось очистить файл {superviewer_path}: {e}")

        memory_file_path = self.resource_path('../Data/Input/memory.txt')

        # Clear memory.txt file
        try:
            with open(memory_file_path, 'w', encoding='utf-8') as memory_file:
                memory_file.write('')  # Empty the file content
            self.fancy_log("📂 ОЧИСТКА ФАЙЛА", f"Файл {memory_file_path} успешно очищен.")
        except Exception as e:
            self.fancy_log("❌ ОШИБКА", f"Не удалось очистить файл {memory_file_path}: {e}")

        # Initialize LLM model to None
        self.llm_model = None

        self.selected_llm = selected_llm

        # Load the selected LLM model if one is provided
        if self.selected_llm:
            self.fancy_log("🤖 МОДЕЛЬ LLM", f"Загрузка модели LLM из: {self.selected_llm}")
            self.llm_model = load_model(self.selected_llm)
            if self.llm_model:
                self.fancy_log("🤖 МОДЕЛЬ LLM", "Модель успешно загружена!")
            else:
                self.fancy_log("🤖 МОДЕЛЬ LLM", "Не удалось загрузить модель.")
        else:
            self.fancy_log("🤖 МОДЕЛЬ LLM", "Модель LLM не выбрана.")
        # Whisper model initialization
        self.fancy_log("🔈 WHISPER", "Загрузка большой модели Whisper...")
        self.whisper_model = whisper.load_model("large")
        self.fancy_log("🔈 WHISPER", "Большая модель Whisper загружена.")

        # Create a frame for the search bar at the top
        search_frame = ctk.CTkFrame(self)
        search_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        # Create the search bar (CTkEntry)
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Search...")
        self.search_entry.pack(fill="x", padx=10, pady=5)

        # Variables to manage the timing and last printed text
        self.last_printed_text = ""
        self.after_id = None  # This will store the ID of the scheduled after callback

        # Bind the search entry's key release event to handle input changes
        self.search_entry.bind("<KeyRelease>", self.on_search_change)

        self.fancy_log("🖥️ УСТРОЙСТВО ИНТЕРФЕЙСА", "Строка поиска и элементы ввода инициализированы.")

        # File paths (adjust these to match your directory structure)
        files = [
            self.resource_path('../Data/Chat/General/viewer1.hana'),
            self.resource_path('../Data/Chat/General/input1.hana'),
            self.resource_path('../Data/Chat/General/viewer2.hana'),
            self.resource_path('../Data/Chat/General/input2.hana'),
            self.resource_path('../Data/Chat/General/viewer3.hana'),
            self.resource_path('../Data/Chat/General/input3.hana')
        ]

        # Clear chat txt files
        for file_path in files:
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write('')  # Empty the file content
                self.fancy_log("📂 ОЧИСТКА ФАЙЛА", f"Файл {file_path} успешно очищен.")
            except Exception as e:
                self.fancy_log("❌ ОШИБКА", f"Не удалось очистить файл {file_path}: {e}")

        # Create text boxes in two columns
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        for i, file in enumerate(files):
            frame = TextBoxFrame(self, file)
            frame.grid(row=(i // 2) + 1, column=i % 2, padx=10, pady=10)  # Text boxes start at row 1

        self.fancy_log("🖥️ УСТРОЙСТВО ИНТЕРФЕЙСА", "Текстовые поля созданы.")

        # Adjust the button frame row placement to ensure it is below the text boxes
        button_frame = ctk.CTkFrame(self)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10, sticky="ew")  # Shifted to row 4 to account for the search bar and text boxes

        # Create and pack the buttons horizontally with corner-less style
        buttons = ["Hana Start", "Hana Stop", "Chloe Start", "Chloe Stop"]
        for i, button_text in enumerate(buttons):
            if button_text == "Hana Start":
                self.hana_start_button = ctk.CTkButton(button_frame, text=button_text, corner_radius=0, command=self.hana_start)
                self.hana_start_button.grid(row=0, column=i, padx=10, pady=5, sticky="ew")
            elif button_text == "Hana Stop":
                self.hana_stop_button = ctk.CTkButton(button_frame, text=button_text, corner_radius=0, command=self.hana_stop)
                self.hana_stop_button.grid(row=0, column=i, padx=10, pady=5, sticky="ew")
            elif button_text == "Chloe Start":
                self.chloe_start_button = ctk.CTkButton(button_frame, text=button_text, corner_radius=0, command=self.chloe_start)
                self.chloe_start_button.grid(row=0, column=i, padx=10, pady=5, sticky="ew")
            elif button_text == "Chloe Stop":
                self.chloe_stop_button = ctk.CTkButton(button_frame, text=button_text, corner_radius=0, command=self.chloe_stop)
                self.chloe_stop_button.grid(row=0, column=i, padx=10, pady=5, sticky="ew")


        self.fancy_log("🖥️ УСТАНОВКА ИНТЕРФЕЙСА", "Кнопки управления созданы.")

        # Adjust the lower frame row placement as well
        lower_frame = ctk.CTkFrame(self)
        lower_frame.grid(row=5, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")  # Shifted to row 5

        # Left frame (Switches, Sliders, Long Button)
        left_frame = ctk.CTkFrame(lower_frame)
        left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Configure empty columns to center the content horizontally
        left_frame.grid_columnconfigure(0, weight=1)  # Empty column on the left
        left_frame.grid_columnconfigure(5, weight=1)  # Empty column on the right

        # Define switches as attributes
        self.switch_en = ctk.CTkSwitch(left_frame, text="")
        self.switch_es = ctk.CTkSwitch(left_frame, text="")
        self.switch_ru = ctk.CTkSwitch(left_frame, text="")
        self.switch_jp = ctk.CTkSwitch(left_frame, text="")
        
        switches = [self.switch_en, self.switch_es, self.switch_ru, self.switch_jp]

        # Horizontal line of switches with labels
        switch_texts = ["EN", "ES", "RU", "JP"]
        for i, (switch, text) in enumerate(zip(switches, switch_texts)):
            switch.grid(row=0, column=i+1, pady=5, sticky="ew")
            label = ctk.CTkLabel(left_frame, text=text)
            label.grid(row=1, column=i+1, padx=5, sticky="n")

        # Create the sliders and bind them to a method to update the text files
        self.slider1 = ctk.CTkSlider(left_frame, from_=0, to=1, command=self.update_slider1_value)
        self.slider1.grid(row=2, column=1, columnspan=4, pady=5, sticky="ew")
        
        self.slider2 = ctk.CTkSlider(left_frame, from_=0, to=1, command=self.update_slider2_value)
        self.slider2.grid(row=3, column=1, columnspan=4, pady=5, sticky="ew")

        self.is_recording = threading.Event()  # Event to signal when recording is active

        # Long button
        self.long_button = ctk.CTkButton(left_frame, text="Mic On", corner_radius=0, command=self.toggle_mic)
        self.long_button.grid(row=4, column=1, columnspan=4, pady=10, sticky="ew")

        # Right frame (Stacked Buttons)
        right_frame = ctk.CTkFrame(lower_frame)
        right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        # Configure empty columns to center the content horizontally
        right_frame.grid_columnconfigure(0, weight=1)  # Empty column on the left
        right_frame.grid_columnconfigure(2, weight=1)  # Empty column on the right

        # Add empty rows above and below the buttons to center them vertically
        right_frame.grid_rowconfigure(0, weight=1)  # Empty row above
        right_frame.grid_rowconfigure(5, weight=1)  # Empty row below

        # Create and stack the four buttons vertically and fill the right side with custom text
        stacked_button_texts = ["Office", "Bedroom", "Station", "Beach"]
        for i, button_text in enumerate(stacked_button_texts):
            button = ctk.CTkButton(right_frame, text=button_text, corner_radius=0,
                                   command=lambda text=button_text: self.create_text_file(text))
            button.grid(row=i+1, column=1, pady=5, sticky="ew")
        # Configure lower frame to ensure proper stretching
        lower_frame.columnconfigure(0, weight=2)
        lower_frame.columnconfigure(1, weight=1)

        self.hana_window = None  # Reference to the HWindow
        self.chloe_window = None

        self.mod_names = ['Joykill']

        # Example button to open additional windows
        open_window1_button = ctk.CTkButton(self, text="Open Chloe Chatter", command=self.open_window1, corner_radius=0)
        open_window1_button.grid(row=6, column=0, padx=10, pady=10, sticky="ew")

        open_window2_button = ctk.CTkButton(self, text="Open Hana Chatter", command=self.open_window2, corner_radius=0)
        open_window2_button.grid(row=6, column=1, padx=10, pady=10, sticky="ew")

        self.monitor_processing = threading.Event()
        self.mic_start_flag = threading.Event()
        self.stop_random_picker = threading.Event()
        self.stop_monitor_file = threading.Event()
        self.mic_pause_event = threading.Event()
        self.pause_event = threading.Event()
        self.new_file_ready_event = threading.Event()

        self.protocol("WM_DELETE_WINDOW", self.on_main_window_close)

        self.fancy_log("⚙️ ИНИЦИАЛИЗАЦИЯ", "Панель управления полностью инициализирована.")

    def safe_after(self, delay, func, *args, **kwargs):
        """
        Schedule an after callback safely by wrapping it in a try-except block.
        This prevents callbacks from being called on destroyed widgets.
        """
        try:
            after_id = self.after(delay, lambda: self.safe_callback(func, *args, **kwargs))
            self.after_ids.append(after_id)  # Keep track of the callback ID
        except Exception as e:
            print(f"Error scheduling after callback: {e}")

    def safe_callback(self, func, *args, **kwargs):
        """
        Wrapper for callback functions to handle exceptions gracefully.
        """
        try:
            func(*args, **kwargs)
        except Exception as e:
            print(f"Error in after callback: {e}")

    def on_search_change(self, event):
        # Cancel any existing scheduled print function
        if self.after_id:
            self.after_cancel(self.after_id)

        # Get the current text from the search entry
        current_text = self.search_entry.get()

        # Schedule a new function to run after 2 seconds
        self.after_id = self.after(2000, mainrag, current_text)
        self.fancy_log("🔍 Поиск", f"Поиск обновлен на: {current_text}")
        
    def delete_all_files_in_folder(self, folder_path):
        """Delete all files in the specified folder."""
        try:
            # Check if the folder exists
            if not os.path.exists(folder_path):
                self.fancy_log("⚠️ Ошибка папки", f"Папка '{folder_path}' не существует.")
                return

            # List all files and directories in the folder
            for file_name in os.listdir(folder_path):
                file_path = os.path.join(folder_path, file_name)

                # Check if it's a file or directory
                if file_path not in self.protected_files and os.path.isfile(file_path):
                    # Delete the file
                    os.remove(file_path)
                    self.fancy_log("🗑️ Файл удален", f"Удален файл: {file_path}")
                elif os.path.isdir(file_path):
                    # Delete the directory and all its contents
                    shutil.rmtree(file_path)
                    self.fancy_log("🗑️ Папка удалена", f"Удалена папка: {file_path}")

            self.fancy_log("✅ Успех", f"Все файлы в папке '{folder_path}' были удалены.")

        except Exception as e:
            self.fancy_log("❌ Ошибка", f"Ошибка при удалении файлов: {e}")

    def update_slider1_value(self, value):
        """Update the value of slider 1 in the text file."""
        with open(self.slider1_file, 'w') as file:
                file.write(f"{value:.2f}")  # Write the slider value to the file

    def update_slider2_value(self, value):
        """Update the value of slider 2 in the text file."""
        with open(self.slider2_file, 'w') as file:
                file.write(f"{value:.2f}")  # Write the slider value to the file

    def create_text_file(self, button_text):
        """Function to create a text file based on the button clicked."""
        folder_path = self.resource_path('../Data/Output')  # Replace with the actual folder path
        file_contents = {
            "Office": "This is the Office file.",
            "Bedroom": "This is the Bedroom file.",
            "Station": "This is the Station file.",
            "Beach": "This is the Beach file."
        }

        file_name = os.path.join(folder_path, f"{button_text}.txt")

        try:
            # Write content to the file
            with open(file_name, "w", encoding='utf-8') as file:
                file.write(file_contents[button_text])

            # Show a confirmation message
            self.fancy_log("📝 Файл создан", f"{button_text}.txt был создан!")

        except Exception as e:
            # Show an error message if file creation fails
            self.fancy_log("❌ Ошибка", f"Не удалось создать файл: {str(e)}")

    def get_active_language(self):
        # Maps the switch to the language code
        switch_language_map = {
            self.switch_en: 'en',
            self.switch_es: 'es',
            self.switch_ru: 'ru',
            self.switch_jp: 'ja'
        }

        active_languages = [lang for switch, lang in switch_language_map.items() if switch.get()]

        if len(active_languages) == 1:
            return active_languages[0]
        else:
            return 'en'

    def toggle_mic(self):
        self.fancy_log("🎤 Переключение микрофона", "toggle_mic вызван")
        self.fancy_log("🎤 Состояние микрофона", f"Активный: {self.is_recording.is_set()}")

        if not self.is_recording.is_set():
            # Pause random_picker and set the recording flag
            self.mic_pause_event.set()
            self.is_recording.set()

            # Start the recording loop in a new thread to avoid blocking the UI
            self.mic_thread = threading.Thread(target=self.start_recording_loop, daemon=True)
            self.mic_thread.start()

        else:
            # Stop the recording
            self.is_recording.clear()
            self.stop_recording_loop()

            # Ensure the recording thread finishes before resuming random_picker
            if self.mic_thread and self.mic_thread.is_alive():
                self.mic_thread.join()  # Wait for the mic logic to complete

            # Resume random_picker
            self.mic_pause_event.clear()

    def start_recording_loop(self):
        self.fancy_log("🎤 Ожидание разрешения", "Ожидание начала записи с микрофона...")

        # Run in a non-blocking loop to avoid freezing
        while not self.mic_start_flag.is_set():
            if not self.is_recording.is_set():
                return  # Exit if recording is stopped
            time.sleep(0.1)  # Small delay to avoid CPU overuse

        self.fancy_log("🎤 Разрешение получено", "Инициализация записи...")
        self.record_and_process_audio()

    def stop_recording_loop(self):
        self.fancy_log("🎤 Остановка записи", "Завершение записи...")

        self.stop_mic_processing = True
        self.is_recording.clear()

        # Wait for mic thread to finish without blocking the UI
        if self.mic_thread and self.mic_thread.is_alive():
            self.fancy_log("⌛ Ожидание завершения", "Ожидание завершения потока...")
            self.mic_thread.join(timeout=5)  # Timeout to avoid indefinite wait

    def record_and_process_audio(self):
        while self.is_recording.is_set():  # Keep recording as long as the mic is on
            # 1. Record audio from the microphone
            output_audio_path = self.resource_path('../Assets/Audio/user.wav')  # Adjust path as needed
            self.fancy_log("🎤 Запись аудио", "Запись аудио с микрофона...")
            record_audio(output_file=output_audio_path, mic_index=1, sample_rate=48000, chunk_size=1024, max_record_seconds=300)

            # 2. Transcribe the recorded audio using Whisper
            self.fancy_log("💬 Транскрибирование аудио", "Используя Whisper для транскрибирования аудио...")
            transcription = self.whisper_transcribe(output_audio_path)

            # 3. Translate the transcription based on the active language switch
            active_language = self.get_active_language()
            self.fancy_log("🌍 Перевод транскрипции", f"Переводим транскрипцию на {active_language}...")
            translated_text = translate(transcription, active_language)

            # 4. Save the translated transcript to a .hana file
            transcript_file_path = self.resource_path('../Data/Output/translated.hana')  # Adjust path as needed
            try:
                with open(transcript_file_path, 'w', encoding='utf-8') as hana_file:
                    hana_file.write(translated_text)
                self.fancy_log("💾 Транскрипт сохранён", f"Переведённый транскрипт сохранён по адресу {transcript_file_path}.")
            except Exception as e:
                self.fancy_log("❌ Ошибка", f"Ошибка при сохранении транскрипта: {e}")

            # 5. Use TTS to generate a response based on the translation
            self.fancy_log("🗣️ Генерация аудио", "Генерируем аудиовыход с помощью TTS...")
            tts_function = self.get_active_tts_function()
            if tts_function:
                ai_output_path = self.resource_path('../Assets/Audio/ai.wav')  # Adjust path as needed
                try:
                    tts_function(translated_text, output_path=ai_output_path)
                    self.fancy_log("🔊 Аудио TTS сохранено", f"Аудио TTS сохранено по адресу {ai_output_path}.")
                except Exception as e:
                    self.fancy_log("❌ Ошибка", f"Ошибка при генерации TTS аудио: {e}")
                    return  # Skip further processing if TTS fails

                # 6. Process the audio using mainrvc and play the output
                hana_output_path = self.resource_path('../Assets/Audio/hana.wav')  # Adjust path as needed
                try:
                    self.fancy_log("🎶 Обработка аудио", "Обработка аудио с помощью mainrvc...")
                    mainrvc(ai_output_path, hana_output_path)
                    self.fancy_log("💽 Обработанное аудио сохранено", f"Обработанное аудио сохранено по адресу {hana_output_path}.")
                except Exception as e:
                    self.fancy_log("❌ Ошибка", f"Ошибка при обработке аудио с помощью mainrvc: {e}")
                    return  # Skip playback if processing fails

                try:
                    self.fancy_log("▶️ Воспроизведение аудио", "Воспроизводим обработанное аудио...")
                    play(hana_output_path, self.selected_output_device_index)
                    self.fancy_log("✅ Воспроизведение завершено", "Воспроизведение аудио завершено.")
                except Exception as e:
                    self.fancy_log("❌ Ошибка", f"Ошибка при воспроизведении аудио: {e}", width=100)
            else:
                self.fancy_log("❌ Ошибка", "Нет активной функции TTS. Невозможно сгенерировать аудиовыход.")

            # Optional sleep or other logic
            time.sleep(3)

            # Check if the recording is stopped to exit the loop
            if not self.is_recording.is_set():
                break

    def whisper_transcribe(self, audio_path):
        # Use the loaded Whisper model to transcribe the audio file
        try:
            result = self.whisper_model.transcribe(audio_path)
            transcription = result['text']
            self.fancy_log("✅ Результат транскрипции", f"Результат транскрипции: {transcription}")
            return transcription
        except Exception as e:
            self.fancy_log("❌ Ошибка", f"Ошибка во время транскрипции: {e}")
            return ""

    def get_active_tts_function(self):
        for switch, tts_func in zip([self.switch_en, self.switch_es, self.switch_ru, self.switch_jp],
                                    [tts_en, tts_es, tts_ru, tts_ja]):
            if switch.get():
                return tts_func
        # Default to English TTS if no other switch is active
        return tts_en

    def hana_start(self):

        if self.random_picker_running:
            self.fancy_log("ℹ️ Информация", "random_picker уже запущен.")
            return

        self.hana_start_button.configure(state="normal", fg_color="grey")

        # Start chat handlers based on the selected platform
        if self.selected_platform == "Youtube":
            self.handler_thread = threading.Thread(target=self.start_youtube_chat, daemon=True)
            self.handler_thread.start()
        elif self.selected_platform == "Twitch":
            self.handler_thread = threading.Thread(target=self.start_twitch_chat, daemon=True)
            self.handler_thread.start()
        elif self.selected_platform == "Both":
            self.handler_thread = threading.Thread(target=self.start_alternating_handlers, daemon=True)
            self.handler_thread.start()
        else:
            self.fancy_log("❌ Ошибка", "Не запущен обработчик чата (не выбрано).")

        # Start random picker
        self.stop_random_picker.clear()  # Clear the stop event before starting
        self.picker_thread = threading.Thread(target=self.random_picker, daemon=True)
        self.picker_thread.start()
        self.random_picker_running = True
        self.fancy_log("▶️ Hana Запущен", "random_picker запущен.")

    
    def hana_stop(self):
        if not self.random_picker_running:
            self.fancy_log("ℹ️ Информация", "random_picker уже остановлен.")
            return

        self.hana_start_button.configure(state="normal", fg_color="#2FA572")

        # Stop the random picker thread
        self.stop_random_picker.set()  # Signal the picker thread to stop
        self.random_picker_running = False
        self.fancy_log("⏹️ Случайный выбор", "Случайный выбор остановлен. Обработчики чата продолжают работать.")
    

    def chloe_start(self):
        if self.monitor_file_running:
            self.fancy_log("ℹ️ Информация", "monitor_file уже запущен.")
            return

        self.chloe_start_button.configure(state="normal", fg_color="grey")

        # Clear any stop signals and start the monitoring thread
        self.stop_monitor_file.clear()  # Clear the stop event (make sure it's not set)
        self.pause_event.clear()        # Ensure the pause event is clear
        self.new_file_ready_event.clear()
        self.monitor_thread = threading.Thread(target=self.monitor_file, daemon=True)
        self.monitor_thread.start()     # Start the monitoring thread
        self.monitor_file_running = True
        self.fancy_log("📡 Chloe AI", "Мониторинг Chloe AI запущен")

    def chloe_stop(self):
        if not self.monitor_file_running:
            self.fancy_log("ℹ️ Информация", "monitor_file уже остановлен.")
            return
        
        self.chloe_start_button.configure(state="normal", fg_color="#2FA572")

        # Set the stop signal and clear any pause event to ensure the monitor stops cleanly
        self.stop_monitor_file.set()  # Signal to stop the monitoring thread
        self.new_file_ready_event.set()  # Unblock monitor if waiting
        self.pause_event.clear()      # Ensure the pause event is clear
        self.monitor_file_running = False
        self.fancy_log("📡 Chloe AI", "Остановка мониторинга Chloe AI")

    def start_youtube_chat(self):
        load_dotenv()
        video_id = os.getenv('Video-Url')
        self.youtube_handler = YouTubeChatHandler(video_id, self.mod_names)
        self.youtube_handler.start()

    def start_twitch_chat(self):
        load_dotenv()
        token = os.getenv('Twitch-Token')
        client_id = os.getenv('Twitch-Client-ID')
        nick = os.getenv('Twitch-Nick')
        prefix = os.getenv('Twitch-Prefix')
        initial_channels = [os.getenv('Twitch-Channel')]
        self.twitch_handler = TwitchChatHandler(token=token, client_id=client_id, nick=nick, prefix=prefix, initial_channels=initial_channels, mod_names=self.mod_names)
        self.twitch_handler.run()

    def is_valid_utf8(self, text):
        """Check if the text can be properly decoded as UTF-8."""
        try:
            text.encode('utf-8').decode('utf-8')  # Attempt to encode and decode
            return True
        except UnicodeDecodeError as e:
            logging.error(f"Unicode decode error: {e}. Problematic text: {text}")
            return False

    def start_alternating_handlers(self):
        load_dotenv()
        video_id = os.getenv('Video-Url')
        yt_mods = []
        token = os.getenv('Twitch-Token')
        client_id = os.getenv('Twitch-Client-ID')
        nick = os.getenv('Twitch-Nick')
        prefix = os.getenv('Twitch-Prefix')
        initial_channels = [os.getenv('Twitch-Channel')]
        tt_mods = []
        self.youtube_handler = YouTubeChatHandler(video_id, yt_mods)
        self.twitch_handler = TwitchChatHandler(token=token, client_id=client_id, nick=nick, prefix=prefix, initial_channels=initial_channels, mod_names=tt_mods)

        def alternate_handlers():
            if not hasattr(self, 'current_handler') or self.current_handler == "Twitch":
                if self.twitch_handler:
                    self.twitch_handler.stop()
                self.youtube_handler.start()
                self.current_handler = "Youtube"
            else:
                if self.youtube_handler:
                    self.youtube_handler.stop()
                self.twitch_handler.start()
                self.current_handler = "Twitch"

            self.after_id = self.after(10000, alternate_handlers)

        alternate_handlers()

    def contains_emoji_or_emote(self, text):
        """Check if the text contains any emojis or known livestream emotes."""
        
        # Check for standard emojis using emoji library
        if any(char in emoji.EMOJI_DATA for char in text):
            return True
        
        # Check for text inside colons (e.g., :example:) using regex
        if re.search(r':[^:\s]+:', text):
            return True

        # Check for known text-based emotes
        for emote in self.known_emotes:
            if emote in text:
                return True

        return False
    
    def random_picker(self):
        input_files = [
            self.resource_path('../Data/Chat/General/input1.hana'),
            self.resource_path('../Data/Chat/General/input2.hana'),
            self.resource_path('../Data/Chat/General/input3.hana')
        ]
        viewer_files = [
            self.resource_path('../Data/Chat/General/viewer1.hana'),
            self.resource_path('../Data/Chat/General/viewer2.hana'),
            self.resource_path('../Data/Chat/General/viewer3.hana')
        ]

        predefined_inputs = [
            "Talk about humans or your life",
            "Say something controversial",
            "Make a hot take. (topic is your choice).",
            "Say something that involves you swearing.",
            "Change subject to anime.",
            "Change subject to the economy.",
            "Change subject to politics.",
            "Change subject to guns.",
        ]

        mod_file = self.resource_path('../Data/Chat/Special/moderator.hana')
        message_file = self.resource_path('../Data/Chat/Special/modmessage.hana')

        self.cycle_active = False  # Tracks if we are in the predefined-input cycle
        self.predefined_input_flag = False  # Tracks if predefined input was chosen
        output_chloe_path = self.resource_path('../Data/Output/output.chloe')  # Monitor file output
        superchat_path = self.resource_path('../Data/Chat/Special/superchat.chloe')  # Path for superchat
        last_superchat_content = None  # Track last processed superchat content

        last_formatted_string = None  # Initialize the variable

        while not self.stop_random_picker.is_set():  # Check if the stop event is set
            if self.mic_pause_event.is_set():
                self.fancy_log("⏸️ Пауза", "random_picker приостановлен для записи с микрофона.")

                # Set mic_start_flag to signal that recording can start
                self.mic_start_flag.set()

                # Wait until the pause_event is cleared before continuing
                while self.mic_pause_event.is_set():
                    time.sleep(0.1)

                # Clear the mic_start_flag when random_picker resumes
                self.mic_start_flag.clear()
                self.fancy_log("▶️ Возобновление", "random_picker возобновлен.")

            # Check if superchat.chloe has content
            if os.path.exists(superchat_path):
                with open(superchat_path, 'r', encoding='utf-8') as superchat_file:
                    superchat_content = superchat_file.read().strip()

                if superchat_content and superchat_content != last_superchat_content:
                    # New content detected in superchat.chloe
                    last_superchat_content = superchat_content

                    if self.monitor_file_running:   
                        self.fancy_log("🔔 СУПЕРЧАТ ДЕТЕКТИРОВАН", "Обнаружено новое содержимое в superchat.chloe! Приостановка random_picker для monitor_file.")
                        self.pause_event.set()  # Pause random_picker
                        self.new_file_ready_event.set()  # Notify monitor_file
                    time.sleep(5)
                    continue

            if self.pause_event.is_set():
                self.fancy_log("⏸️  ОБРАБОТКА", "Выбор случайного значения приостановлен для обработки Chloe AI...")
                while self.pause_event.is_set() and not self.stop_random_picker.is_set():
                    time.sleep(1)

            if self.cycle_active:
                # Inside the cycle: 50/50 between monitor_file output or viewer input
                if random.choice([True, False]) and os.path.exists(output_chloe_path):
                    # Use monitor_file output
                    with open(output_chloe_path, 'r', encoding='utf-8') as file:
                        input_text = file.read().strip()
                    viewer_text = "Chloe Hayashi"  # Label for AI-generated output
                    self.predefined_input_flag = True  # Set flag for monitor_file to handle it again
                else:
                    index = random.randint(0, 2)

                    # Open the input files with UTF-8 encoding
                    with open(input_files[index], 'r', encoding='utf-8') as infile:
                        input_text = infile.read().strip()

                    # Open the viewer files with UTF-8 encoding
                    with open(viewer_files[index], 'r', encoding='utf-8') as viewerfile:
                        viewer_text = viewerfile.read().strip()


                    # Check if the modviewer file has content
                    with open(mod_file, 'r', encoding='utf-8') as modviewer_infile:
                        modviewer_content = modviewer_infile.read().strip()

                    if modviewer_content:  # If content exists in modviewer
                        self.fancy_log("🔍 Модератор обнаружен", f"Модератор {viewer_text} обнаружен, используется специальный ввод.")
                            
                        # Save content of moderator and message files
                        with open(mod_file, 'r', encoding='utf-8') as mod_infile:
                            viewer_text = mod_infile.read().strip()  # Save moderator file content to viewer_text

                        with open(message_file, 'r', encoding='utf-8') as message_infile:
                            input_text = message_infile.read().strip()  # Save message file content to input_text
                            
                        # Now clear the contents of both modmessage and moderator files
                        with open(mod_file, 'w', encoding='utf-8') as mod_infile:
                            mod_infile.write("")  # Clear the content

                        with open(message_file, 'w', encoding='utf-8') as message_infile:
                            message_infile.write("")  # Clear the content

                    # Before processing the input_text, validate if it's a proper UTF-8 string
                    if not self.is_valid_utf8(input_text):
                        self.fancy_log("⚠️ НЕДОПУСТИМАЯ UTF-8", f"Пропуск недопустимого UTF-8 ввода: '{input_text}'")
                        continue  # Skip this iteration if the input text has encoding issues

                    if not input_text or input_text.startswith('!') or self.contains_emoji_or_emote(input_text):
                        self.fancy_log("⚠️ НЕДОПУСТИМЫЙ ВВОД", f"Пропуск недопустимого или пустого ввода: '{input_text}'")

                        # Now call handle_command if it starts with '!'
                        if input_text.startswith('!'):
                            self.fancy_log("🛠️ КОМАНДА", f"Обнаружена команда: {input_text}")
                            self.handle_command(input_text)

                        time.sleep(5)
                        continue

                    self.cycle_active = False  # Exit the cycle

            else:
                # Not in the cycle: Pick between predefined input or viewer input
                if random.choice([True, False]) and self.monitor_file_running:
                    # Pick a predefined input
                    input_text = random.choice(predefined_inputs)
                    viewer_text = "User"
                    self.predefined_input_flag = True
                    self.cycle_active = True  # Start the cycle
                    self.fancy_log("🎲 СЛУЧАЙНЫЙ ВЫБОР", f"Выбран предопределенный ввод: '{input_text}'")
                else:
                    index = random.randint(0, 2)

                    # Open the input files with UTF-8 encoding
                    with open(input_files[index], 'r', encoding='utf-8') as infile:
                        input_text = infile.read().strip()

                    # Open the viewer files with UTF-8 encoding
                    with open(viewer_files[index], 'r', encoding='utf-8') as viewerfile:
                        viewer_text = viewerfile.read().strip()

                    # Check if the modviewer file has content
                    with open(mod_file, 'r', encoding='utf-8') as modviewer_infile:
                        modviewer_content = modviewer_infile.read().strip()

                    if modviewer_content:  # If content exists in modviewer
                        self.fancy_log("🔍 Модератор обнаружен", f"Модератор {viewer_text} обнаружен, используется специальный ввод.")
                            
                        # Save content of moderator and message files
                        with open(mod_file, 'r', encoding='utf-8') as mod_infile:
                            viewer_text = mod_infile.read().strip()  # Save moderator file content to viewer_text

                        with open(message_file, 'r', encoding='utf-8') as message_infile:
                            input_text = message_infile.read().strip()  # Save message file content to input_text
                            
                        # Now clear the contents of both modmessage and moderator files
                        with open(mod_file, 'w', encoding='utf-8') as mod_infile:
                            mod_infile.write("")  # Clear the content

                        with open(message_file, 'w', encoding='utf-8') as message_infile:
                            message_infile.write("")  # Clear the content

                    # Before processing the input_text, validate if it's a proper UTF-8 string
                    if not self.is_valid_utf8(input_text):
                        self.fancy_log("⚠️ НЕДОПУСТИМАЯ UTF-8", f"Пропуск недопустимого UTF-8 ввода: '{input_text}'")
                        continue  # Skip this iteration if the input text has encoding issues

                    if not input_text or input_text.startswith('!') or self.contains_emoji_or_emote(input_text):
                        self.fancy_log("⚠️ НЕДОПУСТИМЫЙ ВВОД", f"Пропуск недопустимого или пустого ввода: '{input_text}'")

                        # Now call handle_command if it starts with '!'
                        if input_text.startswith('!'):
                            self.fancy_log("🛠️ КОМАНДА", f"Обнаружена команда: {input_text}")
                            self.handle_command(input_text)

                        time.sleep(5)
                        continue

            # Check if any language switches are toggled on
            any_switch_toggled = any([self.switch_en.get(), self.switch_es.get(), self.switch_ru.get(), self.switch_jp.get()])

            # If any switch is toggled, translate the text; otherwise, skip translation
            if any_switch_toggled:
                target_language = self.get_active_language()
                if target_language:
                    input_text = translate(input_text, target_language)
                    self.fancy_log("🌍 ПЕРЕВОД", f"Переведен ввод на {target_language}: '{input_text}'")

            formatted_string = f"System: {viewer_text} said: {input_text}"

            # Check if the current message is the same as the last one
            if formatted_string != last_formatted_string:

                # Update HWindow if it's open
                if self.hana_window and isinstance(self.hana_window, HWindow):
                    self.hana_window.update_textbox(formatted_string)

                # Process the formatted string with hana_ai
                processed_string = hana_ai(formatted_string, self.llm_model)

                last_formatted_string = processed_string

                # Write the processed string to a text file
                output_file_path = self.resource_path('../Data/Output/output.hana')
                with open(output_file_path, 'w', encoding='utf-8') as outfile:
                    outfile.write(processed_string)
                self.fancy_log("💾 ВЫВОД ССОХРАНЕН", "Обработанная строка сохранена в output.hana")

                # Select the TTS function based on the active language switch or default to English
                tts_function = self.get_active_tts_function() if any_switch_toggled else tts_en

                if tts_function:
                    # Generate the audio file using the selected TTS function
                    ai_output_path = self.resource_path('../Assets/Audio/ai.wav')
                    tts_function(processed_string, output_path=ai_output_path)

                    # Process the audio file with mainrvc and save as hana.wav
                    hana_output_path = self.resource_path('../Assets/Audio/hana.wav')
                    mainrvc(ai_output_path, hana_output_path)

                    if os.getenv('Avatar-On') == 'True':
                        with open(self.resource_path("../Data/Output/hana.txt"), "w", encoding='utf-8') as file:
                            file.write("Аудио готово")
                    else:
                        play(hana_output_path, self.selected_output_device_index)

                    # **Clear the HWindow text after hana.wav is created**
                    if self.hana_window and isinstance(self.hana_window, HWindow):
                        self.hana_window.update_textbox("")  # Clear the text

                    # Notify monitor_file that a new file is ready
                    if self.predefined_input_flag:
                        self.fancy_log("🔄 МОНИТОР ФАЙЛ", "Запуск monitor_file после предопределенного ввода.")
                        self.new_file_ready_event.set()
                        self.predefined_input_flag = False

                    time.sleep(3)

                    # Play the generated hana.wav file
                    # play(hana_output_path, self.selected_output_device_index)
                else:
                    self.fancy_log("⚠️ ОШИБКА", "Нет активной функции TTS. Невозможно сгенерировать аудио.")
                    continue  # Skip if no TTS function is available
            else:
                self.fancy_log("🔁 ОБНАРУЖЕН ДУБЛИКАТ", "Пропуск повторяющегося текста ввода.")

            time.sleep(5)

        self.fancy_log("🛑 ВЫХОД", "Выход из потока случайного выбора.")

        
    def monitor_file(self):
        chloe_file_path = self.resource_path('../Data/Output/output.hana')
        log_file_path = self.resource_path('../Data/Output/output.chloe')
        superchat_path = self.resource_path('../Data/Chat/Special/superchat.chloe')
        superviewer_path = self.resource_path('../Data/Chat/Special/superviewer.chloe')

        while not os.path.exists(chloe_file_path) and not self.stop_monitor_file.is_set():
            time.sleep(1)

        while not self.stop_monitor_file.is_set():
            while not self.new_file_ready_event.is_set():
                time.sleep(1)

            if self.stop_monitor_file.is_set():
                self.fancy_log("🛑 МОНИТОР", "Остановка monitor_file, так как установлен сигнал остановки.")
                break

            self.fancy_log("⏸️ ПАУЗА", "Приостановка random_picker...")
            self.pause_event.set()

            try:
                # Check if superchat.chloe exists and has content
                superchat_used = False

                if os.path.exists(superchat_path):
                    with open(superchat_path, 'r', encoding='utf-8') as superchat_file:
                        chloe_text = superchat_file.read().strip()

                    # If superchat is valid, try to get the viewer from superviewer.chloe
                    if chloe_text:
                        with open(superviewer_path, 'r', encoding='utf-8') as superviewer_file:
                            viewer = superviewer_file.read().strip() or "Unknown Viewer"
                        superchat_used = True
                    else:
                        # If superchat.chloe is empty, fallback to default handling
                        chloe_text = None

                # Fallback logic: If superchat is not found or empty, use default chloe_file_path
                if not chloe_text:
                    with open(chloe_file_path, 'r', encoding='utf-8') as file:
                        chloe_text = file.read().strip()
                    viewer = "Hana Busujima"  # Default viewer for fallback case

                if chloe_text:
                    raw_chloe_text = f"System: {viewer} said: {chloe_text}"

                    if self.chloe_window and isinstance(self.chloe_window, CWindow):
                        self.chloe_window.update_textbox(raw_chloe_text)
                    # Superchat-specific prompt or regular AI prompt
                    if superchat_used:
                        processed_chloe_text = f"Thank you {viewer} for the superchat {chloe_ai(raw_chloe_text, self.llm_model)}"
                    else:
                        processed_chloe_text = chloe_ai(raw_chloe_text, self.llm_model)

                    with open(log_file_path, 'w', encoding='utf-8') as file:
                        file.write(f"{processed_chloe_text}\n")

                    tts_function = self.get_active_tts_function()
                    if tts_function:
                        ai_output_path = self.resource_path('../Assets/Audio/ai.wav')
                        tts_function(processed_chloe_text, output_path=ai_output_path)

                        distorted_output_path = self.resource_path('../Assets/Audio/chloe.wav')
                        static_file_path = self.resource_path('../Assets/Audio/radio.mp3')
                        distort(ai_output_path, static_file_path, output_file_path=distorted_output_path)

                        with open(superchat_path, 'w', encoding='utf-8') as superchat_file:
                            superchat_file.write('')  # Empty the file content after use

                        with open(superviewer_path, 'w', encoding='utf-8') as superviewer_file:
                            superviewer_file.write('')  # Empty the file content after use

                        if os.getenv('Avatar-On') == 'True':
                            with open(self.resource_path("../Data/Output/chloe.txt"), "w", encoding='utf-8') as file:
                                file.write("Аудио готово")
                        else:
                            play(distorted_output_path, self.selected_output_device_index)

                        if self.chloe_window and isinstance(self.chloe_window, CWindow):
                            self.chloe_window.update_textbox("")  # Clear the text

                        self.fancy_log("🎧 АУДИО", f"Сгенерированное искаженное аудио для Хлои: {distorted_output_path}")
                    else:
                        self.fancy_log("⚠️ ПРЕДУПРЕЖДЕНИЕ", "Нет активной функции TTS. Пропуск генерации аудио.")

                    # Signal to random_picker that the cycle can continue
                    self.new_file_ready_event.set()
                else:
                    self.fancy_log("📝 ПУСТОЙ ФАЙЛ", f"Файл {chloe_file_path} был пустым, пропуск обработки.")
            except Exception as e:
                self.fancy_log("❌ ОШИБКА", f"Ошибка при обработке файла Chloe: {str(e)}", width=100)
            finally:
                self.fancy_log("▶️ ПРОДОЛЖИТЬ", "Возобновление random_picker...")
                self.pause_event.clear()
                self.new_file_ready_event.clear()

            time.sleep(5)

        self.fancy_log("🔚 ВЫХОД", "Выход из потока monitor_file.")

    def handle_command(self, command):
        """
        General handler for commands starting with '!'.
        """
        self.fancy_log("🛠️ КОМАНДА", f"Обработка команды: {command}")

        # Handle the !draw command only if Art-On is set to True
        if command.startswith('!draw'):
            # Check if Art-On environment variable is set to "True"
            if os.getenv('Art-On') == 'True':
                self.handle_draw_command(command)
            else:
                self.fancy_log("🎨 РЕЖИМ ИСКУССТВА", "Art-On отключен, игнорирование команды !draw.")

        if command.startswith('!spin'):
            current_time = time.time()  # Get the current time in seconds
            time_since_last_spin = current_time - self.last_spin_time

            if time_since_last_spin >= 300:  # Check if 5 minutes (300 seconds) have passed
                # Create spin.txt file
                with open(self.spin_file, 'w', encoding='utf-8') as f:
                    f.write('This is the spin.txt file.')
                self.last_spin_time = current_time  # Update the last spin command time
                self.fancy_log("🔄 ВРАЩЕНИЕ", "Создан файл spin.txt")
            else:
                # Ignore command and log the cooldown message
                remaining_time = 300 - time_since_last_spin
                self.fancy_log("⏳ ОЖИДАНИЕ", f"Команда !spin игнорируется. Подождите {int(remaining_time)} секунд.")

        elif command.startswith('!headpat'):
            current_time = time.time()  # Get the current time in seconds
            time_since_last_headpat = current_time - self.last_headpat_time

            if time_since_last_headpat >= 30:  # Check if 30 seconds have passed
                # Create pat.txt file
                with open(self.headpat_file, 'w', encoding='utf-8') as f:
                    f.write('This is the pat.txt file.')
                self.last_headpat_time = current_time  # Update the last headpat command time
                self.fancy_log("🤚 ПАТ", "Создан файл pat.txt")
            else:
                # Ignore command and log the cooldown message
                remaining_time = 30 - time_since_last_headpat
                self.fancy_log("⏳ ОЖИДАНИЕ", f"Команда !headpat игнорируется. Подождите {int(remaining_time)} секунд.")

        else:
            self.fancy_log("❓ НЕИЗВЕСТНО", f"Получена неизвестная команда: {command}")

    def handle_draw_command(self, command):
        # Strip !draw from the command
        command_text = command.lstrip('!draw').strip()
        self.fancy_log("✏️ ДЕТЕКТИРОВАНА КОМАНДА", f"Обнаружена команда !draw: {command_text}")

        # Add the command to the draw queue
        self.draw_queue.put(command_text)

        # Start the processing thread if not already running
        if not self.processing:
            self.processing = True
            self.draw_thread = threading.Thread(target=self.process_draw_commands)
            self.draw_thread.start()

    def process_draw_commands(self):
        """Thread function to process draw commands sequentially."""
        while True:
            try:
                # Get the next item from the queue, block if empty
                input_text = self.draw_queue.get(block=True)

                if input_text is None:
                    # Special case to exit the thread
                    break

                # Strip !draw from the input text
                input_text = input_text.replace("!draw", "").strip()

                # Correctly pass a single-element tuple for args
                trigger_thread = threading.Thread(
                    target=self.image_generator.generate_image_thread,
                    args=(input_text,),  # Note the comma here
                    daemon=True
                )
                trigger_thread.start()

                self.draw_queue.task_done()  # Mark the task as done
                self.fancy_log("✅ ЗАВЕРШЕНО", f"Завершена обработка команды рисования: {input_text}")

            except Exception as e:
                self.fancy_log("❌ ОШИБКА", f"Ошибка при обработке команды рисования: {e}")
            
            # If the queue is empty, finish processing
            if self.draw_queue.empty():
                self.fancy_log("🔚 ЗАВЕРШЕНИЕ", "Больше нет команд рисования. Выход из потока рисования.")
                self.processing = False
                break

    def resource_path(self, relative_path):
        """ Get the absolute path to the resource, works for dev and for PyInstaller """
        try:
            # If using PyInstaller, sys._MEIPASS will be set to the temporary folder where files are extracted
            base_path = sys._MEIPASS
        except AttributeError:
            # Otherwise, use the current directory
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def calculate_display_width(self, text):
        """Calculate the display width of a string, accounting for wide characters."""
        return sum(2 if unicodedata.east_asian_width(char) in 'WF' else 1 for char in text)

    def fancy_log(self, header, body, width=150):
        # Validate and convert width to integer
        if not isinstance(width, int):
            try:
                width = int(width)
            except ValueError:
                raise TypeError("Width must be an integer.")

        # Get the current timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Prepare colors
        header_color = "\033[1;36m"  # Bright Cyan for header
        body_color = "\033[0;32m"    # Green for body
        reset_color = "\033[0m"      # Reset color

        # Prepare the log message header
        log_header = f"{timestamp} | INFO | {header_color}{header}{reset_color} :: "
        header_width = self.calculate_display_width(log_header)

        # Calculate total width available for the body
        total_width = width - header_width - 3  # 3 for the " |"
        
        # Truncate the body if it's too long
        if len(body) > total_width:
            body = body[:total_width - len("...{скрытый}")].rstrip() + "...{скрытый}"

        # Apply the body color and generate the log output
        log_output = f"{log_header}{body_color}{body}{reset_color}".ljust(width)

        # Print the formatted log
        print("=" * (width - 1) + "=")
        print(log_output)
        print("=" * (width - 1) + "=")
        print()  # Print a new line after the log entry

    def clear_last_lines(self, n=4):
        # ANSI escape sequence for moving the cursor up and clearing the line
        # \033[A moves the cursor up
        # \033[K clears the line
        for _ in range(n):
            sys.stdout.write('\033[A')  # Move cursor up one line
            sys.stdout.write('\033[K')  # Clear the line
        sys.stdout.flush()

    def open_window1(self):
        self.chloe_window = CWindow()
        self.chloe_window.mainloop()

    def open_window2(self):
        self.hana_window = HWindow(self)  # Pass the reference of App to HWindow
        self.hana_window.mainloop()

    def on_main_window_close(self):
        """Cancel all after callbacks and gracefully close the window."""
        # Cancel all scheduled after callbacks
        for after_id in self.after_ids:
            try:
                self.after_cancel(after_id)
            except Exception as e:
                print(f"Error canceling after callback {after_id}: {e}")
        self.after_ids.clear()  # Clear the list after canceling

        # Perform other cleanup operations as needed
        self.stop_random_picker.set()  # Stop picker if running
        self.monitor_processing.set()  # Stop any monitoring

        # Finally, destroy the window
        self.destroy()

    def destroy(self):
        if self.after_id is not None:
            self.after_cancel(self.after_id)
        super().destroy()