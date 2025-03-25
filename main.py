
import serial
from tts import text_to_speech
from stt import record_and_recognize  # Import our new convenience function
from camera import init_camera, capture_image, release_camera
from image_analysis import analyze_image
import os
import time
from medication_db import (
    init_db,
    add_schedule,
    update_schedule,
    delete_schedule,
    get_all_schedules,
    add_status,
    update_status,
    get_all_statuses
)


#구글 인증 파일 읽기
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "credentials.json"

#stm32로부터 시리얼 신호 받을 객체
ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)


def standby():
    while(true):
        #메인 기능 시작: USB로 신호 기다리기        
        if ser.in_waiting > 0:
            event = ser.read(1)  # Read one byte from UART

            #스탠바이시 변화를 감지하는 변수 standby_change
            standby_change = react_to_event(event)

            if standby_change == '1':
                #1번 소켓 눌림 실행
                press_button('1')
            elif standby_change == '2':
                #2번 소켓 눌림 실행
                press_button('2')
            elif standby_change == '3':
                #3번 소켓 눌림 실행
                press_button('3')

            elif standby_change == 'O':
                #원터치 버튼 눌린 경우 메인 기능 실행
                main_function1()

            elif standby_change == 'Q':
                #물음표 버튼 눌린 경우 스탠바이 시 물음표 기능 실행
                main_function2()

            elif standby_change == 'A':
                #1번 소켓 센서 변화된 경우 약 섭취로 취급
                take_medicine('A')
            elif standby_change == 'B':
                #2번 소켓 센서 변화된 경우 약 섭취로 취급
                take_medicine('B')
            elif standby_change == 'C':
                #3번 소켓 센서 변화된 경우 약 섭취로 취급
                take_medicine('C')


#버튼/센서 상태변화 값 STM32에서 받아온 후 값에따라 처리
def react_to_event(event):
    if event == b'1':
        print("1번 소켓 버튼 눌림")
        return '1'
    elif event == b'2':
        print("1번 소켓 버튼 눌림")
        return '2'
    elif event == b'3':
        print("1번 소켓 버튼 눌림")
        return '3'
    elif event == b'O':
        print("원터치 버튼 눌림")
        return 'O'
    elif event == b'Q':
        print("물음표 버튼 눌림")
        return 'Q'
    elif event == b'A':
        print("1번소켓 센서 변화")
        return 'A'
    elif event == b'B':
        print("2번소켓 센서 변화")
        return 'B'
    elif event == b'C':
        print("3번소켓 센서 변화")
        return 'C'
    else:
        print("이상신호 감지")
        return 'E'


#기본기능1 (스탠바이에서 원터치 눌렀을 경우)
def main_function1():
    text = "무엇을 도와드릴까요? 메뉴 설명을 들으시려면 물음표 버튼을 눌러주세요"
    text_to_speech(text, "output.mp3")
    
    # 7초동안 음성 인식하기
    recognized_text = record_and_recognize(duration=7, filename="recorded_audio.wav")
    
    #만일 음성이 인식되었다면
    if recognized_text:
        print(f"Recognized Speech: {recognized_text}")
        
        if recognized_text == "약추가":
            add_medicine()
        
        elif recognized_text == "약삭제":
            delete_medicine()
        
        elif recognized_text == "물건추가":
            add_thing()

        elif recognized_text == "물건삭제":
            delete_thing()

        elif recognized_text == "물건묘사":
            describe_thing()

    #만일 음성이 인식되지 않았다면
    else:
        print("No speech recognized.")

    return

#기본기능2 (스탠바이에서 물음표 눌렀을 경우)
def main_function2():
    text = "메뉴는 다음과 같습니다. 약추가. 약삭제. 물품추가. 물품삭제. 물품묘사"
    text_to_speech(text, "output.mp3")
        
    #메뉴 설명후 기본기능1로 귀환
    main_function1()    

    return


#약 추가
def add_medicine():
    print("약추가 실행")

    return

#약 삭제
def delete_medicine():
    print("약삭제 실행")

    return

#약 복용하는 경우
def take_medicine(socket):
    print("약복용 실행")

    return


#물건 추가
def add_thing():
    print("물건추가 실행")


    return

#물건 삭제
def delete_thing():
    print("물건삭제 실행")

    return



#물건 묘사
def describe_thing():
    print("물건묘사 실행")

    return


#소켓버튼 눌린경우 처리
def press_button(socket):
    print("소켓내용 설명 실행")

    return



def main():

    #DB 생성또는 불러오기
    init_db()
    print("Medication database initialized.\n")

    # 웹캠 Init
    cap = init_camera()
    print("Webcam initialized and ready.")

    #스탠바이 상태로 대기
    standby()
    

    # 아래는 모든 기능 테스트용 코드
    # while True:
    #     print("\nSelect an option:")
    #     print("1: Speech-to-Text (record voice for 5 sec)")
    #     print("2: Text-to-Speech (TTS)")
    #     print("3: Image Analysis (capture & analyze image)")
    #     print("q: Quit")
    #     choice = input("Enter your choice: ").strip().lower()

    #     if choice == "1":
    #         # Record and recognize speech in one step
    #         recognized_text = record_and_recognize(duration=5, filename="recorded_audio.wav")
    #         if recognized_text:
    #             print(f"Recognized Speech: {recognized_text}")
    #         else:
    #             print("No speech recognized.")

    #     elif choice == "2":
    #         text = input("Enter text to synthesize: ").strip()
    #         text_to_speech(text, "output.mp3")
    #         print("Text has been converted to speech and saved as output.mp3")

    #     elif choice == "3":
    #         print("Capturing image from webcam...")
    #         image_path = capture_image(cap)
    #         if image_path:
    #             print("Analyzing captured image...")
    #             result = analyze_image(image_path)
    #             labels = result.get("labels", [])
    #             detected_text = result.get("text")
    #             description = "This image appears to show "
    #             if labels:
    #                 if len(labels) == 1:
    #                     description += labels[0]
    #                 else:
    #                     description += ", ".join(labels[:-1]) + ", and " + labels[-1]
    #             else:
    #                 description += "an unspecified scene"
    #             if detected_text:
    #                 description += f". It also contains the text: '{detected_text.strip()}'"
    #             description += "."
    #             print("\nImage Description:")
    #             print(description)
    #         else:
    #             print("No image captured.")

    #     elif choice == "q":
    #         print("Exiting application.")
    #         break

    #     else:
    #         print("Invalid option, please try again.")

    # # Release the webcam resources when the program ends


    





    #웹캠 해제
    release_camera(cap)

if __name__ == "__main__":
    main()
