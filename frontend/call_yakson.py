import os  # 운영체제와 상호작용하기 위한 모듈 임포트
import speech_recognition as sr  # 음성 인식을 위한 speech_recognition 모듈 임포트
from google.cloud import texttospeech  # Google Cloud TTS 모듈 임포트

# Google Cloud API 인증 정보(JSON 파일 경로)를 환경변수에 설정
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "stt-key.json"  # API 인증키 파일 경로 설정

def text_to_speech(text, filename="output.mp3"):
    """입력된 텍스트를 음성으로 합성하고 파일에 저장하는 함수"""
    client = texttospeech.TextToSpeechClient()  # TTS 클라이언트 객체 생성

    # 한국어, 여성 음성 설정
    voice = texttospeech.VoiceSelectionParams(
        language_code="ko-KR",  # 언어를 한국어로 설정
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,  # 여성 음성 선택
        name="ko-KR-Wavenet-A",  # Wavenet 여성 목소리 선택
    )

    # 오디오 출력 형식을 MP3로 설정
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3  # MP3 인코딩 설정
    )

    # 입력 텍스트를 음성 합성용으로 변환
    synthesis_input = texttospeech.SynthesisInput(text=text)  # 텍스트 입력을 SynthesisInput 객체로 생성

    # TTS 요청을 보내어 음성 합성 수행
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config  # 합성 요청 인자 전달
    )

    # 합성된 음성 데이터를 파일에 저장
    with open(filename, "wb") as out:  # 바이너리 쓰기 모드로 파일 열기
        out.write(response.audio_content)  # 응답받은 오디오 콘텐츠를 파일에 기록
    print(f"Speech saved as {filename}")  # 파일 저장 완료 메시지 출력

def speech_to_text():
    """마이크로 입력받은 음성을 텍스트로 변환하는 함수"""
    recognizer = sr.Recognizer()  # 음성 인식 객체 생성
    with sr.Microphone() as source:  # 마이크로폰을 음성 입력 소스로 사용
        print("말씀하세요...")  # 사용자에게 입력 안내 메시지 출력
        audio = recognizer.listen(source)  # 마이크로부터 음성 데이터 수집
    try:
        # Google Cloud STT API를 이용하여 음성 데이터를 텍스트로 변환 (한국어 설정)
        text = recognizer.recognize_google_cloud(audio, language_code="ko-KR")  # 음성 데이터를 한국어로 인식
        print("인식된 텍스트:", text)  # 인식된 텍스트 출력
        return text.strip()  # 변환된 텍스트 반환 (공백 제거)
    except sr.UnknownValueError:
        print("음성을 인식하지 못했습니다.")  # 음성을 인식하지 못한 경우
        return None
    except sr.RequestError as e:
        print("STT 요청 실패:", e)  # STT 요청 실패 시
        return None

def play_audio(filename):
    """생성된 음성 파일을 재생하는 함수"""
    from playsound import playsound  # 간단한 오디오 재생을 위한 playsound 모듈 임포트
    playsound(filename)  # 지정된 파일 재생

if __name__ == "__main__":
    # 메인 실행부: 마이크 입력 -> STT -> 조건에 따른 TTS -> 재생 순서로 진행
    recognized_text = speech_to_text()  # 음성 입력 받아 텍스트로 변환
    if recognized_text:  # 변환된 텍스트가 존재하면
        match recognized_text:  # match-case 문을 사용하여 조건 처리
            case "이 약은 뭐야":
                response_text = "네 고객님 이 약은 우르사입니다"
            case "이 약이 뭐야":
                response_text = "네 고객님 이 약은 우르사입니다"    
            case "이야기 뭐야":
                response_text = "네 고객님 이 약은 우르사입니다"    
            case "약소 날":
                response_text = "네 고객님 말씀하세요"
            case "약손아":
                response_text = "네 고객님 말씀하세요"
            case "약손 아":
                response_text = "네 고객님 말씀하세요"    
            case _:
                response_text = recognized_text  # 기본 응답

        text_to_speech(response_text, "output.mp3")  # 응답 텍스트를 음성으로 합성하여 파일 저장
        play_audio("output.mp3")  # 생성된 음성 파일을 재생
