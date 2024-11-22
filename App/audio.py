from gtts import gTTS
from pydub import AudioSegment
import io
import numpy as np
from scipy.io.wavfile import write
import librosa
import pyaudio
import wave
import io
import numpy as np
from pydub import AudioSegment, silence
import os
import re
import time
from dotenv import load_dotenv
from transformers import MarianMTModel, MarianTokenizer
from langdetect import detect, DetectorFactory
import sounddevice as sd
import soundfile as sf
from datetime import datetime
from rvc import mainrvc
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

def log_debug(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"{timestamp} | INFO | {message}")

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


def tts(input_text, banned_words, language='en', banned_audio_path='../Assets/Audio/quack.mp3', output_path='../Assets/Audio/hana.wav', banned_audio_offset=0, speed_up_factor=1.1, gain_dB=5, censor_enabled=True):
    """
    Process text from a string by splitting between banned and non-banned words, generating audio segments
    for each part, and combining them into a single audio file.
    
    Args:
        input_text (str): The input text to process.
        banned_words (list): List of banned words to identify and replace in text.
        language (str): Language for TTS.
        banned_audio_path (str): Path to the audio file used for banned words.
        output_path (str): Final path to save the combined output audio.
        banned_audio_offset (int): Start time (in milliseconds) for slicing the banned audio.
        speed_up_factor (float): Factor to speed up the audio segments without pitch shift.
        gain_dB (int): Decibel gain to increase the loudness of the output.
        censor_enabled (bool): Enable or disable censoring of banned words.
    """
    words = re.findall(r'\S+', input_text)  # Include words and connected characters

    current_text_segment = []
    segments = []
    audio_segments = []
    temp_files = []

    banned_audio_format = banned_audio_path.split('.')[-1]

    for word in words:
        is_banned = censor_enabled and any(banned_word in word for banned_word in banned_words)
        
        if is_banned:
            if current_text_segment:
                segments.append((' '.join(current_text_segment), False))
                current_text_segment = []
            segments.append((word, True))
        else:
            current_text_segment.append(word)

    if current_text_segment:
        segments.append((' '.join(current_text_segment), False))

    for i, (segment_text, is_banned) in enumerate(segments):
        temp_output_path = os.path.join('../Assets/Audio', f'temp_segment_{i}.wav')
        
        if is_banned:
            banned_audio = AudioSegment.from_file(banned_audio_path, format=banned_audio_format)
            fixed_censor_duration = 300  # Fixed duration in milliseconds for the censor sound
            sliced_banned_audio = banned_audio[banned_audio_offset:banned_audio_offset + fixed_censor_duration]
            audio_segments.append(sliced_banned_audio)
        else:
            tts_audio = gTTS(text=segment_text, lang=language)
            with io.BytesIO() as fp:
                tts_audio.write_to_fp(fp)
                fp.seek(0)
                audio = AudioSegment.from_file(fp, format='mp3')
                
                # Detect and trim silence
                silent_ranges = silence.detect_silence(audio, min_silence_len=100, silence_thresh=-50)
                if silent_ranges:
                    start_trim = silent_ranges[0][1] if silent_ranges[0][0] == 0 else 0
                    end_trim = silent_ranges[-1][0] if silent_ranges[-1][1] == len(audio) else len(audio)
                    trimmed_audio = audio[start_trim:end_trim]
                else:
                    trimmed_audio = audio
                
                # Speed up and amplify
                sped_up_audio = trimmed_audio.speedup(playback_speed=speed_up_factor)
                louder_audio = sped_up_audio + gain_dB
                louder_audio.export(temp_output_path, format='wav')
                
            # Apply mainrvc processing
            mainrvc(temp_output_path, temp_output_path)
            normalize(temp_output_path)
            
            final_temp_output_path = os.path.join(os.path.dirname(output_path), f'temp_segment_{i}.wav')
            if os.path.exists(temp_output_path):
                os.rename(temp_output_path, final_temp_output_path)
            
            processed_audio = AudioSegment.from_file(final_temp_output_path, format='wav')
            segment_audio = (processed_audio + gain_dB).speedup(playback_speed=speed_up_factor)
            
            # Check for punctuation and add silence if present
            if segment_text[-1] in '.?!':
                silence_duration = AudioSegment.silent(duration=300)  # 300 ms pause
                segment_audio = segment_audio + silence_duration

            audio_segments.append(segment_audio)
        
        temp_files.append(final_temp_output_path)

    # Combine with crossfade
    combined_audio = audio_segments[0]
    for next_segment in audio_segments[1:]:
        combined_audio = combined_audio.append(next_segment, crossfade=50)  # 50ms crossfade for smooth transitions
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    combined_audio.export(output_path, format='wav')
    
    for temp_file in temp_files:
        if os.path.exists(temp_file):
            os.remove(temp_file)
            
