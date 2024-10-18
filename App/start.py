import customtkinter as ctk
import tkinter as tk
import os
import sys
import random
import string
from gui import Stream
from gui import Record
from audio import list_microphones, list_output_devices  

class StartWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Setup")
        self.geometry("350x625")  # Adjust height to fit all widgets
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        self.after_ids = []

        # Get the list of available microphones and output devices
        self.microphones = list_microphones()  # Now contains tuples of (name, index)
        self.output_devices = list_output_devices()  # Now contains tuples of (name, index)

        # Extract only the names for the dropdown display
        microphone_names = [name for name, idx in self.microphones]
        output_device_names = [name for name, idx in self.output_devices]
        platform_options = ["None", "Youtube", "Twitch", "Both"]

        # Find the maximum width needed for the dropdowns
        all_names = microphone_names + output_device_names + platform_options
        max_width = max(len(name) for name in all_names) * 8  # Approximate width in pixels (8 pixels per character)

        # Microphone dropdown with label
        self.microphone_label = ctk.CTkLabel(self, text="Select Microphone", text_color="grey")
        self.microphone_label.pack(pady=(20, 0))
        self.dropdown_var1 = tk.StringVar(value=microphone_names[0] if microphone_names else "No Microphone")
        self.dropdown_menu1 = ctk.CTkOptionMenu(self, variable=self.dropdown_var1, 
                                                  values=microphone_names if microphone_names else ["No Microphone"], 
                                                  corner_radius=0, width=max_width)
        self.dropdown_menu1.pack(padx=20, pady=10, ipady=2)

        # Platform selection dropdown with label
        self.platform_label = ctk.CTkLabel(self, text="Select Streaming Platform", text_color="grey")
        self.platform_label.pack(pady=(20, 0))
        self.dropdown_var2 = tk.StringVar(value="None")
        self.dropdown_menu2 = ctk.CTkOptionMenu(self, variable=self.dropdown_var2, 
                                                  values=platform_options, 
                                                  corner_radius=0, width=max_width)
        self.dropdown_menu2.pack(padx=20, pady=10, ipady=2)

        # Output device dropdown with label
        self.output_device_label = ctk.CTkLabel(self, text="Select Output Device", text_color="grey")
        self.output_device_label.pack(pady=(20, 0))
        self.dropdown_var3 = tk.StringVar(value=output_device_names[0] if output_device_names else "No Output Device")
        self.dropdown_menu3 = ctk.CTkOptionMenu(self, variable=self.dropdown_var3, 
                                                  values=output_device_names if output_device_names else ["No Output Device"], 
                                                  corner_radius=0, width=max_width)
        self.dropdown_menu3.pack(padx=20, pady=10, ipady=2)

        # Folder file selection dropdown with label
        self.folder_label = ctk.CTkLabel(self, text="Select Local GGUF File", text_color="grey")
        self.folder_label.pack(pady=(20, 0))
        self.dropdown_var4 = tk.StringVar(value="None")
        folder_files = self.list_files_in_folder(self.resource_path("../Utilities/Models"), ".gguf")  # Set your folder path here
        self.dropdown_menu4 = ctk.CTkOptionMenu(self, variable=self.dropdown_var4, 
                                                  values=["None"] + folder_files, 
                                                  corner_radius=0, width=max_width)
        self.dropdown_menu4.pack(padx=20, pady=10, ipady=2)

        # New dropdown for folder selection in ../Assets/Audio
        self.audio_folder_label = ctk.CTkLabel(self, text="Select Audio Folder", text_color="grey")
        self.audio_folder_label.pack(pady=(20, 0))
        self.dropdown_var5 = tk.StringVar(value="None")
        audio_folders = self.list_folders_in_directory(self.resource_path("../Assets/Audio"))  # List of folders in ../Assets/Audio
        self.dropdown_menu5 = ctk.CTkOptionMenu(self, variable=self.dropdown_var5, 
                                                values=["None"] + audio_folders,  # Add "None" as an option
                                                corner_radius=0, width=max_width)
        self.dropdown_menu5.pack(padx=20, pady=10, ipady=2)

        # Add extra space before the buttons
        self.extra_space_label = ctk.CTkLabel(self, text="", text_color="grey")  # Invisible label for spacing
        self.extra_space_label.pack(pady=(20, 0))

        # Two buttons (Stream and Record) side by side
        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.pack(pady=10, padx=20, fill="x")

        self.stream_button = ctk.CTkButton(self.button_frame, text="Stream", command=self.start_stream, corner_radius=0)
        self.stream_button.pack(side="left", expand=True, padx=5, pady=10)

        self.record_button = ctk.CTkButton(self.button_frame, text="Record", command=self.start_record, corner_radius=0)
        self.record_button.pack(side="right", expand=True, padx=5, pady=10)

    def list_files_in_folder(self, folder_path, file_extension):
        """List files in the given folder path that match the specified extension."""
        try:
            files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f)) and f.endswith(file_extension)]
            return files
        except FileNotFoundError:
            print(f"Error: Folder '{folder_path}' not found.")
            return []

    def list_folders_in_directory(self, folder_path):
        """List only folders in the given folder path."""
        try:
            folders = [f for f in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, f))]
            return folders
        except FileNotFoundError:
            print(f"Error: Folder '{folder_path}' not found.")
            return []
        
    def create_random_folder(self, base_path):
        """Creates a random-named folder under the specified base path."""
        random_folder_name = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        random_folder_path = os.path.join(base_path, random_folder_name)
        os.makedirs(random_folder_path, exist_ok=True)
        return random_folder_path

    def start_stream(self):
        """Starts the stream window with the same functionality as the previous 'start_app'."""
        selected_mic_name = self.dropdown_var1.get()
        selected_output_device_name = self.dropdown_var3.get()

        selected_mic_index = next((idx for name, idx in self.microphones if name == selected_mic_name), None)
        selected_output_device_index = next((idx for name, idx in self.output_devices if name == selected_output_device_name), None)

        if selected_output_device_index is None:
            print("Error: No valid output device selected.")
            return

        selected_platform = self.dropdown_var2.get()

        selected_llm = self.dropdown_var4.get()
        if selected_llm == "None":
            selected_llm = None
        else:
            selected_llm = self.resource_path(f"../Utilities/Models/{selected_llm}")

        print(f"Selected File: {selected_llm}")

        self.destroy()
        app = Stream(selected_mic_index, selected_output_device_index, selected_platform, selected_llm)
        app.mainloop()

    def start_record(self):
        """Starts a new record window."""
        selected_audio_folder = self.dropdown_var5.get()

        # If "None" is selected, create a new folder
        if selected_audio_folder == "None":
            selected_audio_folder = self.create_random_folder(self.resource_path("../Assets/Audio"))
        
        print(f"Selected/Generated Audio Folder: {selected_audio_folder}")

        self.destroy()
        record_window = Record(selected_audio_folder)
        record_window.mainloop()

    def destroy(self):
        for after_id in self.after_ids:
            self.after_cancel(after_id)
        super().destroy()

    def resource_path(self, relative_path):
        """Get the absolute path to the resource, works for dev and for PyInstaller."""
        try:
            base_path = sys._MEIPASS
        except AttributeError:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

if __name__ == "__main__":
    start_window = StartWindow()
    start_window.mainloop()