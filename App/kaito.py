import customtkinter as ctk
import tkinter as tk
import os
import sys
from dotenv import load_dotenv
import requests
import json
import io
import base64
from PIL import Image, PngImagePlugin
import uuid
import threading
from datetime import datetime

class ImageGenerator(ctk.CTkToplevel):
    def __init__(self, master=None):
        super().__init__(master)
        
        self.prompt_file = resource_path('../Data/Chat/Special/request.chloe')

        # Initialize list to track all scheduled 'after' callbacks
        self.after_ids = []

        # Set up main window
        self.title("Image Control Panel")
        self.geometry("400x500")
        ctk.set_appearance_mode("dark")  # Dark mode
        ctk.set_default_color_theme("green")  # Green theme
        self.attributes("-topmost", True)

        # Create status bar (initially red)
        self.status_bar = ctk.CTkLabel(self, text="Waiting for input", fg_color="red", height=30)
        self.status_bar.pack(side="top", fill="x", pady=(0, 10))

        # Create image display area in main window
        self.image_label = ctk.CTkLabel(self, text="No Image", width=200, height=200)
        self.image_label.pack(pady=10)

        # Create "Show Image" button (initially disabled)
        self.button = ctk.CTkButton(self, text="Show Image", state="disabled", command=self.show_image)
        self.button.pack(pady=20)

        # Initialize invisible window
        self.invisible_window = self.create_invisible_window()

        # Initialize image tracking
        self.latest_image = None
        self.displayed_images = set()

        # Define folder to monitor images
        self.image_folder = self.resource_path("../Assets/Images")  # Adjust path as needed
        os.makedirs(self.image_folder, exist_ok=True)  # Create folder if it doesn't exist

        # Attempt to use Resampling.LANCZOS for resizing
        try:
            self.resample_filter = Image.Resampling.LANCZOS
        except AttributeError:
            self.resample_filter = Image.LANCZOS  # For Pillow < 10.0.0

        # Start monitoring image folder for new files
        self.monitor_image_folder()

        # Handle window close event
        self.protocol("WM_DELETE_WINDOW", self.on_main_window_close)

    def create_invisible_window(self):
        """Create an invisible window to display the image."""
        image_window = tk.Toplevel(self)
        image_window.withdraw()  # Hide window initially
        image_window.title("Generated Image")
        image_window.geometry("512x512")
        image_window.overrideredirect(True)  # Remove window borders
        image_window.attributes("-topmost", True)  # Always on top

        # Position the window at a specific location (e.g., top-right corner)
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x_position = int(screen_width * 7 / 8) + 256  # Adjust for correct positioning
        y_position = int(screen_height / 2)  # Center vertically
        image_window.geometry(f"512x512+{x_position}+{y_position}")

        # Create label to display image
        image_label = ctk.CTkLabel(image_window, width=512, height=512)
        image_label.pack()

        return (image_window, image_label)

    def generate_image_thread(self, prompt):
        # Generate image using the prompt
        image_path = generate_image(prompt)  # Ensure this function is defined

        if image_path and os.path.exists(image_path):
            log_debug(f"Изображение сгенерировано по адресу: {image_path}")
            # Notify main thread about new image
            self.after(0, self.on_new_image_generated, image_path)
        else:
            log_debug("Генерация изображения не удалась или изображение не существует.")
            self.after(0, self.update_status, "Image generation failed", "red")

    def on_new_image_generated(self, image_path):
        """Handle newly generated image."""
        self.display_image_on_main_window(image_path)

    def monitor_image_folder(self):
        """Monitor the image folder for new files."""
        try:
            # List current images in folder
            current_images = set(os.listdir(self.image_folder))
            # Determine new images not yet displayed
            new_images = current_images - self.displayed_images

            if new_images:
                # Process each new image
                for image_name in sorted(new_images):
                    image_path = os.path.join(self.image_folder, image_name)
                    self.display_image_on_main_window(image_path)
                    self.displayed_images.add(image_name)
        except Exception as e:
            log_debug(f"Ошибка при мониторинге папки с изображениями: {e}")

        # Schedule next check in 1 second
        self.safe_after(1000, self.monitor_image_folder)

    def display_image_on_main_window(self, image_path):
        """Display the image in the main window and enable the button."""
        try:
            # Load and resize image
            img = Image.open(image_path)
            img = img.resize((341, 341), self.resample_filter)

            # Convert to CTkImage
            self.image_obj = ctk.CTkImage(light_image=img, dark_image=img, size=(341, 341))

            # Update image label in main window
            self.image_label.configure(image=self.image_obj, text="")

            # Update status bar to indicate readiness
            self.status_bar.configure(text="Image ready", fg_color="green")

            # Save path to latest image
            self.latest_image = image_path

            # Enable "Show Image" button
            self.button.configure(state="normal")
        except Exception as e:
            log_debug(f"Ошибка при отображении изображения в главном окне: {e}")
            self.status_bar.configure(text="Failed to load image", fg_color="red")

    def show_image(self):
        """Display the latest image in the invisible window."""
        if self.latest_image and os.path.exists(self.latest_image):
            try:
                image_window, image_label = self.invisible_window

                # Load image
                img = Image.open(self.latest_image)

                # Resize image for invisible window
                img_resized = img.resize((341, 341), self.resample_filter)
                # Convert to CTkImage
                self.image_obj_invisible = ctk.CTkImage(light_image=img_resized, dark_image=img_resized, size=(341, 341))

                # Update image label in invisible window
                image_label.configure(image=self.image_obj_invisible, text='')

                # Show invisible window
                image_window.deiconify()

                # Optionally, hide invisible window after 30 seconds
                self.safe_after(30000, lambda: image_window.withdraw())

                # Disable the button until a new image is generated
                self.button.configure(state="disabled")

                # Update status bar
                self.status_bar.configure(text="Image displayed", fg_color="blue")

            except Exception as e:
                log_debug(f"Ошибка при отображении изображения в невидимом окне: {e}")
                self.status_bar.configure(text="Failed to display image", fg_color="red")
        else:
            log_debug("Нет доступного изображения или файл не найден.")
            self.status_bar.configure(text="No image to display", fg_color="red")

    def update_status(self, text, color):
        """Update the status bar."""
        self.status_bar.configure(text=text, fg_color=color)

    def on_main_window_close(self):
        """Handle main window closing."""
        # Cancel all scheduled 'after' callbacks
        for after_id in self.after_ids:
            try:
                self.after_cancel(after_id)
            except Exception as e:
                log_debug(f"Ошибка при отмене обратного вызова {after_id}: {e}")
        self.after_ids.clear()

        # Destroy invisible window
        image_window, _ = self.invisible_window
        image_window.destroy()

        # Destroy main window
        self.destroy()

    def resource_path(self, relative_path):
        """Get absolute path to resource, works for dev and PyInstaller."""
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def safe_after(self, delay, func, *args, **kwargs):
        """
        Safely schedule an 'after' callback using try-except.
        Prevents callbacks on destroyed widgets.
        """
        try:
            after_id = self.after(delay, lambda: self.safe_callback(func, *args, **kwargs))
            self.after_ids.append(after_id)  # Track callback ID
        except Exception as e:
            log_debug(f"Ошибка при планировании обратного вызова: {e}")

    def safe_callback(self, func, *args, **kwargs):
        """
        Wrapper for callback functions to handle exceptions.
        """
        try:
            func(*args, **kwargs)
        except Exception as e:
            log_debug(f"Ошибка в обратном вызове: {e}")

