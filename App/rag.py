import requests
import urllib.parse
import os

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
            # Use os.path.join for Windows path compatibility
            "output_file": os.path.join("..", "Data", "Input", "results.txt"),
        }
        
        for key, value in default_params.items():
            self.params.setdefault(key, value)

    def save_params(self):
        with open(self.params_file, 'w', encoding='utf-8') as file:
            for key, value in self.params.items():
                file.write(f"{key}: {value}\n")

    def fetch_url_content(self, url):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.text
            else:
                return f"Error: HTTP {response.status_code}"
        except requests.RequestException as e:
            return f"Error: {str(e)}"

    def get_context(self, query):
        if len(query) > 0:
            # URL encode the query string to handle special characters
            encoded_query = urllib.parse.quote(query)
            url = self.params["url"].replace("%q", encoded_query)

        search_context = self.fetch_url_content(url)

        # Process the content based on 'start' and 'end' markers
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

def mainrag():
    # Ensure the directory for parameters exists on Windows
    params_file = os.path.join("..", "Data", "Input", "parameters.txt")
    rag = RAG(params_file)
    search_query = "Mouth Breathers"
    rag.generate_prompt(search_query)
    print(f"Results have been written to {rag.params['output_file']}")

if __name__ == "__main__":
    mainrag()
