import os
from google.cloud import texttospeech
from pydub import AudioSegment
from pydub.playback import play

# Google Cloud 인증 설정
# 바꾸실것
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "stt-key.json"

def text_to_speech(text, filename="output.mp3"):
    """텍스트를 음성으로 변환하고 16비트 44.1kHz 스테레오 MP3로 저장"""
    client = texttospeech.TextToSpeechClient()

    # 음성 합성 요청
    response = client.synthesize_speech(
        input=texttospeech.SynthesisInput(text=text),
        voice=texttospeech.VoiceSelectionParams(language_code="ko-KR", name="ko-KR-Wavenet-A"),
        audio_config=texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
    )

    # 생성된 음성 저장
    with open(filename, "wb") as out:
        out.write(response.audio_content)

    # 오디오 변환: 44.1kHz, 16비트, 스테레오
    audio = AudioSegment.from_mp3(filename)
    audio = audio.set_frame_rate(44100).set_sample_width(2).set_channels(2)

    # 변환된 오디오 저장
    final_filename = "final_" + filename
    audio.export(final_filename, format="mp3")
    print(f"Converted audio saved as {final_filename}")

    # 변환된 오디오 재생
    play(audio)

if __name__ == "__main__":
    text_to_speech("원석님 머하시나요")
