import customtkinter as ctk
import tkinter as tk
from App.gui import App
from App.audio import list_microphones, list_output_devices  

class StartWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Setup")
        self.geometry("300x300")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        self.after_id = None

        # Get the list of available microphones and output devices
        self.microphones = list_microphones()  # Now contains tuples of (name, index)
        self.output_devices = list_output_devices()  # Now contains tuples of (name, index)

        # Extract only the names for the dropdown display
        microphone_names = [name for name, idx in self.microphones]
        output_device_names = [name for name, idx in self.output_devices]

        # Populate the first dropdown with microphone options (only the names)
        self.dropdown_var1 = tk.StringVar(value=microphone_names[0] if microphone_names else "No Microphone")
        self.dropdown_menu1 = ctk.CTkOptionMenu(self, variable=self.dropdown_var1, values=microphone_names if microphone_names else ["No Microphone"], corner_radius=0)
        self.dropdown_menu1.pack(padx=20, pady=10)

        # Populate the second dropdown with output device options (only the names)
        self.dropdown_var3 = tk.StringVar(value=output_device_names[0] if output_device_names else "No Output Device")
        self.dropdown_menu3 = ctk.CTkOptionMenu(self, variable=self.dropdown_var3, values=output_device_names if output_device_names else ["No Output Device"], corner_radius=0)
        self.dropdown_menu3.pack(padx=20, pady=10)

        # Platform selection dropdown
        self.dropdown_var2 = tk.StringVar(value="Youtube")
        self.dropdown_menu2 = ctk.CTkOptionMenu(self, variable=self.dropdown_var2, values=["None", "Youtube", "Twitch", "Both"], corner_radius=0)
        self.dropdown_menu2.pack(padx=20, pady=10)

        # Start button
        self.start_button = ctk.CTkButton(self, text="Start", command=self.start_app, corner_radius=0)
        self.start_button.pack(pady=10, side="bottom", fill="x", padx=20)

    def start_app(self):
        # Get the selected microphone and output device names
        selected_mic_name = self.dropdown_var1.get()
        selected_output_device_name = self.dropdown_var3.get()

        # Find the corresponding indices
        selected_mic_index = next((idx for name, idx in self.microphones if name == selected_mic_name), None)
        selected_output_device_index = next((idx for name, idx in self.output_devices if name == selected_output_device_name), None)

        # Ensure a valid output device index is selected
        if selected_output_device_index is None:
            print("Error: No valid output device selected.")
            return

        # Get the selected platform
        selected_platform = self.dropdown_var2.get()

        # Destroy the start window
        self.destroy()

        # Pass the selected microphone and output device indexes and platform to the App class
        app = App(selected_mic_index, selected_output_device_index, selected_platform)
        app.mainloop()

    def destroy(self):
        # Cancel any pending callbacks before destroying the window
        if self.after_id is not None:
            self.after_cancel(self.after_id)
        super().destroy()

if __name__ == "__main__":
    start_window = StartWindow()
    start_window.mainloop()