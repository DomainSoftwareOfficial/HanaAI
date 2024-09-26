from gtts import gTTS
from pydub import AudioSegment
import io
import numpy as np
import librosa
import pyaudio
import wave
import numpy as np
from pydub import AudioSegment
from pydub.playback import _play_with_simpleaudio
import os
import warnings
from dotenv import load_dotenv
from transformers import MarianMTModel, MarianTokenizer
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException
import sounddevice as sd
# Mapping for supported languages and models

load_dotenv()

TOKEN = os.getenv('HF-Token')

DetectorFactory.seed = 0  # To make language detection consistent

# Mapping for supported languages and models
LANGUAGE_MODEL_MAP = {
    'en': {
        'es': 'Helsinki-NLP/opus-mt-en-es',
        'ja': 'Helsinki-NLP/opus-mt-en-jap',
        'ru': 'Helsinki-NLP/opus-mt-en-ru',
    },
    'es': {
        'en': 'Helsinki-NLP/opus-mt-es-en',
        'ru': 'Helsinki-NLP/opus-mt-es-ru',
    },
    'ja': {
        'en': 'Helsinki-NLP/opus-mt-jap-en',
        'es': 'Helsinki-NLP/opus-mt-ja-es',
        'ru': 'Helsinki-NLP/opus-mt-ja-ru',
    },
    'ru': {
        'en': 'Helsinki-NLP/opus-mt-ru-en',
        'es': 'Helsinki-NLP/opus-mt-ru-es',
    }
}


def tts_en(text, speed_up_factor=1.2, output_path='../Assets/Audio/ai.wav', gain_dB=5):
    """
    Convert text to speech, adjust the speed and volume (without pitch shift), and save it to a file.
    
    Args:
        text (str): Text to convert to speech.
        speed_up_factor (float): Factor to speed up the audio.
        output_path (str): Path to save the output audio file.
        gain_dB (int): Decibel gain to increase the loudness of the output.
    """
    # Convert text to speech using gTTS
    tts = gTTS(text=text, lang='en')
    
    # Save the speech to a temporary file-like object
    with io.BytesIO() as fp:
        tts.write_to_fp(fp)
        fp.seek(0)
        
        # Load the audio file with pydub
        audio = AudioSegment.from_file(fp, format='mp3')
        
        # Speed up the audio
        sped_up_audio = audio.speedup(playback_speed=speed_up_factor)
        
        # Increase the volume by the specified gain in dB
        louder_audio = sped_up_audio + gain_dB
        
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save the adjusted audio to a file
        louder_audio.export(output_path, format='wav')


def tts_ru(text, speed_up_factor=1.2, output_path='../Assets/Audio/ai.wav', gain_dB=5):
    """
    Convert text to speech in Russian, adjust the speed and volume (without pitch shift), and save it to a file.
    
    Args:
        text (str): Text to convert to speech.
        speed_up_factor (float): Factor to speed up the audio.
        output_path (str): Path to save the output audio file.
        gain_dB (int): Decibel gain to increase the loudness of the output.
    """
    # Convert text to speech using gTTS
    tts = gTTS(text=text, lang='ru')
    
    # Save the speech to a temporary file-like object
    with io.BytesIO() as fp:
        tts.write_to_fp(fp)
        fp.seek(0)
        
        # Load the audio file with pydub
        audio = AudioSegment.from_file(fp, format='mp3')
        
        # Speed up the audio
        sped_up_audio = audio.speedup(playback_speed=speed_up_factor)
        
        # Increase the volume by the specified gain in dB
        louder_audio = sped_up_audio + gain_dB
        
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save the adjusted audio to a file
        louder_audio.export(output_path, format='wav')


def tts_es(text, speed_up_factor=1.2, output_path='../Assets/Audio/ai.wav', gain_dB=5):
    """
    Convert text to speech in Spanish, adjust the speed and volume (without pitch shift), and save it to a file.
    
    Args:
        text (str): Text to convert to speech.
        speed_up_factor (float): Factor to speed up the audio.
        output_path (str): Path to save the output audio file.
        gain_dB (int): Decibel gain to increase the loudness of the output.
    """
    # Convert text to speech using gTTS
    tts = gTTS(text=text, lang='es')
    
    # Save the speech to a temporary file-like object
    with io.BytesIO() as fp:
        tts.write_to_fp(fp)
        fp.seek(0)
        
        # Load the audio file with pydub
        audio = AudioSegment.from_file(fp, format='mp3')
        
        # Speed up the audio
        sped_up_audio = audio.speedup(playback_speed=speed_up_factor)
        
        # Increase the volume by the specified gain in dB
        louder_audio = sped_up_audio + gain_dB
        
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save the adjusted audio to a file
        louder_audio.export(output_path, format='wav')


def tts_ja(text, speed_up_factor=1.2, output_path='../Assets/Audio/ai.wav', gain_dB=5):
    """
    Convert text to speech in Japanese, adjust the speed and volume (without pitch shift), and save it to a file.
    
    Args:
        text (str): Text to convert to speech.
        speed_up_factor (float): Factor to speed up the audio.
        output_path (str): Path to save the output audio file.
        gain_dB (int): Decibel gain to increase the loudness of the output.
    """
    # Convert text to speech using gTTS
    tts = gTTS(text=text, lang='ja')
    
    # Save the speech to a temporary file-like object
    with io.BytesIO() as fp:
        tts.write_to_fp(fp)
        fp.seek(0)
        
        # Load the audio file with pydub
        audio = AudioSegment.from_file(fp, format='mp3')
        
        # Speed up the audio
        sped_up_audio = audio.speedup(playback_speed=speed_up_factor)
        
        # Increase the volume by the specified gain in dB
        louder_audio = sped_up_audio + gain_dB
        
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save the adjusted audio to a file
        louder_audio.export(output_path, format='wav')


