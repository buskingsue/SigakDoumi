import os
import numpy as np
from scipy import signal
from google.cloud import texttospeech
from pydub import AudioSegment
from pydub.playback import play

# Set the credentials for Google Cloud APIs
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "credentials.json"

# Filtering constants
LOW_CUTOFF = 500    # 필터의 하한 주파수 (500Hz)
HIGH_CUTOFF = 1500  # 필터의 상한 주파수 (1500Hz)
SAMPLE_RATE = 16000  # 필터 적용시 사용할 샘플링 레이트 (16kHz)

def bandpass_filter(audio_data, rate, lowcut, highcut):
    """Applies a Butterworth bandpass filter to the audio data."""
    nyquist = 0.5 * rate
    low = lowcut / nyquist
    high = highcut / nyquist
    b, a = signal.butter(4, [low, high], btype="band")
    return signal.lfilter(b, a, audio_data)

def text_to_speech(text, filename="output.mp3"):
    # Initialize the Text-to-Speech client
    client = texttospeech.TextToSpeechClient()

    # Configure the voice parameters (Korean, female, Wavenet)
    voice = texttospeech.VoiceSelectionParams(
        language_code="ko-KR",
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
        name="ko-KR-Wavenet-A"
    )

    # Set up the audio configuration (MP3 format)
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    # Prepare the synthesis input
    synthesis_input = texttospeech.SynthesisInput(text=text)

    # Synthesize speech
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    # Save the synthesized speech to an MP3 file
    with open(filename, "wb") as out:
        out.write(response.audio_content)
    print(f"Speech saved as {filename}")

    # Load the generated MP3 file using pydub
    audio = AudioSegment.from_mp3(filename)

    # Convert the audio to 44.1 kHz, 16-bit, stereo
    audio = audio.set_channels(2)      # 스테레오로 변환
    audio = audio.set_sample_width(2)    # 16비트 (2바이트)
    audio = audio.set_frame_rate(44100)  # 44.1kHz 샘플링 레이트

    # Export the converted audio (overwrite the original file)
    audio.export(filename, format="mp3")
    print(f"Converted audio saved as {filename}")

    # --- Audio Filtering ---
    # To apply the bandpass filter, we'll first resample the audio to 16kHz.
    audio_for_filter = audio.set_frame_rate(SAMPLE_RATE)
    # Get raw audio data as a NumPy array
    raw_data = np.frombuffer(audio_for_filter.raw_data, dtype=np.int16)
    # Apply the bandpass filter
    filtered_data = bandpass_filter(raw_data, SAMPLE_RATE, LOW_CUTOFF, HIGH_CUTOFF)
    # Convert filtered data back to bytes
    filtered_bytes = filtered_data.astype(np.int16).tobytes()
    # Create a new AudioSegment from the filtered data
    filtered_segment = AudioSegment(
        data=filtered_bytes,
        sample_width=audio_for_filter.sample_width,
        frame_rate=SAMPLE_RATE,
        channels=audio_for_filter.channels
    )
    # Resample filtered audio back to 44.1kHz for playback consistency
    filtered_segment = filtered_segment.set_frame_rate(44100)

    # Export the filtered audio to a new file (or overwrite)
    filtered_filename = "filtered_" + filename
    filtered_segment.export(filtered_filename, format="mp3")
    print(f"Filtered audio saved as {filtered_filename}")

    # Playback the filtered audio
    print("Playing filtered audio...")
    play(filtered_segment)

if __name__ == "__main__":
    text = "원석님 머하시나요"
    text_to_speech(text, "output.mp3")
