import re
import emoji
import customtkinter as ctk
import tkinter as tk
import os
import sys
from dotenv import load_dotenv
import requests
import json
import io
import base64
from PIL import Image, PngImagePlugin, ImageTk
import uuid
import threading
import time
from datetime import datetime

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


class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Main App with Status and Button")
        self.geometry("300x200")
        ctk.set_appearance_mode("dark")  # Dark mode
        ctk.set_default_color_theme("green")  # Green accent

        # Create a status bar (red initially)
        self.status_bar = ctk.CTkLabel(self, text="Waiting for input", fg_color="red", height=30)
        self.status_bar.pack(side="top", fill="x", pady=(0, 10))

        # Create a rectangular button (initially disabled)
        self.button = ctk.CTkButton(self, text="Show Image", state="disabled", command=self.show_image)
        self.button.pack(pady=20)

        # Create an invisible window for showing the image
        self.invisible_window = InvisibleWindow() # Ensure this is correctly creating the window object

        # Image path (initially None)
        self.latest_image = None

        # Start image generation in a separate thread
        self.generate_image_async()

    def generate_image_async(self):
        # Run the image generation in a separate thread
        threading.Thread(target=self.generate_image_thread).start()

    def generate_image_thread(self):
        # Generate the image
        image_path = generate_image("Studious Lad going to school")
        
        self.after(0, self.update_image, image_path)
        print(image_path)

    def update_image(self, image_path):
        self.latest_image = image_path

        if self.latest_image:
            # Update the status bar to green and enable the button
            self.status_bar.configure(text="Image Ready", fg_color="green")
            self.button.configure(state="normal")  # Enable the button

            # Update the invisible window with the latest image
            self.invisible_window.update_latest_image(self.latest_image)
        else:
            print("Failed to generate an image.")
            self.status_bar.configure(text="Image generation failed", fg_color="red")

    def show_image(self):
        # Disable the button while the image is shown
        self.button.configure(state="disabled")

        # Trigger the invisible window to show the image
        self.invisible_window.display_latest_image()

        # Reset the status bar and button after image is shown
        self.after(30000, self.reset_after_image_display)  # Wait for 30 seconds

    def reset_after_image_display(self):
        self.status_bar.configure(text="Waiting for input", fg_color="red")
        self.button.configure(state="normal")  # Enable the button for new inputs

class InvisibleWindow(ctk.CTk):
    def __init__(self):
        super().__init__()  # Initialize the CTk window

        # Correctly create the Toplevel window (this might be where the issue is)
        self.withdraw()  # Make the main window invisible
        self.latest_image = None

        # Set up the image window
        self.setup_image_window()

    def setup_image_window(self):
        # Create a new Toplevel window
        self.image_window = tk.Toplevel(self)  # Link it to the current invisible window
        self.image_window.withdraw()  # Keep it hidden initially
        self.image_window.title("Generated Image")
        self.image_window.geometry("512x512")

        # Make the window borderless and always on top
        self.image_window.overrideredirect(True)
        self.image_window.attributes("-topmost", True)

        # Position the window (ensure this calculation is correct)
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x_position = int(screen_width * 7 / 8) + 256
        y_position = int(screen_height / 2)
        self.image_window.geometry(f"512x512+{x_position}+{y_position}")

        # Create a label in the image window to show the image
        self.image_label = tk.Label(self.image_window)
        self.image_label.pack()

    def update_latest_image(self, image_path):
        self.latest_image = image_path

    def display_latest_image(self):
        if self.latest_image and os.path.exists(self.latest_image):
            try:
                # Load the image
                img = Image.open(self.latest_image)
                img = img.resize((512, 512))

                # Create a persistent reference to the image
                self.image_obj = ImageTk.PhotoImage(img)

                # Update the label with the image
                self.image_label.config(image=self.image_obj)

                # Show the image window
                self.image_window.deiconify()

                # Hide the window after 30 seconds
                self.after(30000, self.image_window.withdraw)

            except Exception as e:
                print(f"Error loading image: {e}")
        else:
            print("No image available or file not found.")
            
