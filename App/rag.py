import requests
import urllib.parse
import os
import subprocess
import sys
import shlex  # Import shlex for quoting shell arguments
from datetime import datetime

class RAG:
    def __init__(self, params):
        self.params_file = params
        self.load_params()

    def load_params(self):
        try:
            with open(self.params_file, 'r', encoding='utf-8') as file:
                self.params = {}
                for line in file:
                    if ":" in line:
                        key, value = line.strip().split(":", 1)
                        self.params[key.strip()] = value.strip()
        except FileNotFoundError:
            self.params = {}

        default_params = {
            "activate": "True",
            "url": "https://lite.duckduckgo.com/lite/?q=%q",
            "start": "[ Next Page > ]",
            "end": "\n10.",
            "max": "8000",
            "data": "",
            # Use os.path.join for compatibility across operating systems
            "output_file": resource_path('../Data/Input/results.txt'),
        }
        
        for key, value in default_params.items():
            self.params.setdefault(key, value)

    def save_params(self):
        with open(self.params_file, "w", encoding="utf-8") as f:
            for key, value in self.params.items():
                f.write(f"{key}: {value}\n")

    def get_context(self, query):
        if len(query) > 0:
            # URL encode the query string
            query = urllib.parse.quote(query)  # Properly encode the query
            url = self.params["url"].replace("%q", query)

        # Safely quote the URL for shell execution
        command = f"wsl links -dump {shlex.quote(url)}"  # Use shlex.quote to escape the URL
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        output, _ = process.communicate()
        search_context = output.decode("utf-8")

        if len(self.params["start"]) > 0:
            start = search_context.find(self.params["start"])
            if start < 0:
                start = 0
            else:
                start = start + len(self.params["start"])
            search_context = search_context[start:]

        if len(self.params["end"]) > 0:
            end = search_context.find(self.params["end"])
            if end < 0:
                end = int(self.params["max"])
        else:
            end = int(self.params["max"])
        search_context = search_context[:end]
        return search_context

    def generate_prompt(self, input_text):
        user_prompt = input_text

        if self.params["activate"].lower() == "true":
            retrieved = self.get_context(user_prompt)
            if len(retrieved) > 0:
                self.params["data"] += retrieved
                self.save_params()
                self.print_results(retrieved)
                
    def print_results(self, data):
        # Ensure the directory exists before writing to it
        output_dir = os.path.dirname(self.params["output_file"])
        os.makedirs(output_dir, exist_ok=True)
        
        with open(self.params["output_file"], 'w', encoding='utf-8') as file:
            file.write(data)

def resource_path(relative_path):
    """ Get the absolute path to the resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def mainrag(search_query):
    # Ensure the directory for parameters exists in Linux/WSL
    params_file = resource_path('../Data/Input/parameters.txt')
    rag = RAG(params_file)
    rag.generate_prompt(search_query)
    log_debug(f"Results have been written to {rag.params['output_file']}")

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


if __name__ == "__main__":
    mainrag()
