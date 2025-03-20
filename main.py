from tts import text_to_speech
from stt import speech_to_text
from camera import init_camera, capture_image, release_camera
from image_analysis import analyze_image
import sounddevice as sd
import soundfile as sf
import os
import time

# Set the credentials for Google Cloud APIs
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"C:\googleCloudCredentials\credentials.json"

def record_audio(duration=5, filename="recorded_audio.wav", samplerate=16000):
    """Records audio from the microphone for a given duration and saves it as a WAV file."""
    print(f"Recording audio from mic for {duration} seconds...")
    audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
    sd.wait()  # Wait until recording is finished
    sf.write(filename, audio, samplerate)
    print(f"Recording complete. Saved as {filename}")
    return filename

def main():
    # Initialize the webcam once when the program starts
    cap = init_camera()
    print("Webcam initialized and ready.")

    while True:
        print("\nSelect an option:")
        print("1: Speech-to-Text (record voice for 5 sec)")
        print("2: Text-to-Speech (TTS)")
        print("3: Image Analysis (capture & analyze image)")
        print("q: Quit")
        choice = input("Enter your choice: ").strip().lower()

        if choice == "1":
            # Record audio from the mic for 5 seconds
            audio_file = record_audio(duration=5, filename="recorded_audio.wav")
            time.sleep(2)
            # Use the recorded audio file for STT
            recognized_text = speech_to_text(audio_file)
            if recognized_text:
                print(f"Recognized Speech: {recognized_text}")
            else:
                print("No speech recognized.")

        elif choice == "2":
            text = input("Enter text to synthesize: ").strip()
            text_to_speech(text, "output.mp3")
            print("Text has been converted to speech and saved as output.mp3")

        elif choice == "3":
            print("Capturing image from webcam...")
            # Use the already initialized camera to capture an image
            image_path = capture_image(cap)
            if image_path:
                print("Analyzing captured image...")
                result = analyze_image(image_path)
                # Create a natural, human-like description
                labels = result.get("labels", [])
                detected_text = result.get("text")
                description = "This image appears to show "
                if labels:
                    if len(labels) == 1:
                        description += labels[0]
                    else:
                        description += ", ".join(labels[:-1]) + ", and " + labels[-1]
                else:
                    description += "an unspecified scene"
                if detected_text:
                    description += f". It also contains the text: '{detected_text.strip()}'"
                description += "."
                print("\nImage Description:")
                print(description)
            else:
                print("No image captured.")

        elif choice == "q":
            print("Exiting application.")
            break

        else:
            print("Invalid option, please try again.")

    # Release the webcam resources when the program ends
    release_camera(cap)

if __name__ == "__main__":
    main()