def list_microphones():
    microphones = []
    devices = sd.query_devices()

    for idx, device in enumerate(devices):
        # Check if the device is an input device (microphone)
        if device['max_input_channels'] > 0:
            microphones.append(f"{device['name']} (Index: {idx})")
    
    return microphones

def list_output_devices():
    output_devices = []
    devices = sd.query_devices()

    for idx, device in enumerate(devices):
        # Check if the device is an output device (speaker/headphone)
        if device['max_output_channels'] > 0:
            output_devices.append(f"{device['name']} (Index: {idx})")
    
    return output_devices

def record_audio(output_file, mic_index, sample_rate=44100, chunk_size=1024, record_seconds=10):
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=sample_rate,
                    input=True,
                    input_device_index=mic_index,
                    frames_per_buffer=chunk_size)
    print("* recording")
    frames = []
    for i in range(0, int(sample_rate / chunk_size * record_seconds)):
        data = stream.read(chunk_size, exception_on_overflow=False)
        frames.append(data)
    print("* done recording")
    stream.stop_stream()
    stream.close()
    p.terminate()
    wf = wave.open(output_file, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
    wf.setframerate(sample_rate)
    wf.writeframes(b''.join(frames))
    wf.close()

def ensure_models_downloaded():
    """
    Ensure that all models in the LANGUAGE_MODEL_MAP are downloaded.
    """
    for src_lang, targets in LANGUAGE_MODEL_MAP.items():
        for target_lang, model_name in targets.items():
            model_dir = os.path.join(os.path.expanduser("~/.cache/huggingface/transformers"), model_name.replace("/", "_"))
            if not os.path.exists(model_dir):
                print(f"Downloading model: {model_name}")
                # Load model to trigger download
                MarianMTModel.from_pretrained(model_name)
                print(f"Model {model_name} downloaded successfully.")
            else:
                print(f"Model {model_name} already exists.")


def translate(text, target_lang):
    try:
        # Step 1: Detect the source language
        src_lang = detect(text)

        # Step 2: Check if the detected language is supported in the LANGUAGE_MODEL_MAP
        if src_lang not in LANGUAGE_MODEL_MAP or target_lang not in LANGUAGE_MODEL_MAP.get(src_lang, {}):
            print(f"Language pair '{src_lang}' to '{target_lang}' not supported. Assuming input is in English.")
            src_lang = 'en'  # Default to English as the source language

        # Step 3: Check if there's a model for translation from English to the target language
        if target_lang not in LANGUAGE_MODEL_MAP.get(src_lang, {}):
            print(f"Cannot find a translation model for '{src_lang}' to '{target_lang}'. Returning the original text.")
            return text

        # Step 4: Load the model and tokenizer for the detected language pair (or English to target language)
        model_name = LANGUAGE_MODEL_MAP[src_lang][target_lang]
        tokenizer = MarianTokenizer.from_pretrained(model_name)
        model = MarianMTModel.from_pretrained(model_name)

        # Step 5: Tokenize the input text
        inputs = tokenizer(text, return_tensors="pt", padding=True)

        # Step 6: Perform the translation
        translated = model.generate(**inputs)

        # Step 7: Decode the translated text
        translated_text = tokenizer.batch_decode(translated, skip_special_tokens=True, clean_up_tokenization_spaces=True)

        return translated_text[0]

    except LangDetectException:
        print("Language could not be detected. Returning the original text.")
        return text


def check_wav_properties(file_path):
    audio = AudioSegment.from_file(file_path)
    print(f"Channels: {audio.channels}")
    print(f"Sample width: {audio.sample_width}")
    print(f"Frame rate (sample rate): {audio.frame_rate}")
    print(f"Frame width: {audio.frame_width}")
    print(f"Length (ms): {len(audio)}")



def play(file_path, output_device_index=None):
    try:
        # Load the WAV file
        audio = AudioSegment.from_file(file_path)

        # Resample the audio to 48000 Hz, 16-bit, stereo
        resampled_audio = audio.set_frame_rate(48000).set_sample_width(2).set_channels(2)

        # Convert audio to numpy array for playback with sounddevice
        audio_data = np.array(resampled_audio.get_array_of_samples())
        audio_data = audio_data.astype(np.float32) / (2 ** 15)  # Normalize the audio data

        # If no output device index provided, use default output device
        if output_device_index is None:
            output_device_index = sd.default.device['output']

        # Get information about the selected output device
        device_info = sd.query_devices(output_device_index, 'output')
        expected_channels = device_info['max_output_channels']

        # Ensure the audio has the correct number of channels
        if resampled_audio.channels != expected_channels:
            print(f"Resampling to match the output device channels: {expected_channels} channels.")
            resampled_audio = resampled_audio.set_channels(expected_channels)

        # Play the resampled audio using the selected output device
        sd.play(audio_data, samplerate=resampled_audio.frame_rate, device=output_device_index)
        sd.wait()  # Wait until audio is finished playing

    except Exception as e:
        print(f"An error occurred while trying to play the audio: {e}")


        
if __name__ == "__main__":
    ensure_models_downloaded()
