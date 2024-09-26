import re
import emoji
import customtkinter as ctk
import tkinter as tk
import os
import sys
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

def hana_ai(input):
    """Chloe AI logic with PyInstaller compatibility."""
    load_dotenv()

    # Use resource_path to access files with PyInstaller compatibility
    instructions_path = resource_path("../Data/Input/profile.chloe")
    memory_path = resource_path("../Data/Input/memory.txt")

    # Ensure files are read with UTF-8 encoding
    with open(instructions_path, "r", encoding='utf-8') as file:
        instructions = file.read()

    with open(memory_path, "r", encoding='utf-8') as file:
        memory = file.read()

    url = f"{os.getenv('Text-Generation')}/v1/completions"
    headers = {"Content-Type": "application/json"}
    data = {
        "prompt": f"{instructions}\n{memory}\nYou: {input}\n\n### Response:\nHana Busujima:",
        "mode": "chat-instruct",
        "instruction_template": "ChatML",
        "max_tokens": 512,
    }

    response = requests.post(url, headers=headers, json=data, verify=False)
    if response.status_code == 200:
        # Ensure the response is properly decoded as UTF-8
        results = json.loads(response.content.decode('utf-8'))["choices"][0]["text"]
        new_result = results.replace("\n", "")

        # Remove any text between asterisks (including the asterisks)
        new_result = re.sub(r'\*.*?\*', '', new_result)

        # Remove emojis
        new_result = emoji.replace_emoji(new_result, replace='')

        print(f"Chloe said: {new_result}")
        return new_result
    else:
        print(f"Request failed with status code: {response.status_code}")
        return "Server's down! Please fix."

def resource_path(relative_path):
    """ Get the absolute path to the resource, works for dev and for PyInstaller """
    try:
        # If using PyInstaller, sys._MEIPASS will be set to the temporary folder where files are extracted
        base_path = sys._MEIPASS
    except AttributeError:
        # Otherwise, use the current directory
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)