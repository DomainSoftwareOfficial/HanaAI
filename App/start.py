import customtkinter as ctk
import tkinter as tk
from gui import App
from audio import list_microphones, list_output_devices  

class StartWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Setup")
        self.geometry("300x300")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        self.after_id = None  # Store after callback ID

        # Get the list of available microphones and output devices
        self.microphones = list_microphones()
        self.output_devices = list_output_devices()

        # Populate the first dropdown with microphone options
        self.dropdown_var1 = tk.StringVar(value=self.microphones[0] if self.microphones else "No Microphone")
        self.dropdown_menu1 = ctk.CTkOptionMenu(self, variable=self.dropdown_var1, values=self.microphones if self.microphones else ["No Microphone"], corner_radius=0)
        self.dropdown_menu1.pack(padx=20, pady=10)

        # Populate the second dropdown with output device options
        self.dropdown_var3 = tk.StringVar(value=self.output_devices[0] if self.output_devices else "No Output Device")
        self.dropdown_menu3 = ctk.CTkOptionMenu(self, variable=self.dropdown_var3, values=self.output_devices if self.output_devices else ["No Output Device"], corner_radius=0)
        self.dropdown_menu3.pack(padx=20, pady=10)

        self.dropdown_var2 = tk.StringVar(value="Youtube")
        self.dropdown_menu2 = ctk.CTkOptionMenu(self, variable=self.dropdown_var2, values=["None", "Youtube", "Twitch", "Both"], corner_radius=0)
        self.dropdown_menu2.pack(padx=20, pady=10)

        self.start_button = ctk.CTkButton(self, text="Start", command=self.start_app, corner_radius=0)
        self.start_button.pack(pady=10, side="bottom", fill="x", padx=20)

    def start_app(self):
        # Get the selected microphone and output device
        selected_mic = self.dropdown_var1.get()
        selected_mic_index = self.microphones.index(selected_mic) if selected_mic in self.microphones else None

        selected_output_device = self.dropdown_var3.get()
        selected_output_device_index = self.output_devices.index(selected_output_device) if selected_output_device in self.output_devices else None

        # Ensure an output device index is selected (check it's not None)
        if selected_output_device_index is None:
            print("Error: No valid output device selected.")
            return

        # Get the selected platform
        selected_platform = self.dropdown_var2.get()

        self.destroy()  # Close the start window

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