def generate_image(prompt):
    # Generate a random filename
    random_filename = f"../Assets/Images/{uuid.uuid4()}.png"
    
    load_dotenv()
    url = os.getenv("Image-Generation")

    negative_prompt_directory = resource_path("../Data/Input/negatives.txt")

    with open(negative_prompt_directory, "r", encoding="utf-8") as file:
        Negative_Prompt = file.read()

    payload = {
        "prompt": f"masterpiece, best quality, subject in focus, detailed eyes, {prompt}, very detailed, professional quality, perfect, beautiful, cinematic, attractive, artistic, sharp focus, dramatic lighting, incredible fine detail, gorgeous, inspired, vibrant, best",
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
                return random_filename  # Return the saved image path
            else:
                log_debug("'images' ключ не найден в JSON ответе.")
                return None
        except json.JSONDecodeError:
            log_debug("Ошибка при декодировании JSON ответа.")
            return None
    else:
        log_debug(f"Ошибка: {response.status_code} - {response.text}")
        return None

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

def resource_path(relative_path):
    """Get path to resource relative to the executable's location."""
    # Get the directory of the executable if frozen (PyInstaller), else use script location
    base_path = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
    return os.path.join(base_path, relative_path)

if __name__ == "__main__":
    app = ImageGenerator()

    trigger_thread = threading.Thread(target=app.generate_image_thread, args=('Cyborg'), daemon=True)
    trigger_thread.start()

    # Start the main Tkinter loop (on the main thread)
    app.mainloop()