# Function to convert pydub AudioSegment to numpy array for librosa
def audiosegment_to_np(audio_segment):
    samples = np.array(audio_segment.get_array_of_samples())
    if audio_segment.channels == 2:  # Stereo
        samples = samples.reshape((-1, 2)).T
    return samples.astype(np.float32) / np.iinfo(np.int16).max  # Normalize to [-1.0, 1.0]

# Function to convert numpy array back to pydub AudioSegment
def np_to_audiosegment(samples, sample_rate, sample_width, channels):
    samples = (samples * np.iinfo(np.int16).max).astype(np.int16)  # De-normalize
    if channels == 2:  # Stereo
        samples = np.stack((samples[0], samples[1]), axis=-1)
    return AudioSegment(
        samples.tobytes(), 
        frame_rate=sample_rate, 
        sample_width=sample_width, 
        channels=channels
    )

# Function to change the pitch of the audio without altering speed using librosa
def pitch_shift_preserving_duration(sound, semitones):
    samples = audiosegment_to_np(sound)
    # Perform pitch shifting using librosa
    shifted_samples = librosa.effects.pitch_shift(samples, sr=sound.frame_rate, n_steps=semitones)
    
    # Convert back to AudioSegment
    return np_to_audiosegment(shifted_samples, sound.frame_rate, sound.sample_width, sound.channels)


# Function to loop the static sound if the speech is longer
def loop_static(static, speech_length):
    loops = int(speech_length / len(static)) + 1  # Calculate how many times we need to loop
    return static * loops

def distort(speech_file_path, static_file_path, semitones=2, volume_reduction=0.2, final_output_reduction=0.95, output_file_path="output.wav"):
    # Load the speech audio and static audio
    speech = AudioSegment.from_file(speech_file_path)
    static = AudioSegment.from_file(static_file_path)
    
    # Pitch shift the speech audio without altering the duration
    pitched_speech = pitch_shift_preserving_duration(speech, semitones)
    
    # Loop the static file if the speech is longer
    if len(pitched_speech) > len(static):
        static = loop_static(static, len(pitched_speech))
    
    # Trim or pad the static to match the length of the speech
    static = static[:len(pitched_speech)]
    
    # Adjust the volume of the static audio based on the reduction factor
    if volume_reduction < 1.0:
        db_reduction = 20 * np.log10(volume_reduction)
        static = static + db_reduction  # Apply the calculated decibel reduction
    
    # Overlay the static on top of the pitched speech
    combined = pitched_speech.overlay(static)
    
    # Reduce the volume of the final output by a factor of `final_output_reduction`
    if final_output_reduction < 1.0:
        final_db_reduction = 20 * np.log10(final_output_reduction)
        combined = combined + final_db_reduction  # Reduce the volume of the final output
    
    # Export the resulting audio file
    combined.export(output_file_path, format="wav")
    log_debug(f"Аудио обработано и сохранено в {output_file_path}")

def normalize(audio_path):
    try:
        # Load the audio file with librosa for processing
        y, sr = librosa.load(audio_path, sr=None)

        # Step 1: Noise Reduction - Trim silence or quiet sections
        y_trimmed, _ = librosa.effects.trim(y)

        # Step 2: Time Stretching - Speed up slightly without changing pitch
        y_stretched = librosa.effects.time_stretch(y_trimmed, rate=1.1)

        # Convert the processed numpy array back to an audio segment for filtering adjustments
        temp_output_path = "temp_normalized.wav"
        write(temp_output_path, sr, (y_stretched * 32767).astype(np.int16))
        
        # Reload as AudioSegment for balanced filtering
        processed_audio = AudioSegment.from_file(temp_output_path)

        # Step 3: Balanced Filtering - Apply both low-pass and high-pass filters
        filtered_audio = processed_audio.low_pass_filter(5000)  # Keep frequencies below 5000 Hz
        filtered_audio = filtered_audio.high_pass_filter(100)    # Keep frequencies above 100 Hz

        # Final output path (overwrite original file)
        filtered_audio.export(audio_path, format="wav")
        print(f"Processed audio saved to the same path: {audio_path}")
        
        # Remove the temporary file
        os.remove(temp_output_path)
    
    except Exception as e:
        print(f"An error occurred: {e}")

def list_microphones():
    microphones = []
    devices = sd.query_devices()

    for idx, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            # Append the name and its corresponding index as a tuple
            microphones.append((device['name'], idx))
    
    return microphones

def list_output_devices():
    output_devices = []
    devices = sd.query_devices()

    for idx, device in enumerate(devices):
        if device['max_output_channels'] > 0:
            # Append the name and its corresponding index as a tuple
            output_devices.append((device['name'], idx))
    
    return output_devices