def chloe_ai(input_text, model=None):
    """Hana AI logic to handle both local GGUF model and fallback to WebUI."""

    def log_debug(message, width=150):
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


    log_debug("Запуск обработки Chloe AI...")

    # Load environment variables (e.g., WebUI URL)
    load_dotenv()
    log_debug("Переменные окружения загружены.")

    chat_set = os.getenv('Instruction-Set')

    # Use resource_path to access files with PyInstaller compatibility
    instructions_path = resource_path("../Data/Input/profile.chloe")
    rag_path = resource_path("../Data/Input/results.txt")

    log_debug(f"Чтение файлов ввода: {instructions_path}, {rag_path}")

    # Ensure files are read with UTF-8 encoding
    with open(instructions_path, "r", encoding='utf-8') as file:
        instructions = file.read()

    # Split the instructions into two parts: the first four lines and the rest
    instructions_lines = instructions.splitlines()
    instructions_pt1 = "\n".join(instructions_lines[:4])  # First four lines
    instructions_pt2 = "\n".join(instructions_lines[4:])  # The rest

    with open(rag_path, "r", encoding='utf-8') as file:
        rag = file.read()

    log_debug("Файлы успешно прочитаны.")

    if chat_set == 'Alpaca':
        prompt = f"{instructions_pt1}\n\n{rag}\n\n{instructions_pt2}\n{input_text}\n\n### Response:\nChloe Hayashi:"
    elif chat_set == 'ChatML':
        prompt = f"{instructions_pt1}\n\n{rag}\n\n{instructions_pt2}\n{input_text}<|im_end|>\n<|im_start|>assistant\nChloe Hayashi:"

    log_debug(f"Сгенерирована подсказка с использованием {chat_set} набора инструкций.")

    # Check if a model is provided, use it; otherwise, fallback to WebUI
    if model is not None:
        log_debug("Предоставлена локальная модель GGUF. Использование локальной модели.")
        try:
            # Generate response using the local model
            start_time = time.time()
            response = model(prompt, max_tokens=512, temperature=0.6, top_p=0.8, top_k=50)  # Adjust as needed
            end_time = time.time()
            elapsed_time = end_time - start_time

            # Process the response
            new_result = response['choices'][0]['text'].replace("\n", "")
            new_result = re.sub(r'\*.*?\*', '', new_result)  # Remove text between asterisks
            new_result = emoji.replace_emoji(new_result, replace='')  # Remove emojis

            new_result = truncate_at_newline(new_result)

            log_debug(f"Chloe сказала (через GGUF): {new_result} (Обработано за {elapsed_time:.2f} с.)")
            return new_result
        except Exception as e:
            log_debug(f"Ошибка при использовании модели GGUF: {e}")
            return "Error using the local model. Please check the model setup."
    
    # If no local model is provided, fallback to WebUI
    log_debug("Локальная модель не предоставлена. Переход на WebUI.")
    try:
        url = f"{os.getenv('Text-Generation')}/v1/completions"
        headers = {"Content-Type": "application/json"}
        data = {
            "prompt": prompt,
            "mode": "chat-instruct",
            "instruction_template": "Alpaca",
            "temperature": 0.6,
            "max_tokens": 512,
            "temperature": 0.6,
            "top_p": 0.8,
            "top_k": 50,
        }

        start_time = time.time()
        response = requests.post(url, headers=headers, json=data, verify=False)
        end_time = time.time()
        elapsed_time = end_time - start_time

        if response.status_code == 200:
            results = json.loads(response.content.decode('utf-8'))["choices"][0]["text"]
            new_result = results.replace("\n", "")
            new_result = re.sub(r'\*.*?\*', '', new_result)
            new_result = emoji.replace_emoji(new_result, replace='')

            new_result = truncate_at_newline(new_result)

            log_debug(f"Chloe сказала (через WebUI): {new_result} (Обработано за {elapsed_time:.2f} с.)")
            return new_result
        else:
            log_debug(f"Запрос к WebUI завершился с кодом: {response.status_code}")
            return "Failed to connect to WebUI."
    except Exception as e:
        log_debug(f"Ошибка подключения к WebUI: {e}")
        return "WebUI connection error."

def generate_image(prompt):
    # Generate a random filename
    random_filename = f"../Assets/Images/{uuid.uuid4()}.png"
    
    load_dotenv()
    url = os.getenv("Image-Generation")

    negative_prompt_directory = resource_path("../Data/Input/negatives.txt")

    with open(negative_prompt_directory, "r", encoding="utf-8") as file:
        Negative_Prompt = file.read()

    payload = {
        "prompt": f"masterpiece, best quality, very detailed eyes, subject in focus, defined eyes, {prompt}, cinematic lighting",
        "negative_prompt": f"{Negative_Prompt}",
        "sampler_name": "DPM++ 3M SDE",
        "scheduler": "Karras",
        "checkpoint": os.getenv('Stable-Diffusion-Model-Base'),
        # "refiner_checkpoint": os.getenv('Stable-Diffusion-Model-Refiner'),
        # "refiner_switch_at": 0.5,
        "batch_size": 1,
        "width": 512,
        "height": 512,
        "seed": -1,
        "steps": 60,
        "cfg_scale": 7,
    }

    response = requests.post(url=f"{url}/sdapi/v1/txt2img", json=payload)

    if response.status_code == 200:
        try:
            r = response.json()
            if "images" in r:
                for i in r["images"]:
                    image = Image.open(io.BytesIO(base64.b64decode(r["images"][0])))

                    png_payload = {"image": "data:image/png;base64," + i}
                    response2 = requests.post(
                        url=f"{url}/sdapi/v1/png-info", json=png_payload
                    )
                    pnginfo = PngImagePlugin.PngInfo()
                    pnginfo.add_text("parameters", response2.json().get("info"))
                    # Save the image with the random filename
                    image.save(random_filename, pnginfo=pnginfo)
                print(f"Image saved as {random_filename}")
                return random_filename  # Return the saved image path
            else:
                print("'images' key not found in the JSON response.")
                return None
        except json.JSONDecodeError:
            print("Error decoding JSON response.")
            return None
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None

def truncate_at_newline(text):
    """Truncate the text right before it encounters any newline sequences (<0x0A><0x0A> or <0x0A> in the output)."""
    # First, look for double newlines \n\n (corresponding to <0x0A><0x0A>)
    double_newline_pos = text.find('<0x0A><0x0A>')
    if double_newline_pos != -1:
        # Truncate everything after the first occurrence of <0x0A><0x0A>
        return text[:double_newline_pos].strip()
    
    # If no double newline is found, look for a single newline \n (corresponding to <0x0A>)
    single_newline_pos = text.find('<0x0A>')
    if single_newline_pos != -1:
        # Truncate everything after the first occurrence of <0x0A>
        return text[:single_newline_pos].strip()

    # If no newlines are found, return the original text
    return text.strip()

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
    # Initialize and start the main app
    app = MainApp()

    # Start the app loop
    app.mainloop()