from google.cloud import texttospeech


def text_to_speech(text, output_filename="output.mp3"):
    """Converts text to speech and saves as an audio file using Google Cloud Text-to-Speech API"""

    client = texttospeech.TextToSpeechClient()

    # Set up text input and voice selection
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )

    # Set up audio configuration
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    # Generate speech
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    # Save output file
    with open(output_filename, "wb") as out:
        out.write(response.audio_content)
        print(f"Audio file saved as {output_filename}")


if __name__ == "__main__":
    text_to_speech("Hello! This is a test for Google Cloud TTS.", "output.mp3")
