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
from dotenv import load_dotenv
from App.chloe import CWindow
from App.hana import HWindow
from App.hana import hana_ai
from App.chloe import chloe_ai
from App.chat import YouTubeChatHandler
from App.chat import TwitchChatHandler
from App.audio import translate
from App.audio import record_audio
from App.audio import distort
from App.audio import tts_en
from App.audio import tts_es
from App.audio import tts_ja
from App.audio import tts_ru
from App.rvc import mainrvc
from App.audio import play
from App.rag import mainrag
from App.model import load_model

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
                with open(self.file_path, 'w') as file:
                    file.write("")
        except Exception as e:
            print(f"Error ensuring file exists: {e}")

    def load_content(self):
        try:
            with open(self.file_path, 'r') as file:
                content = file.read()
            self.textbox.delete("1.0", ctk.END)
            self.textbox.insert(ctk.END, content)
            self.textbox.see(ctk.END)  # Ensure the content is visible
        except Exception as e:
            print(f"Error loading content: {e}")

    def save_content(self, event=None):
        try:
            content = self.textbox.get("1.0", ctk.END).strip()  # Strip trailing newlines
            with open(self.file_path, 'w') as file:
                file.write(content)
        except Exception as e:
            print(f"Error saving content: {e}")

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
                print(f"Error monitoring file changes: {e}")

