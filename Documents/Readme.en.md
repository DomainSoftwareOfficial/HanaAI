# HanaAI

This is the repository for HanaAI's Python code for streams and other uses.

## Installation

### For Windows

1. Clone the repository:
    ```bash
    git clone https://github.com/DomainSoftwareOfficial/HanaAI.git
    ```
2. Navigate to the project directory:
    ```bash
    cd HanaAI
    ```
3. Install dependencies:

    Optional (Make a virtual environment):
    ```bash
    python -m venv myvenv
    .\myvenv\Scripts\activate
    ```

    Install dependencies not in `requirements.txt`:
    ```bash
    pip install setuptools
    pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/<cuda-version>
    pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/<cuda-version>
    ```

    Where `<cuda-version>` is one of the following:

    - cu117: CUDA 11.7
    - cu118: CUDA 11.8
    - cu121: CUDA 12.1
    - cu122: CUDA 12.2
    - cu123: CUDA 12.3
    - cu124: CUDA 12.4
    - cu125: CUDA 12.5

    Then run:
    ```bash
    pip install -r requirements.txt
    ```

4. Build the application (optional):
    ```bash
    python setup.py
    ```

### For Linux

1. Clone the repository:
    ```bash
    git clone https://github.com/DomainSoftwareOfficial/HanaAI.git
    ```
2. Navigate to the project directory:
    ```bash
    cd HanaAI
    ```
3. Install dependencies:

    Optional (Make a virtual environment):
    ```bash
    python -m venv myvenv
    ./myvenv/bin/activate
    ```

    Install dependencies not in `requirements.txt`:
    ```bash
    pip install setuptools
    pip install torch torchvision torchaudio
    CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python
    ```

    Install the rest of the dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4. Build the application (optional):
    ```bash
    python setup.py
    ```

## Preusage

1. Rename `.env.sample` to `.env`.
2. Change values to the ones you deem correct.
3. Create a folder called `./Utilities/Models`:
    ```bash
    cd Utilities
    mkdir Models
    ```

### Optional

- Go to [Hugging Face](https://huggingface.co) and download a model with the extension `.gguf` and place it under `./Utilities/Models` (Make sure the model uses ChatML or Alpaca).
- Set up [text generation webui](https://github.com/oobabooga/text-generation-webui) (Ensure the prompt style is set to Alpaca or ChatML).
- Set YouTube video URL (https://www.youtube.com/watch?v=[Thispart!]) or set Twitch credentials in `.env` (Look it up).
- Learn Russian (print statements are in Russian).

4. Set up [stable diffusion webui](https://github.com/AUTOMATIC1111/stable-diffusion-webui).
5. Create or download a `.pth` and `.index` file and place it under `./Utilities/Models`.
6. Create files under `./Input`:
    - Create negative prompts for stable diffusion under `negatives.txt`.
    - Create `profile.chloe` with the first four lines looking like:
        ```
        Below is an instruction that describes a task. Write a response that appropriately completes the request.

        \### Instruction:
        Continue the chat dialogue below. Write a single reply for the character "Chloe Hayashi".

        -- or --

        <|im_start|> user
        Continue the chat dialogue below. Write a single reply for the character "Chloe Hayashi".
        [blank line just make sure it's here]
        [blank line just make sure it's here]
        ```

        After the first four lines:
        ```
        Chloe Hayashi's Persona: [Type anything, this is the personality]
        ```
    - Create `profile.hana` with the first four lines looking like:
        ```
        Below is an instruction that describes a task. Write a response that appropriately completes the request.

        \### Instruction:
        Continue the chat dialogue below. Write a single reply for the character "Hana Busujima".

        -- or --

        <|im_start|> user
        Continue the chat dialogue below. Write a single reply for the character "Hana Busujima".
        [blank line just make sure it's here]
        [blank line just make sure it's here]
        ```

        After the first four lines:
        ```
        Hana Busujima's Persona: [Type anything, this is the personality]
        ```

## Usage

### If not built
    ```
    cd App
    python main.py  
    ```

### If built
    ```
    cd Distribution
    .\Stream
    ```