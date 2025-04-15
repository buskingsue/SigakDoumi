import struct
import os
import time
import pyaudio
import pvporcupine
from frontend.speak import text_to_speech  # Your project’s TTS function

class WakeWordDetector:
    def __init__(self, callback, access_key, keyword_paths, model_path):
        """
        :param callback: Function to call when a wake word is detected.
        :param access_key: Your Picovoice AccessKey.
        :param keyword_paths: List (or a single path) to custom keyword file(s) (.ppn).
        :param model_path: Path to the Porcupine model file (.pv) for your platform.
        """
        self.callback = callback
        self.access_key = access_key

        # Ensure keyword_paths is a list.
        if isinstance(keyword_paths, str):
            self.keyword_paths = [keyword_paths]
        else:
            self.keyword_paths = keyword_paths

        self.model_path = model_path

        # Create the Porcupine instance using the provided custom keyword files.
        self.porcupine = pvporcupine.create(
            access_key=self.access_key,
            keyword_paths=self.keyword_paths,
            model_path=self.model_path
        )

        self.sample_rate = self.porcupine.sample_rate
        self.frame_length = self.porcupine.frame_length

        # Initialize PyAudio stream.
        self.pa = pyaudio.PyAudio()
        self.audio_stream = self.pa.open(
            rate=self.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=self.frame_length
        )
        print("Listening continuously for wake words...")

    def run(self):
        try:
            while True:
                # Read a single frame of audio (returns a byte string).
                pcm = self.audio_stream.read(self.frame_length, exception_on_overflow=False)
                # Unpack the byte string into a tuple of 16-bit integers.
                pcm_unpacked = struct.unpack_from("h" * self.frame_length, pcm)
                # Process the audio frame.
                keyword_index = self.porcupine.process(pcm_unpacked)
                if keyword_index >= 0:
                    # A wake word was detected.
                    print("Wake word detected! Activating chat...")
                    response_text = "네 주인님, 무엇을 도와드릴까요?"
                    text_to_speech(response_text, "response.mp3")
                    if self.callback:
                        self.callback()
                # Small sleep to ease CPU usage.
                time.sleep(0.01)
        except KeyboardInterrupt:
            self.delete()

    def delete(self):
        # Clean up resources.
        self.audio_stream.stop_stream()
        self.audio_stream.close()
        self.pa.terminate()
        self.porcupine.delete()
