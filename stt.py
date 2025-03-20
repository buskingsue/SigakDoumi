from google.cloud import speech


def speech_to_text(audio_path):
    """Converts speech in an audio file to text using Google Cloud Speech-to-Text API"""

    client = speech.SpeechClient()

    # Read the audio file
    with open(audio_path, "rb") as audio_file:
        content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,  # Adjust based on your audio file format
        sample_rate_hertz=16000,
        language_code="en-US"
    )

    # Request recognition
    response = client.recognize(config=config, audio=audio)

    # Extract and print results
    for result in response.results:
        print("Transcript: {}".format(result.alternatives[0].transcript))
        return result.alternatives[0].transcript

    return None


if __name__ == "__main__":
    speech_to_text("sample_audio.wav")  # Provide a sample audio file
