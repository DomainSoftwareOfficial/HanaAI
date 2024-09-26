import customtkinter as ctk
import tkinter as tk
import os
from dotenv import load_dotenv
import requests
import json

class CWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Chloe Chatter")
        self.geometry("400x300")
        ctk.set_appearance_mode("dark")  # Dark mode
        ctk.set_default_color_theme("green")  # Green accent

        # Create a frame for the text box and text
        frame = ctk.CTkFrame(self)
        frame.pack(expand=True, fill="both", padx=10, pady=10)

        # Add text label above the text box
        label = ctk.CTkLabel(frame, text="Now Responding:")
        label.pack(pady=(10, 5))  # Padding above and below the label

        # Create a text box
        self.textbox = ctk.CTkTextbox(frame, width=300, height=150, wrap='none')
        self.textbox.pack(padx=10, pady=10)

        # Insert some text into the text box
        self.textbox.insert(tk.END, "")

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        self.destroy()

def chloe_talk(input):
    load_dotenv()

    """Inputs for the Prompt"""

    with open("../Data/Input/profile.chloe", "r", encoding='utf-8') as file:
        instructions = file.read()

    url = f"{os.getenv('Text-Generation')}/v1/completions"
    headers = {"Content-Type": "application/json"}
    data = {
        "prompt": f"{instructions}\nYou: {input}<|im_end|>\n<|im_start_> assistant\nHana Busujima:",
        "mode": "chat-instruct",
        "instruction_template": "ChatML",
        "max_tokens": 512,
    }

    response = requests.post(url, headers=headers, json=data, verify=False)
    if response.status_code == 200:
        results = json.loads(response.content)["choices"][0]["text"]
        new_result = results.replace("\n", "")
        print(f"Hana said: {new_result}")
        return new_result
    else:
        print(f"Request failed with status code: {response.status_code}")
        return "Server's down! Please fix!"