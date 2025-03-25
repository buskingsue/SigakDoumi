import os
import numpy as np
import sounddevice as sd
import soundfile as sf
from google.cloud import speech

# 구글 인증키 정보
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "credentials.json"

# 마이크 장비 선택하기
sd.default.device = 2

# Define a sample rate (16kHz is typical for speech recognition)
SAMPLE_RATE = 16000

def record_audio(duration=5, filename="recorded_audio.wav", samplerate=SAMPLE_RATE):
    """
    Records audio from the microphone for a given duration and saves it as a WAV file.
    """
    print(f"Recording audio from mic for {duration} seconds...")
    audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
    sd.wait()  # Wait until recording is finished
    sf.write(filename, audio, samplerate)
    print(f"Recording complete. Saved as {filename}")
    return filename

def speech_to_text(audio_path):
    """
    Converts speech in an audio file to text using Google Cloud Speech-to-Text API.
    """
    client = speech.SpeechClient()

    # Read the audio file
    with open(audio_path, "rb") as audio_file:
        content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,  # Adjust based on your audio file format
        sample_rate_hertz=SAMPLE_RATE,
        language_code="ko-KR"  # Recognize Korean speech
    )

    # 음성인식 요청
    response = client.recognize(config=config, audio=audio)

    # 결과 출력
    for result in response.results:
        transcript = result.alternatives[0].transcript
        print("Transcript: {}".format(transcript))
        return transcript

    return None

def record_and_recognize(duration=5, filename="recorded_audio.wav"):
    """
    Convenience function that records audio from the microphone and performs STT.
    """
    audio_file = record_audio(duration=duration, filename=filename)
    # Optional: Wait a bit before recognition if needed
    return speech_to_text(audio_file)

if __name__ == "__main__":
    # For standalone testing, record audio for 5 seconds and then perform STT.
    record_and_recognize()
