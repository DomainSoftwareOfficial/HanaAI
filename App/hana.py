import re
import emoji
import customtkinter as ctk
import tkinter as tk
import os
import sys
from dotenv import load_dotenv
import requests
import json

class HWindow(ctk.CTk):
    def __init__(self, app):
        super().__init__()

        self.app = app
        self.title("Hana Chatter")
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

def hana_ai(input_text, model=None):
    """Hana AI logic to handle both local GGUF model and fallback to WebUI."""

    # Load environment variables (e.g., WebUI URL)
    load_dotenv()

    chat_set = os.getenv('Instruction-Set')

    # Use resource_path to access files with PyInstaller compatibility
    instructions_path = resource_path("../Data/Input/profile.hana")
    memory_path = resource_path("../Data/Input/memory.txt")
    rag_path = resource_path("../Data/Input/results.txt")

    # Ensure files are read with UTF-8 encoding
    with open(instructions_path, "r", encoding='utf-8') as file:
        instructions = file.read()

    # Split the instructions into two parts: the first four lines and the rest
    instructions_lines = instructions.splitlines()
    instructions_pt1 = "\n".join(instructions_lines[:4])  # First four lines
    instructions_pt2 = "\n".join(instructions_lines[4:])  # The rest

    with open(memory_path, "r", encoding='utf-8') as file:
        memory = file.read()

    with open(rag_path, "r", encoding='utf-8') as file:
        rag = file.read()

    if chat_set == 'Alpaca':
        prompt = f"{instructions_pt1}\n\n{rag}\n\n{instructions_pt2}\n\n{memory}\n{input_text}\n\n### Response:\nHana Busujima:"
    elif chat_set == 'ChatML':
        prompt = f"{instructions_pt1}\n\n{rag}\n\n{instructions_pt2}\n\n{memory}\n{input_text}<|im_end|>\n<|im_start|>assistant\nHana Busujima:"

    # Check if a model is provided, use it; otherwise, fallback to WebUI
    if model is not None:
        print("Local GGUF model is provided. Using the local model.")
        try:
            response = model(prompt, max_tokens=512, temperature=0.6, top_p=0.8, top_k=50)  # Adjust as needed

            # Process the response
            new_result = response['choices'][0]['text'].replace("\n", "")
            new_result = re.sub(r'\*.*?\*', '', new_result)  # Remove text between asterisks
            new_result = emoji.replace_emoji(new_result, replace='')  # Remove emojis

            new_result = truncate_at_newline(new_result)

            print(f"Hana said (via GGUF): {new_result}")

            append_to_history_file(memory_path, input_text, new_result)

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
            "prompt": prompt,
            "mode": "chat-instruct",
            "instruction_template": "Alpaca",
            "max_tokens": 512,
            "temperature": 0.6,
            "top_p": 0.8,
            "top_k": 50,
        }

        response = requests.post(url, headers=headers, json=data, verify=False)
        if response.status_code == 200:
            results = json.loads(response.content.decode('utf-8'))["choices"][0]["text"]
            new_result = results.replace("\n", "")
            new_result = re.sub(r'\*.*?\*', '', new_result)
            new_result = emoji.replace_emoji(new_result, replace='')

            new_result = truncate_at_newline(new_result)

            print(f"Hana said (via WebUI): {new_result}")

            append_to_history_file(memory_path, input_text, new_result)

            return new_result
        else:
            print(f"WebUI request failed with status code: {response.status_code}")
            return "Failed to connect to WebUI."
    except Exception as e:
        print(f"Error connecting to WebUI: {e}")
        return "WebUI connection error."

# Helper function to truncate at newlines
def truncate_at_newline(text):
    """Truncate the text right before it encounters any newline characters."""
    # Find the first occurrence of newline \n or double newline \n\n
    newline_pos = text.find('\n')
    if newline_pos != -1:
        # Truncate the text before the first newline
        return text[:newline_pos].strip()
    return text.strip()

def append_to_history_file(history_file_path, input_text, new_result):
    """Append the input and output to the history file, keeping only the last 12 lines (6 input-output pairs)."""
    # Clean up the new_result to ensure no leading/trailing spaces or newlines
    new_result = new_result.strip()

    # Create the new entry (input and output, separated by a newline)
    new_entry = f"{input_text}\nHana Busujima: {new_result}\n"

    # Read the current content of the history file
    if os.path.exists(history_file_path):
        with open(history_file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()
    else:
        lines = []

    # Append the new entry
    lines.append(new_entry)

    # Limit the file to 12 lines (6 input-output pairs)
    if len(lines) > 11:
        lines = lines[-11:]  # Keep only the last 12 lines, removing the oldest entries

    # Write the updated content back to the file
    with open(history_file_path, "w", encoding="utf-8") as file:
        file.writelines(lines)

def resource_path(relative_path):
    """ Get the absolute path to the resource, works for dev and for PyInstaller """
    try:
        # If using PyInstaller, sys._MEIPASS will be set to the temporary folder where files are extracted
        base_path = sys._MEIPASS
    except AttributeError:
        # Otherwise, use the current directory
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

if __name__ == "__main__":
    hana_ai("User: JoyKill asks: Hey, how are you!")