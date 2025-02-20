import os
import sys
import time
import tkinter as tk
import customtkinter as ctk
import random
import threading
import whisper
import logging
import emoji
import shutil
import queue
import re
import json
import unicodedata
import sounddevice as sd
import numpy as np
import wavio
from datetime import datetime
from dotenv import load_dotenv
from chloe import CWindow
from hana import HWindow
from hana import Ranting
from hana import Reading
from hana import hana_ai
from auto import emotion
from chloe import chloe_ai
from chloe import ImageGenerator
from chat import YouTubeChatHandler
from chat import TwitchChatHandler
from chat import AutoChatHandler
from audio import translate
from audio import record_audio
from audio import distort
from audio import normalize
from audio import tts_en
from audio import tts_es
from audio import tts_ja
from audio import tts_ru
from audio import tts
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

class Stream(ctk.CTk):
    def __init__(self, microphone_index=None, output_device_index=None, selected_platform="None", selected_llm=None):
        super().__init__()

        self.clear_last_lines()
        self.after_ids = []
        self.fancy_log("⚙️ ИНИЦИАЛИЗАЦИЯ", "Запуск Панели Управления...")

        self.title("Stream Control Panel")
        self.geometry("640x800")  # Increased height to accommodate the new layout
        ctk.set_appearance_mode("dark")  # Dark mode
        ctk.set_default_color_theme("green")  # Green accent

        self.attributes("-topmost", True)
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
        self.chat_handler = AutoChatHandler(input_text="")

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


        self.blacklist = []
        self.open_output_window()
        self.simulate_chat()

        self.protocol("WM_DELETE_WINDOW", self.on_main_window_close)

        self.fancy_log("⚙️ ИНИЦИАЛИЗАЦИЯ", "Панель управления полностью инициализирована.")

    def open_output_window(self):
        self.blacklist_window = ctk.CTkToplevel(self)
        self.blacklist_window.title("Output Control Panel")
        self.blacklist_window.geometry("400x250")
        self.blacklist_window.attributes("-topmost", True)

        # Create a frame to hold both left and right sections
        self.main_frame = ctk.CTkFrame(self.blacklist_window)
        self.main_frame.grid(row=0, column=0, sticky="nsew")

        # Create the left part of the window (with entry, button, and listbox)
        self.left_frame = ctk.CTkFrame(self.main_frame)
        self.left_frame.grid(row=0, column=0, sticky="nsew")

        self.blacklist_entry = ctk.CTkEntry(self.left_frame, placeholder_text="Insert name to blacklist")
        self.blacklist_entry.pack(pady=20, padx=10, fill="x")

        self.add_to_blacklist_button = ctk.CTkButton(
            self.left_frame, 
            text="Add to Blacklist", 
            corner_radius=0,  # No rounded corners
            command=self.add_to_blacklist
        )
        self.add_to_blacklist_button.pack(pady=10, padx=10, fill="x")

        self.blacklist_listbox = tk.Listbox(self.left_frame, height=6, width=40)
        self.blacklist_listbox.pack(pady=10, padx=10, fill="both")

        # Create the right side frame with gray background and no rounded corners
        self.right_frame = ctk.CTkFrame(self.main_frame, bg_color="gray", corner_radius=0)  # No rounded corners
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=5)

        # Configure the grid layout to make the right frame 1/4 of the window width
        self.main_frame.grid_columnconfigure(0, weight=3)  # Left side takes 3 parts
        self.main_frame.grid_columnconfigure(1, weight=1)  # Right side takes 1 part

        # Set grid layout for right frame
        self.right_frame.grid_rowconfigure(0, weight=1)
        self.right_frame.grid_rowconfigure(1, weight=1)
        self.right_frame.grid_rowconfigure(2, weight=1)
        self.right_frame.grid_rowconfigure(3, weight=1)

        self.right_frame.grid_columnconfigure(0, weight=1)

        # Set a reasonable width for the buttons
        button_width = 90  # Adjust button width to fit nicely within the 1/4 window width

        # Create 4 buttons on the right side
        self.button1 = ctk.CTkButton(self.right_frame, text="Intro", corner_radius=0, width=button_width, command=lambda: self.copy_audio_file('intro.wav'))
        self.button1.grid(row=0, column=0, pady=5, padx=10, sticky="ew")

        self.button2 = ctk.CTkButton(self.right_frame, text="Outro", corner_radius=0, width=button_width, command=lambda: self.copy_audio_file('outro.wav'))
        self.button2.grid(row=1, column=0, pady=5, padx=10, sticky="ew")

        self.button3 = ctk.CTkButton(self.right_frame, text="Button 3", corner_radius=0, width=button_width, command=lambda: self.copy_audio_file('file3.wav'))
        self.button3.grid(row=2, column=0, pady=5, padx=10, sticky="ew")

        self.button4 = ctk.CTkButton(self.right_frame, text="Button 4", corner_radius=0, width=button_width, command=lambda: self.copy_audio_file('file4.wav'))
        self.button4.grid(row=3, column=0, pady=5, padx=10, sticky="ew")

        # Set grid weight to ensure both sides expand
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)

        self.update_blacklist_display()

    def copy_audio_file(self, filename):
        source_dir = "../Assets/Audio/Record/"
        dest_audio_dir = "../Assets/Audio/"
        dest_txt_dir = "../Data/Output/"

        # Ensure the source file exists
        source_file = os.path.join(source_dir, filename)
        if not os.path.exists(source_file):
            print(f"File {filename} not found in {source_dir}")
            return

        # Copy the audio file to the destination with the new name
        dest_audio_file = os.path.join(dest_audio_dir, "hana.wav")
        shutil.copy(source_file, dest_audio_file)
        print(f"Audio file copied to {dest_audio_file}")

        # Create a corresponding text file in the output directory
        dest_txt_file = os.path.join(dest_txt_dir, "hana.txt")
        with open(dest_txt_file, "w") as f:
            f.write("Nothing to recognize here")
        print(f"Text file created at {dest_txt_file}")

    def update_blacklist_display(self):
        self.blacklist_listbox.delete(0, tk.END)
        for name in self.blacklist:
            self.blacklist_listbox.insert(tk.END, name)

    def add_to_blacklist(self):
        name_to_blacklist = self.blacklist_entry.get().strip()

        if name_to_blacklist and name_to_blacklist not in self.blacklist:
            self.blacklist.append(name_to_blacklist)
            self.fancy_log("🔒 ЧЕРНЫЙ СПИСОК", f"{name_to_blacklist} добавлен в черный список.")
            self.blacklist_entry.delete(0, "end")
            self.update_blacklist_display()


    def simulate_chat(self):
        # Create a new window for the chat simulation
        self.chat_simulation_window = ctk.CTkToplevel(self)
        self.chat_simulation_window.title("Simulate Chat")
        self.chat_simulation_window.geometry("400x125")  # Set window size
        self.chat_simulation_window.attributes("-topmost", True)

        # Create a frame to organize slider and checkbox
        frame = ctk.CTkFrame(self.chat_simulation_window)
        frame.pack(pady=20, padx=20, fill="both", expand=True)

        # Add a slider to control the delay
        self.simulation_slider = ctk.CTkSlider(frame, from_=10, to=0.5, command=self.update_simulation_delay)
        self.simulation_slider.set(5)  # Default value
        self.simulation_slider.pack(side="left", padx=10, pady=10, fill="x", expand=True)

        # Add a checkbox to enable/disable the simulation
        self.simulation_checkbox = ctk.CTkCheckBox(frame, text="Enable", command=self.toggle_simulation)
        self.simulation_checkbox.pack(side="left", padx=10, pady=10)

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

    def update_simulation_delay(self, value):
        """Updates the processing delay for the simulation."""
        self.chat_handler.line_processing_delay = float(value)
        self.fancy_log("ОБНОВЛЕНИЕ", f"Задержка обработки изменена на {self.chat_handler.line_processing_delay:.2f} секунд.")

    def toggle_simulation(self):
        """Starts or stops the chat simulation."""
        if self.simulation_checkbox.get():
            self.fancy_log("СИМУЛЯЦИЯ", "Симуляция запущена.")
            self.chat_handler.simulation_event.set()  # Enable the simulation event
            self.simulation_thread = threading.Thread(target=self.run_simulation, daemon=True)
            self.simulation_thread.start()
        else:
            self.fancy_log("СИМУЛЯЦИЯ", "Симуляция остановлена.")
            self.chat_handler.simulation_event.clear()  # Disable the simulation event

    def run_simulation(self):
        """Processes the chat.txt file line-by-line."""
        try:
            file_path = self.chat_handler.output_file

            while self.chat_handler.simulation_event.is_set():  # Continue processing only if enabled
                self.chat_handler.process_text_file(file_path)
                time.sleep(1)  # Add a small delay to avoid excessive processing

            self.fancy_log("СИМУЛЯЦИЯ", "Симуляция завершена.")
        except Exception as e:
            self.fancy_log("ОШИБКА", f"Ошибка при запуске симуляции: {e}")

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

            self.long_button.configure(text="Mic Off")

        else:
            # Stop the recording
            self.is_recording.clear()
            self.stop_recording_loop()

            # Ensure the recording thread finishes before resuming random_picker
            if self.mic_thread and self.mic_thread.is_alive():
                self.mic_thread.join()  # Wait for the mic logic to complete

            # Resume random_picker
            self.mic_pause_event.clear()

            self.long_button.configure(text="Mic On")

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
                    if os.getenv('Avatar-On') == 'True':
                        with open(self.resource_path("../Data/Output/hana.txt"), "w", encoding='utf-8') as file:
                            file.write("Аудио готово")
                    else:
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
        self.fancy_log("▶️ Hana Запущен", "random_picker запущен.")
        self.stop_random_picker.clear()  # Clear the stop event before starting
        self.picker_thread = threading.Thread(target=self.random_picker, daemon=True)
        self.picker_thread.start()
        self.random_picker_running = True

    
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
        self.fancy_log("📡 Chloe AI", "Мониторинг Chloe AI запущен")
        self.monitor_thread = threading.Thread(target=self.monitor_file, daemon=True)
        self.monitor_thread.start()     # Start the monitoring thread
        self.monitor_file_running = True
        time.sleep(5)

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
            "Government Bad?",
            "Tilted when?",
            "Make a hot take. (topic is your choice).",
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

                    # Check for blacklisted viewer
                    if viewer_text in self.blacklist:
                        self.fancy_log("⛔ ЗАБЛОКИРОВАННЫЙ ЗРИТЕЛЬ", f"Пропуск ввода от заблокированного зрителя: '{viewer_text}'")
                        time.sleep(5)
                        continue  # Skip further processing and go to the next iteration

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

                    # Check for blacklisted viewer
                    if viewer_text in self.blacklist:
                        self.fancy_log("⛔ ЗАБЛОКИРОВАННЫЙ ЗРИТЕЛЬ", f"Пропуск ввода от заблокированного зрителя: '{viewer_text}'")
                        time.sleep(5)
                        continue  # Skip further processing and go to the next iteration

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
                    normalize(hana_output_path)

                    if os.getenv('Avatar-On') == 'True':
                        with open(self.resource_path("../Data/Output/hana.txt"), "w", encoding='utf-8') as file:
                            file.write(emotion(processed_string, self.llm_model))
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
        """Get path to resource relative to the executable's location."""
        # Get the directory of the executable if frozen (PyInstaller), else use script location
        base_path = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
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
        self.chloe_window = CWindow(self)
        self.chloe_window.mainloop()

    def open_window2(self):
        self.hana_window = HWindow(self)
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

