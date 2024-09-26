import subprocess
import urllib.parse

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
            "output_file": "../Data/Input/results.txt",
        }
        
        for key, value in default_params.items():
            self.params.setdefault(key, value)

    def save_params(self):
        with open(self.params_file, 'w', encoding='utf-8') as file:
            for key, value in self.params.items():
                file.write(f"{key}: {value}\n")

    def execute_command(self, command):
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = process.communicate()
        if process.returncode == 0:
            return output.decode("utf-8")
        else:
            return f"Error: {error.decode('utf-8')}"

    def get_context(self, query):
        if len(query) > 0:
            # URL encode the query string to handle special characters
            encoded_query = urllib.parse.quote(query)
            url = self.params["url"].replace("%q", encoded_query)

        command = f"links -dump {url}"
        search_context = self.execute_command(command)

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

    def generate_prompt(self, input):
        user_prompt = input

        if self.params["activate"].lower() == "true":
            retrieved = self.get_context(user_prompt)
            if len(retrieved) > 0:
                self.params["data"] += retrieved
                self.save_params()
                self.print_results(retrieved)

    def print_results(self, data):
        with open(self.params["output_file"], 'w', encoding='utf-8') as file:
            file.write(data)

def main():
    params_file = '../Data/Input/parameters.txt'
    rag = RAG(params_file)
    search_query = "MrBeast Controversy"
    rag.generate_prompt(search_query)
    print(f"Results have been written to {rag.params['output_file']}")

if __name__ == "__main__":
    main()