class App(ctk.CTk):
    def __init__(self, microphone_index=None, output_device_index=None, selected_platform="None", selected_llm=None):
        super().__init__()

        self.title("Control Panel")
        self.geometry("640x800")  # Increased height to accommodate the new layout
        ctk.set_appearance_mode("dark")  # Dark mode
        ctk.set_default_color_theme("green")  # Green accent

        self.selected_mic_index = microphone_index
        self.selected_platform = selected_platform
        self.selected_output_device_index = output_device_index

        print(f"Playing audio on device index: {self.selected_output_device_index}")
        print(f"Using services: {self.selected_platform}")
        print(f"Inputting audio on device index: {self.selected_mic_index}")


        self.folder_to_clear = self.resource_path('../Data/Output')
        self.delete_all_files_in_folder(self.folder_to_clear)

        self.pause_event = threading.Event()  # Event to pause/resume random_picker
        self.chloe_event = threading.Event()  # Event to signal Chloe monitoring
        self.stop_chloe_event = threading.Event()  # Event to signal stopping Chloe


        self.after_id = None
        self.youtube_handler = None
        self.twitch_handler = None
        self.picker_thread = None
        self.handler_thread = None

        self.known_emotes = []

        # Resolve the base path for PyInstaller
        self.base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))

        self.selected_llm = selected_llm

        # Load the selected LLM model if one is provided
        if self.selected_llm:
            print(f"Loading LLM model from: {self.selected_llm}")
            self.llm_model = load_model(self.selected_llm)
            if self.llm_model:
                print("Model loaded successfully!")
            else:
                print("Failed to load the model.")
        else:
            print("No LLM model selected.")

        # Create a frame for the search bar at the top
        search_frame = ctk.CTkFrame(self)
        search_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        # Create the search bar (CTkEntry)
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Search...")
        self.search_entry.pack(fill="x", padx=10, pady=5)

        # Variables to manage the timing and last printed text
        self.last_printed_text = ""
        self.after_id = None

        # Bind the search entry's key release event to handle input changes
        self.search_entry.bind("<KeyRelease>", self.on_search_change)


        # File paths (adjust these to match your directory structure)
        files = [
            self.resource_path('../Data/Chat/General/viewer1.hana'),
            self.resource_path('../Data/Chat/General/input1.hana'),
            self.resource_path('../Data/Chat/General/viewer2.hana'),
            self.resource_path('../Data/Chat/General/input2.hana'),
            self.resource_path('../Data/Chat/General/viewer3.hana'),
            self.resource_path('../Data/Chat/General/input3.hana')
        ]

        # Create text boxes in two columns
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        for i, file in enumerate(files):
            frame = TextBoxFrame(self, file)
            frame.grid(row=(i // 2) + 1, column=i % 2, padx=10, pady=10)  # Text boxes start at row 1

        # Adjust the button frame row placement to ensure it is below the text boxes
        button_frame = ctk.CTkFrame(self)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10, sticky="ew")  # Shifted to row 4 to account for the search bar and text boxes

        # Create and pack the buttons horizontally with corner-less style
        buttons = ["Hana Start", "Hana Stop", "Chloe Start", "Chloe Stop"]
        for i, button_text in enumerate(buttons):
            if button_text == "Hana Start":
                button = ctk.CTkButton(button_frame, text=button_text, corner_radius=0, command=self.hana_start)
            elif button_text == "Hana Stop":
                button = ctk.CTkButton(button_frame, text=button_text, corner_radius=0, command=self.hana_stop)
            elif button_text == "Chloe Start":
                button = ctk.CTkButton(button_frame, text=button_text, corner_radius=0, command=self.chloe_start)
            else:
                button = ctk.CTkButton(button_frame, text=button_text, corner_radius=0, command=self.chloe_stop)
            button.grid(row=0, column=i, padx=10, pady=5, sticky="ew")


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

        # Sliders
        for i in range(2):
            slider = ctk.CTkSlider(left_frame)
            slider.grid(row=2+i, column=1, columnspan=4, pady=5, sticky="ew")  # Centered within the section

        self.is_recording = threading.Event()  # Event to signal when recording is active

        # Long button
        long_button = ctk.CTkButton(left_frame, text="Mic On", corner_radius=0, command=self.start_recording)
        long_button.grid(row=4, column=1, columnspan=4, pady=10, sticky="ew")

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

        # Example button to open additional windows
        open_window1_button = ctk.CTkButton(self, text="Open Chloe Chatter", command=self.open_window1, corner_radius=0)
        open_window1_button.grid(row=6, column=0, padx=10, pady=10, sticky="ew")

        open_window2_button = ctk.CTkButton(self, text="Open Hana Chatter", command=self.open_window2, corner_radius=0)
        open_window2_button.grid(row=6, column=1, padx=10, pady=10, sticky="ew")

        self.stop_random_picker = threading.Event()

    def on_search_change(self, event):
        # Cancel any existing scheduled print function
        if self.after_id:
            self.after_cancel(self.after_id)

        # Get the current text from the search entry
        current_text = self.search_entry.get()

        # Schedule a new function to run after 2 seconds
        self.after_id = self.after(2000, mainrag, current_text)
        
    def delete_all_files_in_folder(self, folder_path):
        """Delete all files in the specified folder."""
        try:
            # Check if the folder exists
            if not os.path.exists(folder_path):
                print(f"Folder '{folder_path}' does not exist.")
                return

            # List all files and directories in the folder
            for file_name in os.listdir(folder_path):
                file_path = os.path.join(folder_path, file_name)

                # Check if it's a file or directory
                if os.path.isfile(file_path):
                    # Delete the file
                    os.remove(file_path)
                    print(f"Deleted file: {file_path}")
                elif os.path.isdir(file_path):
                    # Delete the directory and all its contents
                    shutil.rmtree(file_path)
                    print(f"Deleted directory: {file_path}")

            print(f"All files in folder '{folder_path}' have been deleted.")

        except Exception as e:
            print(f"Error occurred while deleting files: {e}")

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
            with open(file_name, "w") as file:
                file.write(file_contents[button_text])

            # Show a confirmation message
            print("File Created", f"{button_text}.txt has been created!")

        except Exception as e:
            # Show an error message if file creation fails
            print("Error", f"Could not create file: {str(e)}")

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

    def start_recording(self):
        output_file = self.resource_path('../Assets/Audio/user.wav')
        self.is_recording.set()  # Set the event indicating recording is active
        threading.Thread(target=self.record_and_process_audio, args=(output_file,)).start()

    def record_and_process_audio(self, output_file):
        try:
            self.is_recording.set()  # Set the event indicating recording is active

            # Step 1: Record audio
            record_audio(output_file, self.selected_mic_index, record_seconds=10)  # Increased recording time to 10 seconds

            # Step 2: Transcribe audio using Whisper
            model = whisper.load_model("large", device="cuda")
            result = model.transcribe(output_file)
            transcribed_text = result['text']

            # Log the transcription result
            print(f"Transcribed text: {transcribed_text}")
            
            # Print the transcribed text to the console
            print(f"Transcribed Text: {transcribed_text}")

            # Step 3: Determine which TTS function to use based on active switch
            tts_function = self.get_active_tts_function()

            if tts_function:
                # Step 4: Generate ai.wav using the selected TTS function
                ai_output_path = self.resource_path('../Assets/Audio/ai.wav')
                tts_function(transcribed_text, output_path=ai_output_path)
            else:
                print("No TTS switch is active. Using default TTS (English).")
                ai_output_path = self.resource_path('../Assets/Audio/ai.wav')
                tts_en(transcribed_text, output_path=ai_output_path)

            # Print a message when the audio file is created
            print(f"Audio file created at: {ai_output_path}")

            # Step 5: Process the generated ai.wav file using mainrvc and save it as hana.wav
            hana_output_path = self.resource_path('../Assets/Audio/hana.wav')
            mainrvc(ai_output_path, hana_output_path)

            # Print a message when the hana.wav file is created
            print(f"Hana audio file created at: {hana_output_path}")

            # Step 6: Play the processed hana.wav file
            play(hana_output_path)

        finally:
            self.is_recording.clear()  # Clear the event when recording and processing is finished

    def start_recording(self):
        output_file = self.resource_path('../Assets/Audio/user.wav')
        threading.Thread(target=self.record_and_process_audio, args=(output_file,)).start()

    def get_active_tts_function(self):
        for switch, tts_func in zip([self.switch_en, self.switch_es, self.switch_ru, self.switch_jp],
                                    [tts_en, tts_es, tts_ru, tts_ja]):
            if switch.get():
                return tts_func
        # Default to English TTS if no other switch is active
        return tts_en

    def hana_start(self):
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
            print("No chat handler started (None selected).")

        # Start random picker
        self.stop_random_picker.clear()  # Clear the stop event before starting
        self.picker_thread = threading.Thread(target=self.random_picker, daemon=True)
        self.picker_thread.start()

    def hana_stop(self):
        # Stop only the random picker thread
        self.stop_random_picker.set()  # Signal the picker thread to stop

        print("Random picker stopped. Chat handlers still running.")

    def chloe_start(self):
        self.stop_chloe_event.clear()  # Clear any stop events
        self.pause_event.clear()       # Clear pause event to allow random_picker to run
        threading.Thread(target=self.monitor_file, daemon=True).start()
        threading.Thread(target=self.random_picker, daemon=True).start()
        print("Chloe AI monitoring and random picker started.")

    def chloe_stop(self):
        print("Stopping Chloe monitoring...")
        self.stop_chloe_event.set()  # Signal to stop the monitoring thread
        self.pause_event.clear()

    def start_youtube_chat(self):
        load_dotenv()
        video_id = os.getenv('Video-Url')
        mod_names = ["mod1", "mod2", "mod3"]
        self.youtube_handler = YouTubeChatHandler(video_id, mod_names)
        self.youtube_handler.start()

    def start_twitch_chat(self):
        load_dotenv()
        token = os.getenv('Twitch-Token')
        client_id = os.getenv('Twitch-Client-ID')
        nick = os.getenv('Twitch-Nick')
        prefix = os.getenv('Twitch-Prefix')
        initial_channels = [os.getenv('Twitch-Channel')]
        mod_names = ["mod1", "mod2", "mod3"]
        self.twitch_handler = TwitchChatHandler(token=token, client_id=client_id, nick=nick, prefix=prefix, initial_channels=initial_channels, mod_names=mod_names)
        self.twitch_handler.run()

    def start_alternating_handlers(self):
        load_dotenv()
        video_id = os.getenv('Video-Url')
        yt_mods = ["mod1", "mod2", "mod3"]
        token = os.getenv('Twitch-Token')
        client_id = os.getenv('Twitch-Client-ID')
        nick = os.getenv('Twitch-Nick')
        prefix = os.getenv('Twitch-Prefix')
        initial_channels = [os.getenv('Twitch-Channel')]
        tt_mods = ["mod1", "mod2", "mod3"]
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

        last_formatted_string = None  # Initialize the variable

        while not self.stop_random_picker.is_set():  # Check if the stop event is set
            if self.is_recording.is_set():
                # If recording is active, skip printing or any processing
                print("Random picker is paused due to active recording.")
                time.sleep(1)  # Small sleep to prevent busy-waiting
                continue

            # Check for the pause event
            if self.pause_event.is_set():
                print("Random picker is paused for Chloe AI processing.")
                self.pause_event.wait()  # This will block until the pause_event is cleared
                print("Random picker resumed.")

            index = random.randint(0, 2)

            # Open the input files with UTF-8 encoding
            with open(input_files[index], 'r', encoding='utf-8') as infile:
                input_text = infile.read().strip()

            # Open the viewer files with UTF-8 encoding
            with open(viewer_files[index], 'r', encoding='utf-8') as viewerfile:
                viewer_text = viewerfile.read().strip()

            # Check for empty input and skip if empty
            if not input_text:
                print("Skipping empty input text.")
                time.sleep(5)
                continue

            # Check if input begins with '!' and skip if it does
            if input_text.startswith('!'):
                print("Skipping input text that begins with '!'.")
                time.sleep(5)
                continue

            # Check if input text contains any emojis and skip if it does
            if self.contains_emoji_or_emote(input_text):
                print("Skipping input text that contains an emoji.")
                time.sleep(5)
                continue

            # Check if any language switches are toggled on
            any_switch_toggled = any([self.switch_en.get(), self.switch_es.get(), self.switch_ru.get(), self.switch_jp.get()])

            # If any switch is toggled, translate the text; otherwise, skip translation
            if any_switch_toggled:
                target_language = self.get_active_language()
                if target_language:
                    input_text = translate(input_text, target_language)

            formatted_string = f"System: {viewer_text} asks: {input_text}"

            # Check if the current message is the same as the last one
            if formatted_string != last_formatted_string:
                # Process the formatted string with hana_ai
                processed_string = hana_ai(formatted_string, self.llm_model)

                # Update HWindow if it's open
                if self.hana_window and isinstance(self.hana_window, HWindow):
                    self.hana_window.update_textbox(processed_string)

                last_formatted_string = processed_string

                # Write the processed string to a text file
                output_file_path = self.resource_path('../Data/Output/output.hana')
                with open(output_file_path, 'w', encoding='utf-8') as outfile:
                    outfile.write(processed_string)

                # Select the TTS function based on the active language switch or default to English
                tts_function = self.get_active_tts_function() if any_switch_toggled else tts_en

                if tts_function:
                    # Generate the audio file using the selected TTS function
                    ai_output_path = self.resource_path('../Assets/Audio/ai.wav')
                    tts_function(processed_string, output_path=ai_output_path)

                    # Process the audio file with mainrvc and save as hana.wav
                    hana_output_path = self.resource_path('../Assets/Audio/hana.wav')
                    mainrvc(ai_output_path, hana_output_path)

                    print(f"Generated audio for picker: {hana_output_path}")

                    # Play the generated hana.wav file
                    # play(hana_output_path, self.selected_output_device_index)
                else:
                    print("No TTS function is active. Cannot generate audio.")
                    continue  # Skip if no TTS function is available
            else:
                print("Skipping repeated input text.")

            time.sleep(5)

        print("Exiting random picker thread.")
        
    def monitor_file(self):
        chloe_file_path = self.resource_path('../Data/Output/output.hana')
        log_file_path = self.resource_path('../Data/Output/output.chloe')

        # Wait for the file to exist before proceeding
        while not os.path.exists(chloe_file_path):
            print(f"File {chloe_file_path} not found. Retrying in 1 second...")
            time.sleep(1)

        last_modified_time = os.path.getmtime(chloe_file_path)

        while not self.stop_chloe_event.is_set():  # Check if Chloe monitoring is stopped

            # Wait for the file to exist in case it was deleted
            if not os.path.exists(chloe_file_path):
                print(f"File {chloe_file_path} not found. Waiting...")
                time.sleep(1)
                continue

            current_modified_time = os.path.getmtime(chloe_file_path)

            # Check if the file has been modified
            if current_modified_time != last_modified_time:
                print("Change detected in Chloe file.")

                # Step 1: Pause random_picker
                print("Pausing random_picker...")
                self.pause_event.set()  # This should pause the random_picker

                try:
                    # Step 2: Process the file with chloe_ai
                    with open(chloe_file_path, 'r', encoding='utf-8') as file:
                        chloe_text = file.read().strip()

                    if chloe_text:
                        print(f"Processing Chloe text: {chloe_text}")
                        # Process with Chloe AI and get the output string
                        processed_chloe_text = chloe_ai(chloe_text)

                        # Log chloe_ai output to a file
                        with open(log_file_path, 'w', encoding='utf-8') as file:
                            file.write(f"Original: {chloe_text}\nProcessed: {processed_chloe_text}\n")

                        # Step 3: Determine which TTS function to use (like random_picker)
                        tts_function = self.get_active_tts_function()  # Use TTS based on active switches

                        if tts_function:
                            # Generate the audio file using the selected TTS function
                            ai_output_path = self.resource_path('../Assets/Audio/ai_chloe.wav')
                            print(f"Generating audio file at {ai_output_path}...")
                            tts_function(processed_chloe_text, output_path=ai_output_path)

                            # Process the audio file with mainrvc and save as chloe.wav
                            chloe_output_path = self.resource_path('../Assets/Audio/chloe.wav')
                            mainrvc(ai_output_path, chloe_output_path)

                            print(f"Generated audio for Chloe: {chloe_output_path}")

                            # Optionally play the generated audio file
                            # play(chloe_output_path, self.selected_output_device_index)
                        else:
                            print("No TTS function is active. Skipping audio generation.")
                    else:
                        print("Chloe file was empty, skipping processing.")

                except Exception as e:
                    print(f"Error processing Chloe file: {str(e)}")

                finally:
                    # Step 4: Resume random_picker
                    print("Resuming random_picker...")
                    self.pause_event.clear()  # Allow random_picker to resume

                    # Update the last modification time
                    last_modified_time = current_modified_time

            # Wait 5 seconds after random_picker resumes, then start monitoring again
            time.sleep(5)

    def resource_path(self, relative_path):
        """ Get the absolute path to the resource, works for dev and for PyInstaller """
        try:
            # If using PyInstaller, sys._MEIPASS will be set to the temporary folder where files are extracted
            base_path = sys._MEIPASS
        except AttributeError:
            # Otherwise, use the current directory
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def open_window1(self):
        window1 = CWindow()
        window1.mainloop()

    def open_window2(self):
        self.hana_window = HWindow(self)  # Pass the reference of App to HWindow
        self.hana_window.mainloop()

    def destroy(self):
        if self.after_id is not None:
            self.after_cancel(self.after_id)
        super().destroy()