def record_audio(output_file, mic_index, sample_rate=48000, chunk_size=1024, max_record_seconds=300, silence_threshold=500, silence_duration=5):
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,  # 16-bit format
                    channels=2,  # 2 channels (stereo)
                    rate=sample_rate,  # 48000 Hz sample rate
                    input=True,
                    input_device_index=mic_index,
                    frames_per_buffer=chunk_size)

    print("* recording")
    frames = []
    silent_chunks = 0
    max_silent_chunks = int(sample_rate / chunk_size * silence_duration)  # Max silent chunks for 5 seconds of silence

    start_time = time.time()

    # Keep recording until max_record_seconds is reached, but stop earlier if 5 seconds of silence is detected
    while True:
        data = stream.read(chunk_size, exception_on_overflow=False)
        frames.append(data)
        
        # Convert the byte data to numpy array to calculate RMS
        audio_data = np.frombuffer(data, dtype=np.int16)
        rms = np.sqrt(np.mean(audio_data**2))

        # Print recording indicator on the same line
        print(f"\r* recording... RMS: {rms:.2f}", end='', flush=True)

        # Check for silence (RMS lower than threshold)
        if rms < silence_threshold:
            silent_chunks += 1
        else:
            silent_chunks = 0  # Reset silent counter if sound is detected
        
        # If there are 5 seconds of continuous silence, stop recording
        if silent_chunks >= max_silent_chunks:
            print("\n* 5 seconds of silence detected. Stopping recording.")
            break

        # Stop after reaching max_record_seconds regardless of silence
        elapsed_time = time.time() - start_time
        if elapsed_time >= max_record_seconds:
            print("\n* Maximum recording time reached. Stopping recording.")
            break

    total_elapsed_time = time.time() - start_time
    print(f"\n* Done recording. Total time: {total_elapsed_time:.2f} seconds.")

    stream.stop_stream()
    stream.close()
    p.terminate()

    # Save the recorded audio to a .wav file
    wf = wave.open(output_file, 'wb')
    wf.setnchannels(2)  # Save the recording as 2-channel audio
    wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))  # 16-bit audio
    wf.setframerate(sample_rate)  # 48000 Hz sample rate
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
                log_debug(f"Загрузка модели: {model_name}")
                # Load model to trigger download
                MarianMTModel.from_pretrained(model_name)
                log_debug(f"Модель {model_name} успешно загружена.")
            else:
                log_debug(f"Модель {model_name} уже существует.")


def translate(text, target_lang):
    try:
        # Step 1: Detect the source language
        src_lang = detect(text)

        # Step 2: If the detected language is the same as the target language, return the original text
        if src_lang == target_lang:
            log_debug(f"Исходный язык '{src_lang}' совпадает с целевым языком. Перевод не требуется.")
            return text

        # Step 3: Check if the detected language is supported in the LANGUAGE_MODEL_MAP
        if src_lang not in LANGUAGE_MODEL_MAP or target_lang not in LANGUAGE_MODEL_MAP.get(src_lang, {}):
            log_debug(f"Языковая пара '{src_lang}' на '{target_lang}' не поддерживается. Предполагается, что входной язык - английский.")
            src_lang = 'en'  # Default to English as the source language

        # Step 4: Check if there's a model for translation from English to the target language
        if target_lang not in LANGUAGE_MODEL_MAP.get(src_lang, {}):
            log_debug(f"Невозможно найти модель перевода с '{src_lang}' на '{target_lang}'. Возвращаем исходный текст.")
            return text

        # Step 5: Load the model and tokenizer for the detected language pair (or English to target language)
        model_name = LANGUAGE_MODEL_MAP[src_lang][target_lang]
        tokenizer = MarianTokenizer.from_pretrained(model_name)
        model = MarianMTModel.from_pretrained(model_name)

        # Step 6: Tokenize the input text
        inputs = tokenizer(text, return_tensors="pt", padding=True)

        # Step 7: Perform the translation
        translated = model.generate(**inputs)

        # Step 8: Decode the translated text
        translated_text = tokenizer.batch_decode(translated, skip_special_tokens=True, clean_up_tokenization_spaces=True)

        return translated_text[0]

    except Exception as e:
        log_debug(f"Ошибка: {e}")
        return text


def check_wav_properties(file_path):
    audio = AudioSegment.from_file(file_path)
    log_debug(f"Каналы: {audio.channels}")
    log_debug(f"Ширина сэмплов: {audio.sample_width}")
    log_debug(f"Частота кадров (частота дискретизации): {audio.frame_rate}")
    log_debug(f"Ширина кадров: {audio.frame_width}")
    log_debug(f"Длина (мс): {len(audio)}")

def play(file_path, output_device_index=None):
    # Load audio file
    data, samplerate = sf.read(file_path)
    
    # Set output device if specified
    if output_device_index is not None:
        sd.default.device = output_device_index
    
    # Play the audio
    sd.play(data, samplerate)
    
    # Wait until the file has finished playing
    sd.wait()
    
    log_debug(f"Воспроизведение аудио завершено для {file_path}")

        
if __name__ == "__main__":
    normalize('../Assets/Audio/hana.wav')
