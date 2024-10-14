# HanaAI

こちらは、HanaAIのストリームおよびその他の用途に使用されるPythonコードのリポジトリです。

## インストール

### Windowsの場合

1. リポジトリをクローンします:
    ```bash
    git clone https://github.com/DomainSoftwareOfficial/HanaAI.git
    ```
2. プロジェクトディレクトリに移動します:
    ```bash
    cd HanaAI
    ```
3. 依存関係をインストールします:

    （オプション: 仮想環境を作成します）
    ```bash
    python -m venv myvenv
    .\myvenv\Scripts\activate
    ```

    `requirements.txt`に含まれていない依存関係をインストールします::
    ```bash
    pip install setuptools
    pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/<cuda-version>
    pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/<cuda-version>
    ```

    `<cuda-version>`には以下のいずれかを指定します:

    - cu117: CUDA 11.7
    - cu118: CUDA 11.8
    - cu121: CUDA 12.1
    - cu122: CUDA 12.2
    - cu123: CUDA 12.3
    - cu124: CUDA 12.4
    - cu125: CUDA 12.5

    その後、以下を実行します:
    ```bash
    pip install -r requirements.txt
    ```

4. アプリケーションをビルドします（オプション）:
    ```bash
    python setup.py
    ```

### Linuxの場合

1. リポジトリをクローンします:
    ```bash
    git clone https://github.com/DomainSoftwareOfficial/HanaAI.git
    ```
2. プロジェクトディレクトリに移動します:
    ```bash
    cd HanaAI
    ```
3. 依存関係をインストールします:

    （オプション: 仮想環境を作成します）
    ```bash
    python -m venv myvenv
    ./myvenv/bin/activate
    ```

    `requirements.txt`に含まれていない依存関係をインストールします::
    ```bash
    pip install setuptools
    pip install torch torchvision torchaudio
    CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python
    ```

    その他の依存関係をインストールします:
    ```bash
    pip install -r requirements.txt
    ```

4. アプリケーションをビルドします（オプション）:
    ```bash
    python setup.py
    ```

## 事前準備

1. `.env.sample` を `.env`にリネームします。.
2. 適切な値に変更します。
3. `./Utilities/Models`というフォルダを作成します:
    ```bash
    cd Utilities
    mkdir Models
    ```

### オプション

- [Hugging Face](https://huggingface.co)にアクセスし、拡張子が`.gguf`のモデルをダウンロードして、`./Utilities/Models`に配置します（モデルがChatMLまたはAlpacaを使用していることを確認してください）。
- [text generation webui](https://github.com/oobabooga/text-generation-webui)をセットアップします（プロンプトスタイルをAlpacaまたはChatMLに設定してください）。
- YouTubeビデオのURLを設定する（https://www.youtube.com/watch?v=[Thispart!]）か、`.env`にTwitchの認証情報を設定します（方法は調べてください）。
- ロシア語を学習します（print文はロシア語で出力されます）。

4. [stable diffusion webui](https://github.com/AUTOMATIC1111/stable-diffusion-webui)をセットアップします。
5. `.pth`と`.index`ファイルを作成またはダウンロードして、`./Utilities/Models`に配置します。
6. `./Input`フォルダに以下のファイルを作成します:
    - `negatives.txt`にstable diffusion用のネガティブプロンプトを作成します。
    - `profile.chloe`を作成し、最初の4行は次のようにします:
        ```
        Below is an instruction that describes a task. Write a response that appropriately completes the request.

        \### Instruction:
        Continue the chat dialogue below. Write a single reply for the character "Chloe Hayashi".

        -- or --

        <|im_start|> user
        Continue the chat dialogue below. Write a single reply for the character "Chloe Hayashi".
        [空行、ここにあることを確認してください]
        [空行、ここにあることを確認してください]
        ```

        最初の4行の後に:
        ```
        Chloe Hayashi's Persona: [Type anything, this is the personality]
        ```
    - `profile.hana`を作成し、最初の4行は次のようにします:
        ```
        Below is an instruction that describes a task. Write a response that appropriately completes the request.

        \### Instruction:
        Continue the chat dialogue below. Write a single reply for the character "Hana Busujima".

        -- or --

        <|im_start|> user
        Continue the chat dialogue below. Write a single reply for the character "Hana Busujima".
        [空行、ここにあることを確認してください]
        [空行、ここにあることを確認してください]
        ```

        最初の4行の後に:
        ```
        Hana Busujima's Persona: [Type anything, this is the personality]
        ```

## 使用方法

### ビルドしていない場合

    ```
    cd App
    python main.py  
    ```

### ビルド済みの場合

    ```
    cd Distribution
    .\Stream
    ```