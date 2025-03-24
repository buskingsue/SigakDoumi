import os
import numpy as np
import scipy.signal as signal
import speech_recognition as sr
from google.cloud import texttospeech
from pydub import AudioSegment
import pyaudio

# Google Cloud API 인증 정보 설정
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "stt-key.json"

# 주파수 필터 설정
LOW_CUTOFF = 500   # 필터의 하한 주파수 (500Hz)
HIGH_CUTOFF = 1500 # 필터의 상한 주파수 (1500Hz)
SAMPLE_RATE = 16000  # 샘플링 레이트 (16kHz)

# 음성 합성(TTS) 함수
def text_to_speech(text, filename="response.mp3"):
    client = texttospeech.TextToSpeechClient()
    voice = texttospeech.VoiceSelectionParams(
        language_code="ko-KR",
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
        name="ko-KR-Wavenet-A"
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,  # 기본적으로 MP3 형식
        sample_rate_hertz=44100  # 샘플링 레이트를 44.1kHz로 설정
    )
    synthesis_input = texttospeech.SynthesisInput(text=text)
    response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
    
    # 응답 음성을 MP3 파일로 저장
    with open(filename, "wb") as out:
        out.write(response.audio_content)
    print("응답 음성이 저장되었습니다:", filename)

    # 저장된 MP3 파일을 44.1kHz, 16비트, 스테레오로 변환
    audio = AudioSegment.from_mp3(filename)
    audio = audio.set_channels(2)  # 스테레오로 변환
    audio = audio.set_sample_width(2)  # 16비트로 설정 (2바이트)
    audio = audio.set_frame_rate(44100)  # 44.1kHz 샘플링 레이트로 변경

    # 변환된 오디오 저장
    audio.export(filename, format="mp3")
    print(f"변환된 응답 음성 저장 완료: {filename}")

# 오디오 필터 적용 (특정 주파수 대역 통과)
def bandpass_filter(audio_data, rate, lowcut, highcut):
    nyquist = 0.5 * rate
    low = lowcut / nyquist
    high = highcut / nyquist
    b, a = signal.butter(4, [low, high], btype="band")
    return signal.lfilter(b, a, audio_data)

# 음성 인식 함수
def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone(sample_rate=SAMPLE_RATE) as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)  # 노이즈 조정
        print("대기 중... (웨이크 워드 감지)")
        audio = recognizer.listen(source)

    # 오디오 데이터 필터 적용
    audio_data = np.frombuffer(audio.frame_data, dtype=np.int16)
    filtered_audio = bandpass_filter(audio_data, SAMPLE_RATE, LOW_CUTOFF, HIGH_CUTOFF)

    try:
        text = recognizer.recognize_google(audio, language="ko-KR")  # STT 수행
        print("인식된 텍스트:", text)
        return text
    except sr.UnknownValueError:
        print("음성을 인식하지 못했습니다.")
        return None
    except sr.RequestError as e:
        print("STT 요청 실패:", e)
        return None

# 웨이크 워드 감지 및 실행
def wake_word_detection():
    while True:
        text = recognize_speech()
        if text and ("약손아" in text or "약 손아" in text or "약 소나" in text or "약손" in text):
            print("웨이크 워드 감지! 시스템 활성화...")
            response_text = "네, 무엇을 도와드릴까요?"
            text_to_speech(response_text, "response.mp3")
            os.system("mpg321 response.mp3")  # 음성 파일 재생 (리눅스/macOS)
            text = recognize_speech()
            if text and ("약추가" in text or "약 추가" in text):
                print("약추가 워드 감지! 시스템 활성화...")
                response_text = "약정보를 추가합니다."
                text_to_speech(response_text, "response1.mp3")
                os.system("mpg321 response1.mp3")  # 음성 파일 재생 (리눅스/macOS)
                break
            
            if text and ("약 삭제" in text or "약삭제" in text):
                print("약삭제 워드 감지! 시스템 활성화...")
                response_text = "약정보를 삭제합니다."
                text_to_speech(response_text, "response1.mp3")
                os.system("mpg321 response1.mp3")  # 음성 파일 재생 (리눅스/macOS)
                break

# 실행
if __name__ == "__main__":
    wake_word_detection()
