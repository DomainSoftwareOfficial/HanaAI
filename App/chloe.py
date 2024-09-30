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

    def update_textbox(self, new_text):
        # Only update if the new_text is different from the current content
        current_text = self.textbox.get("1.0", tk.END).strip()
        if new_text != current_text:
            self.textbox.delete("1.0", tk.END)
            self.textbox.insert(tk.END, new_text)

def chloe_ai(input_text, model=None):
    """Hana AI logic to handle both local GGUF model and fallback to WebUI."""

    # Load environment variables (e.g., WebUI URL)
    load_dotenv()

    # Use resource_path to access files with PyInstaller compatibility
    instructions_path = resource_path("../Data/Input/profile.chloe")
    rag_path = resource_path("../Data/Input/results.txt")

    # Ensure files are read with UTF-8 encoding
    with open(instructions_path, "r", encoding='utf-8') as file:
        instructions = file.read()

    with open(rag_path, "r", encoding='utf-8') as file:
        rag = file.read()

    prompt = f"{instructions}\nYou: {input_text}\n\n### Response:\nChloe Hayashi:"

    # Check if a model is provided, use it; otherwise, fallback to WebUI
    if model is not None:
        print("Local GGUF model is provided. Using the local model.")
        try:
            # Generate response using the local model
            response = model(prompt, max_tokens=100, temperature=0.6, top_p=0.9)  # Adjust as needed

            # Process the response
            new_result = response['choices'][0]['text'].replace("\n", "")
            new_result = re.sub(r'\*.*?\*', '', new_result)  # Remove text between asterisks
            new_result = emoji.replace_emoji(new_result, replace='')  # Remove emojis

            print(f"Chloe said (via GGUF): {new_result}")
            return new_result
        except Exception as e:
            print(f"Error using GGUF model: {e}")
            return "Error using the local model. Please check the model setup."
    
    # If no local model is provided, fallback to WebUI
    print("No local model provided. Falling back to WebUI.")
    try:
        url = f"{os.getenv('Text-Generation')}/v1/completions"
        headers = {"Content-Type": "application/json"}
        data = {
            "prompt": f"{instructions}\nYou: {input_text}\n\n### Response:\nChloe Hayashi:",
            "mode": "chat-instruct",
            "instruction_template": "Alpaca",
            "temperature": 0.6,
            "max_tokens": 100,
        }

        response = requests.post(url, headers=headers, json=data, verify=False)
        if response.status_code == 200:
            results = json.loads(response.content.decode('utf-8'))["choices"][0]["text"]
            new_result = results.replace("\n", "")
            new_result = re.sub(r'\*.*?\*', '', new_result)
            new_result = emoji.replace_emoji(new_result, replace='')

            print(f"Chloe said (via WebUI): {new_result}")
            return new_result
        else:
            print(f"WebUI request failed with status code: {response.status_code}")
            return "Failed to connect to WebUI."
    except Exception as e:
        print(f"Error connecting to WebUI: {e}")
        return "WebUI connection error."

def resource_path(relative_path):
    """ Get the absolute path to the resource, works for dev and for PyInstaller """
    try:
        # If using PyInstaller, sys._MEIPASS will be set to the temporary folder where files are extracted
        base_path = sys._MEIPASS
    except AttributeError:
        # Otherwise, use the current directory
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)