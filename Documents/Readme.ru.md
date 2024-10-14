# HanaAI

Это репозиторий для Python-кода HanaAI для потоков и других целей.

## Установка

### Для Windows

1. Клонируйте репозиторий:
    ```bash
    git clone https://github.com/DomainSoftwareOfficial/HanaAI.git
    ```
2. Перейдите в каталог проекта:
    ```bash
    cd HanaAI
    ```
3. Установите зависимости:

    Опционально (создайте виртуальное окружение):
    ```bash
    python -m venv myvenv
    .\myvenv\Scripts\activate
    ```

    Установите зависимости, которых нет в `requirements.txt`:
    ```bash
    pip install setuptools
    pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/<cuda-version>
    pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/<cuda-version>
    ```

    Где `<cuda-version>` — одна из следующих версий:

    - cu117: CUDA 11.7
    - cu118: CUDA 11.8
    - cu121: CUDA 12.1
    - cu122: CUDA 12.2
    - cu123: CUDA 12.3
    - cu124: CUDA 12.4
    - cu125: CUDA 12.5

    Затем выполните:
    ```bash
    pip install -r requirements.txt
    ```

4. Соберите приложение (опционально):
    ```bash
    python setup.py
    ```

### Для Linux

1. Клонируйте репозиторий:
    ```bash
    git clone https://github.com/DomainSoftwareOfficial/HanaAI.git
    ```
2. Перейдите в каталог проекта:
    ```bash
    cd HanaAI
    ```
3. Установите зависимости:

    Опционально (создайте виртуальное окружение):
    ```bash
    python -m venv myvenv
    ./myvenv/bin/activate
    ```

    Установите зависимости, которых нет в `requirements.txt`:
    ```bash
    pip install setuptools
    pip install torch torchvision torchaudio
    CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python
    ```

    Установите остальные зависимости:
    ```bash
    pip install -r requirements.txt
    ```

4. Соберите приложение (опционально):
    ```bash
    python setup.py
    ```

## Предварительная настройка

1. Переименуйте `.env.sample` в `.env`.
2. Измените значения на нужные вам.
3. Создайте папку под названием `./Utilities/Models`:
    ```bash
    cd Utilities
    mkdir Models
    ```

### Опционально

- Перейдите на [Hugging Face](https://huggingface.co) и скачайте модель с расширением `.gguf` поместите её в `./Utilities/Models` (убедитесь, что модель использует ChatML или Alpaca).
- Настройте [text generation webui](https://github.com/oobabooga/text-generation-webui) (убедитесь, что стиль запроса установлен на Alpaca или ChatML).
- Укажите URL видео YouTube (https://www.youtube.com/watch?v=[ЭтаЧасть!]) или настройте данные Twitch в `.env` (поискать самостоятельно).

4. Настройте [stable diffusion webui](https://github.com/AUTOMATIC1111/stable-diffusion-webui).
5. Создайте или скачайте файлы `.pth` и `.index` и поместите их в `./Utilities/Models`.
6. Создайте файлы в каталоге `./Input`:
    - Создайте негативные подсказки для stable diffusion в `negatives.txt`.
    - Создайте файл `profile.chloe`, первые четыре строки которого будут такими:
        ```
        Below is an instruction that describes a task. Write a response that appropriately completes the request.

        \### Instruction:
        Continue the chat dialogue below. Write a single reply for the character "Chloe Hayashi".

        -- or --

        <|im_start|> user
        Continue the chat dialogue below. Write a single reply for the character "Chloe Hayashi".
        [пустая строка, убедитесь, что она есть]
        [пустая строка, убедитесь, что она есть]
        ```

        После первых четырёх строк:
        ```
        Chloe Hayashi's Persona: [Type anything, this is the personality]
        ```
    - Создайте файл `profile.hana`, первые четыре строки которого будут такими:
        ```
        Below is an instruction that describes a task. Write a response that appropriately completes the request.

        \### Instruction:
        Continue the chat dialogue below. Write a single reply for the character "Hana Busujima".

        -- or --

        <|im_start|> user
        Continue the chat dialogue below. Write a single reply for the character "Hana Busujima".
        [пустая строка, убедитесь, что она есть]
        [пустая строка, убедитесь, что она есть]
        ```

        После первых четырёх строк:
        ```
        Hana Busujima's Persona: [Type anything, this is the personality]
        ```

## Использование

### Если не собрано

    ```
    cd App
    python main.py  
    ```

### Если собрано

    ```
    cd Distribution
    .\Stream
    ```