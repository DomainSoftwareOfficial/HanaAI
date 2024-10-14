# HanaAI

Este es el repositorio del código en Python de HanaAI para transmisiones y otros usos.

## Instalación

### Para Windows

1. Clonar el repositorio:
    ```bash
    git clone https://github.com/DomainSoftwareOfficial/HanaAI.git
    ```
2. Navegar al directorio del proyecto:
    ```bash
    cd HanaAI
    ```
3. Instalar las dependencias:

    Opcional (Crear un entorno virtual):
    ```bash
    python -m venv myvenv
    .\myvenv\Scripts\activate
    ```

    Instalar dependencias no incluidas en `requirements.txt`:
    ```bash
    pip install setuptools
    pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/<cuda-version>
    pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/<cuda-version>
    ```

    Donde `<cuda-version>` es una de las siguientes:

    - cu117: CUDA 11.7
    - cu118: CUDA 11.8
    - cu121: CUDA 12.1
    - cu122: CUDA 12.2
    - cu123: CUDA 12.3
    - cu124: CUDA 12.4
    - cu125: CUDA 12.5

    Luego ejecutar:
    ```bash
    pip install -r requirements.txt
    ```

4. Construir la aplicación (opcional):
    ```bash
    python setup.py
    ```

### Para Linux

1. Clonar el repositorio:
    ```bash
    git clone https://github.com/DomainSoftwareOfficial/HanaAI.git
    ```
2. Navegar al directorio del proyecto:
    ```bash
    cd HanaAI
    ```
3. Instalar las dependencias:

    Opcional (Crear un entorno virtual):
    ```bash
    python -m venv myvenv
    ./myvenv/bin/activate
    ```

    Instalar dependencias no incluidas en `requirements.txt`:
    ```bash
    pip install setuptools
    pip install torch torchvision torchaudio
    CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python
    ```

    Instalar el resto de las dependencias:
    ```bash
    pip install -r requirements.txt
    ```

4. Construir la aplicación (opcional):
    ```bash
    python setup.py
    ```

## Preuso

1. Renombrar `.env.sample` a `.env`.
2. Crear una carpeta llamada `./Utilities/Models`:
    ```bash
    cd Utilities
    mkdir Models
    ```

### Opcional

- Ve a [Hugging Face](https://huggingface.co) y descarga un modelo con la extensión `.gguf` y colócalo en `./Utilities/Models` (Asegúrate de que el modelo use ChatML o Alpaca).
- Configura [text generation webui](https://github.com/oobabooga/text-generation-webui) (Asegúrate de que el estilo de prompt esté configurado a Alpaca o ChatML).
- Establece la URL de un video de YouTube (https://www.youtube.com/watch?v=[EstaParte!]) o configura las credenciales de Twitch en `.env` (Búscalo).
- Aprende ruso (los mensajes de impresión están en ruso).

3. Configura [stable diffusion webui](https://github.com/AUTOMATIC1111/stable-diffusion-webui).
4. Crea o descarga un archivo `.pth` y un archivo `.index` y colócalos en `./Utilities/Models`.
5. Crea archivos en `./Input`:
    - Crea prompts negativos para stable diffusion en `negatives.txt`.
    - Crea `profile.chloe` con las primeras cuatro líneas así:
        ```
        Below is an instruction that describes a task. Write a response that appropriately completes the request.

        \### Instruction:
        Continue the chat dialogue below. Write a single reply for the character "Chloe Hayashi".

        -- or --

        <|im_start|> user
        Continue the chat dialogue below. Write a single reply for the character "Chloe Hayashi".
        [Línea en blanco, solo asegúrate de que esté aquí]
        [Línea en blanco, solo asegúrate de que esté aquí]
        ```

        Después de las primeras cuatro líneas:
        ```
        Chloe Hayashi's Persona: [Type anything, this is the personality]
        ```
    - Crea `profile.hana` con las primeras cuatro líneas así:
        ```
        Below is an instruction that describes a task. Write a response that appropriately completes the request.

        \### Instruction:
        Continue the chat dialogue below. Write a single reply for the character "Hana Busujima".

        -- or --

        <|im_start|> user
        Continue the chat dialogue below. Write a single reply for the character "Hana Busujima".
        [Línea en blanco, solo asegúrate de que esté aquí]
        [Línea en blanco, solo asegúrate de que esté aquí]
        ```

        Después de las primeras cuatro líneas:
        ```
        Hana Busujima's Persona: [Type anything, this is the personality]
        ```

6. Cambia los valores a los que consideres correctos.

## Uso

### Si no está construido
    ```
    cd App
    python main.py  
    ```

### Si está construido
    ```
    cd Distribution
    .\Stream
    ```