class Record(ctk.CTk):
    def __init__(self, selected_mic_index, folder_path, output_device_index=None):
        super().__init__()
        self.title("Интерфейс записи")
        self.geometry("600x400")

        self.attributes("-topmost", True)
        self.folder_path = folder_path
        self.sample_rate = 16000
        self.selected_mic_index = selected_mic_index  # Store selected mic index
        self.output_device_index = output_device_index  # Store the output device index
        self.current_files = []  # List to keep track of current files
        self.current_file = None
        self.ranting_window = None
        self.reading_window = None

        # Log and load the Whisper model
        self.fancy_log("🔄 ЗАГРУЗКА", "Загрузка Whisper Large Model...")
        self.model = whisper.load_model("large")  # Load Whisper large model
        self.fancy_log("✅ УСПЕШНО", "Whisper Large Model загружена.")

        # Ensure the path for recorded audio is correctly defined here
        self.recorded_audio_file = os.path.join(self.folder_path, "recorded_audio.wav")

        # Create a main frame to hold both the folder view and controls
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Create a frame for folder contents (left side)
        self.folder_frame = ctk.CTkFrame(self.main_frame, width=200)
        self.folder_frame.pack(side="left", fill="y", padx=(0, 10))

        # Listbox for folder contents
        self.file_listbox = tk.Listbox(self.folder_frame, width=30, height=10)
        self.file_listbox.pack(fill="x", padx=5, pady=5)
        self.load_folder_contents(self.folder_path)

        # Bind the selection event for Listbox
        self.file_listbox.bind("<<ListboxSelect>>", self.on_file_select)

        # Textbox for displaying the fixed file's content (below the file list)
        self.fixed_textbox = ctk.CTkTextbox(self.folder_frame, height=10, width=30, wrap="word")
        self.fixed_textbox.pack(fill="both", expand=True, padx=5, pady=5)

        # Load the fixed text file contents
        self.load_fixed_text_file()

        # Create a frame for the controls (right side)
        self.controls_frame = ctk.CTkFrame(self.main_frame, width=300)
        self.controls_frame.pack(side="right", fill="both", expand=True)

        # Create a textbox at the top with the same width as buttons and switches
        self.textbox = ctk.CTkTextbox(self.controls_frame, height=100, width=300)
        self.textbox.pack(pady=(20, 10), padx=20)

        # Create a frame for Start and Stop buttons
        self.button_frame = ctk.CTkFrame(self.controls_frame)
        self.button_frame.pack(pady=10, padx=20)

        # Start button
        self.start_button = ctk.CTkButton(self.button_frame, text="Начать запись", width=140, command=self.start_recording, corner_radius=0)
        self.start_button.pack(side="left", padx=(0, 5))

        # Stop button
        self.stop_button = ctk.CTkButton(self.button_frame, text="Остановить запись", width=140, command=self.stop_recording, corner_radius=0)
        self.stop_button.pack(side="right", padx=(5, 0))

        # Create a frame to hold the slider value and dropdown horizontally
        self.number_dropdown_frame = ctk.CTkFrame(self.controls_frame)
        self.number_dropdown_frame.pack(fill="x", pady=(10, 20), padx=20)

        # Label to display the slider value (on the left)
        self.slider_value_label = ctk.CTkLabel(
            self.number_dropdown_frame,
            text="500",  # Default value
            width=50,  # Fixed width for consistency
            anchor="e"  # Align text to the right
        )
        self.slider_value_label.pack(side="left", padx=(0, 10))

        # Dropdown for .mp3 files (on the right of the slider value)
        self.audio_folder_path = "../Assets/Audio"
        self.mp3_files = self.get_mp3_files()
        self.mp3_dropdown = ctk.CTkComboBox(
            self.number_dropdown_frame,
            values=self.mp3_files,
            fg_color="green"  # Background color for the dropdown
        )
        self.mp3_dropdown.pack(side="right", fill="x", expand=True)

        self.banned_words = os.getenv("BANNED_WORDS").split(",")

        # Slider for selecting a value from 0 to 1000
        self.slider = ctk.CTkSlider(
            self.controls_frame,
            from_=0,
            to=1000,
            command=self.on_slider_change
        )
        self.slider.set(500)  # Set default slider value
        self.slider.pack(pady=(10, 20), padx=20)

        # Create a frame for the language switches and place it at the bottom of the controls frame
        self.switch_frame = ctk.CTkFrame(self.controls_frame)
        self.switch_frame.pack(pady=10, padx=5, side="bottom", anchor="s")  # Positioning at the bottom

        # Language switches with fixed width and spacing to fit nicely
        self.switch_en = ctk.CTkSwitch(self.switch_frame, text="EN", width=60)
        self.switch_en.pack(side="left", padx=5)

        self.switch_es = ctk.CTkSwitch(self.switch_frame, text="ES", width=60)
        self.switch_es.pack(side="left", padx=5)

        self.switch_ru = ctk.CTkSwitch(self.switch_frame, text="RU", width=60)
        self.switch_ru.pack(side="left", padx=5)

        self.switch_ja = ctk.CTkSwitch(self.switch_frame, text="JA", width=60)
        self.switch_ja.pack(side="left", padx=5)

        # Start a periodic check to update the file list
        self.monitor_folder()

        # Bind 'r' and 's' keys to start and stop actions
        self.bind("<7>", lambda event: self.start_recording())
        self.bind("<8>", lambda event: self.stop_recording())
        self.focus_set()  # Set focus to the window to capture keypresses

        self.textbox.bind("<Return>", self.transcribe_and_process)

        self.open_ranting_window()

    def open_ranting_window(self):
        """Open the Ranting window and trigger Reading window."""
        if self.ranting_window is None or not self.ranting_window.winfo_exists():
            self.ranting_window = Ranting(self)
            self.ranting_window.protocol("WM_DELETE_WINDOW", self.cleanup_ranting_window)
            self.open_reading_window()  # Open the Reading window
        else:
            self.ranting_window.focus()

    def cleanup_ranting_window(self):
        """Handle cleanup when the Ranting window is closed."""
        if self.ranting_window:
            self.ranting_window.destroy()
        self.ranting_window = None

    def open_reading_window(self):
        """Open the Reading window."""
        if self.reading_window is None or not self.reading_window.winfo_exists():
            self.reading_window = Reading(self)
        else:
            self.reading_window.focus()

    def load_fixed_text_file(self):
        """Load and display the contents of a fixed text file in the textbox."""
        fixed_file_path = self.resource_path("../Data/Input/timings.txt")
        try:
            with open(fixed_file_path, "r", encoding="utf-8") as file:
                content = file.read()
                self.fixed_textbox.delete("1.0", tk.END)  # Clear existing content
                self.fixed_textbox.insert("1.0", content)  # Insert new content
        except FileNotFoundError:
            self.fixed_textbox.insert("1.0", "Error: Fixed text file not found.")
        except Exception as e:
            self.fixed_textbox.insert("1.0", f"Error loading file: {str(e)}")

    def get_mp3_files(self):
        """Fetches .mp3 files from the ../Assets/Audio directory."""
        try:
            return [f for f in os.listdir(self.audio_folder_path) if f.endswith('.mp3')]
        except FileNotFoundError:
            return []

    def on_slider_change(self, value):
        """Update the label and toggle censoring based on slider value."""
        self.slider_value = int(value)
        self.slider_value_label.configure(text=f"{self.slider_value}")
        self.censoring = self.slider_value != 1000

    def on_file_select(self, event):
        """Play the selected file if it is an audio file."""
        selected_index = self.file_listbox.curselection()
        if selected_index:
            selected_file = self.file_listbox.get(selected_index)
            selected_file_path = os.path.join(self.folder_path, selected_file)

            # Check if the selected file is a .wav audio file
            if selected_file.lower().endswith('.wav'):
                self.current_file = selected_file_path
                self.play_audio()  # Play the selected audio file

    def transcribe_and_process(self, event):
        """Transcribe the text and process it."""
        # Get the text from the textbox
        input_text = self.textbox.get("1.0", tk.END).strip()
        if not input_text:
            self.fancy_log("⚠️ ВНИМАНИЕ", "Введите текст для транскрипции.")
            return

        # Determine the selected language
        selected_language = self.get_selected_language(input_text)

        # Transcribe the text based on the selected language
        translated_text = translate(input_text, selected_language)

        # Get the banned audio path from the dropdown
        banned_audio_path = os.path.join(self.audio_folder_path, self.mp3_dropdown.get())
        if not banned_audio_path:
            self.fancy_log("⚠️ ВНИМАНИЕ", "Выберите аудиофайл, который будет использоваться для запрещённых слов.")
            return

        # Get the banned audio offset from the slider
        banned_audio_offset = self.slider_value

        # Get the output path from user input
        output_path = tk.simpledialog.askstring("Save File", "Введите имя файла для сохранения (без расширения):")
        if not output_path:
            self.fancy_log("⚠️ ВНИМАНИЕ", "Имя файла не введено. Аудиофайл не сохранен.")
            return
        output_path = os.path.join(self.folder_path, f"{output_path}.wav")

        censor_enabled = self.censoring  # Use the updated censoring state

        if censor_enabled:
            self.fancy_log("✅ Обработка", "Цензура активирована для текста.")
        else:
            self.fancy_log("🚫 Обработка", "Цензура отключена для текста.")

        # Call the tts function with required parameters
        tts(
            input_text=translated_text,
            banned_words=self.banned_words,  # Assuming this is a class attribute
            language=selected_language,
            banned_audio_path=banned_audio_path,
            output_path=output_path,
            banned_audio_offset=banned_audio_offset,
            censor_enabled=censor_enabled  # Pass censoring state
        )

        # You may want to implement additional processing here if needed

        self.fancy_log("✅ УСПЕШНО", f"Файл сохранен как: {output_path}")

    def get_selected_language(self, input_text):
        """Determine the selected language based on the switches."""
        if self.switch_en.get():
            return 'en'
        elif self.switch_ru.get():
            return 'ru'
        elif self.switch_es.get():
            return 'es'
        elif self.switch_ja.get():
            return 'ja'
        
        # If none of the switches are selected, assume English by default
        return 'en'

    def play_audio(self):
        """Play the recorded or selected audio."""
        if os.path.exists(self.current_file):
            play(self.current_file, output_device_index=self.output_device_index)
        else:
            print("No recorded or selected audio file found.")

    def clean_up_unwanted_files(self, *files):
        """Remove or move unwanted audio files after processing."""
        for file in files:
            if os.path.exists(file):
                os.remove(file)  # Remove the unwanted file

    def load_folder_contents(self, folder_path):
        """Load and display the folder contents in the Listbox."""
        if os.path.exists(folder_path):
            files = os.listdir(folder_path)
            self.current_files = files  # Keep track of current files

            self.file_listbox.delete(0, tk.END)  # Clear the listbox
            for file in files:
                self.file_listbox.insert(tk.END, file)  # Insert each file/folder into the listbox
        else:
            self.file_listbox.insert(tk.END, "Folder not found")

    def monitor_folder(self):
        """Monitor the folder for changes and update the Listbox if new files are detected."""
        if os.path.exists(self.folder_path):
            current_files = os.listdir(self.folder_path)
            if current_files != self.current_files:
                # If there are changes, update the listbox
                self.current_files = current_files
                self.file_listbox.delete(0, tk.END)  # Clear the listbox
                for file in current_files:
                    self.file_listbox.insert(tk.END, file)  # Insert updated file list
        else:
            self.file_listbox.delete(0, tk.END)
            self.file_listbox.insert(tk.END, "Folder not found")

        # Check the folder again after 2 seconds (2000 milliseconds)
        self.after(2000, self.monitor_folder)

    def start_recording(self):
        """Start recording using the selected microphone."""
        self.fancy_log("📹 НАЧАЛО ЗАПИСИ", "Запись началась...")
        self.is_recording = True
        self.recorded_audio = []
        self.recording_thread = threading.Thread(target=self.record_audio)
        self.recording_thread.start()

    def record_audio(self):
        """Capture audio data from the selected microphone."""
        while self.is_recording:
            # Use the selected microphone index for recording
            audio_chunk = sd.rec(int(1 * self.sample_rate), samplerate=self.sample_rate, 
                                 channels=1, dtype='float64', device=self.selected_mic_index)
            sd.wait()
            self.recorded_audio.append(audio_chunk)

    def stop_recording(self):
        """Stop recording and save the audio as a WAV file."""
        self.is_recording = False
        self.recording_thread.join()

        # Save audio to file
        recorded_audio_np = np.concatenate(self.recorded_audio, axis=0)
        wavio.write(self.recorded_audio_file, recorded_audio_np, self.sample_rate, sampwidth=3)

        self.transcribe_audio(self.recorded_audio_file)

    def transcribe_audio(self, audio_file_path):
        """Transcribe the recorded audio and delete the file if the mic was used."""
        result = self.model.transcribe(audio_file_path)
        transcribed_text = result["text"]

        # Display transcription
        self.textbox.delete("1.0", tk.END)
        self.textbox.insert(tk.END, transcribed_text)

        # Check if the microphone was used (mic index is not None)
        if self.selected_mic_index is not None:
            self.delete_audio_file(audio_file_path)

    def delete_audio_file(self, audio_file_path):
        """Delete the recorded audio file if it exists."""
        if os.path.exists(audio_file_path):
            try:
                os.remove(audio_file_path)
                self.fancy_log("🗑️ УДАЛЕНО", f"Файл {audio_file_path} был успешно удалён.")
            except OSError as e:
                self.fancy_log("❌ ОШИБКА", f"Ошибка удаления файла: {e}")
        else:
            self.fancy_log("⚠️ ОШИБКА", f"Файл {audio_file_path} не найден.")

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

    def calculate_display_width(self, text):
        """Helper method to calculate the display width of the log text."""
        return len(text)
    
    def resource_path(self, relative_path):
        """Get path to resource relative to the executable's location."""
        # Get the directory of the executable if frozen (PyInstaller), else use script location
        base_path = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
        return os.path.join(base_path, relative_path)