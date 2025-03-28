# main.py

import serial
from speak import text_to_speech
from stt import record_and_recognize
from camera import init_camera, capture_image, release_camera
from ocr import send_image_for_ocr  # New import
import os
import time
from convert_to_medicine_schedule import MedicineScheduleConverter
from medication_db import (
    init_db,
    add_schedule,
    update_schedule,
    delete_schedule,
    get_all_schedules,
    add_status,
    update_status,
    get_all_statuses,
    add_socket_content,
    delete_socket_content,
    get_socket_content
)

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "credentials.json"

def get_serial():
    return serial.Serial('/dev/ttyUSB0', 9600, timeout=1)

def standby():
    ser = get_serial()
    while(True):
        if ser.in_waiting > 0:
            event = ser.read(1)
            standby_change = react_to_event(event)

            if standby_change == '1':
                press_button('1')
            elif standby_change == '2':
                press_button('2')
            elif standby_change == '3':
                press_button('3')
            elif standby_change == 'O':
                main_function1()
            elif standby_change == 'Q':
                main_function2()
            elif standby_change == 'A':
                take_medicine('A')
            elif standby_change == 'B':
                take_medicine('B')
            elif standby_change == 'C':
                take_medicine('C')

def add_medicine_standby():
    ser = get_serial()
    while(True):
        if ser.in_waiting > 0:
            event = ser.read(1)
            standby_change = react_to_event(event)

            if standby_change == 'O':
                # 원터치 버튼 누르면 약 섭취 메모지 OCR 실행
                analyze_memo()

            elif standby_change == 'Q':
                standby()

# 물건 추가 대기 함수: 사용자의 버튼 입력을 감지하여 OCR 실행
def add_thing_standby():
    ser = get_serial()
    while True:
        if ser.in_waiting > 0:
            event = ser.read(1)
            standby_change = react_to_event(event)

            if standby_change == 'O':  # 원터치 버튼 눌림 → OCR 실행
                analyze_thing_memo()
            elif standby_change == 'Q':  # 물음표 버튼 눌림 → 대기 모드 복귀
                standby()
            else:
                print("잘못된 입력 감지")

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

def main_function1():
    text = "무엇을 도와드릴까요? 메뉴 설명을 들으시려면 물음표 버튼을 눌러주세요"
    print(f"text: {text}")
    text_to_speech(text, "output.mp3")
    
    recognized_text = record_and_recognize(duration=7, filename="recorded_audio.wav")

    if recognized_text:
        # Normalize by removing all spaces
        normalized_text = recognized_text.replace(" ", "")
        print(f"Recognized Speech: {normalized_text}")
        
        if normalized_text == "약추가":
            add_medicine()
        elif normalized_text == "약삭제":
            delete_medicine()
        elif normalized_text == "물건추가":
            add_thing()
        elif normalized_text == "물건삭제":
            delete_thing()
        elif normalized_text == "물건묘사":
            describe_thing()
    else:
        print("No speech recognized.")
    return

def main_function2():
    text = "메뉴는 다음과 같습니다. 약추가. 약삭제. 물품추가. 물품삭제. 물품묘사"
    text_to_speech(text, "output.mp3")
    main_function1()    
    return

# 약 추가 함수
def add_medicine():
    print("약추가 실행")
    text = "약 정보 메모지를 스테이지에 올려놓으신 후 원터치 버튼을 눌러주세요. " \
    "취소하시려면 물음표 버튼을 눌러주세요"
    text_to_speech(text, "output.mp3")

    add_medicine_standby()

    return

def delete_medicine():
    print("약삭제 실행")
    return

def take_medicine(socket):
    print("약복용 실행")
    
    return

 
# 물건 추가 실행 함수: 음성 안내 후 대기 모드로 전환
def add_thing():
    print("물건추가 실행")
    text = "물건 정보를 메모지에 적고, 스테이지에 올려놓은 후 원터치 버튼을 눌러주세요."
    text_to_speech(text, "add_thing_prompt.mp3")

    add_thing_standby()
    return

def ask_for_another_thing():
    """ 물건 추가 여부를 사용자에게 묻고 입력을 처리 """
    text_to_speech("물건을 추가하시겠습니까? 추가하시려면 원터치 버튼, 취소하시려면 물음표 버튼을 눌러주세요.", "ask_another.mp3")
    
    ser = get_serial()
    while True:
        if ser.in_waiting > 0:
            event = ser.read(1)
            standby_change = react_to_event(event)

            if standby_change == 'Q':  # 물음표 버튼 → standby() 호출
                text_to_speech("메뉴로 돌아갑니다.", "return_to_menu.mp3")
                standby()
            elif standby_change == 'O':  # 원터치 버튼 → 음성 인식 실행
                text_to_speech("물품명을 말씀해주세요.", "say_item_name.mp3")
                record_and_save_thing()
            else:
                print("잘못된 입력 감지")

def record_and_save_thing():
#사용자의 음성을 인식하여 물품명을 저장
    recognized_text = record_and_recognize(duration=5, filename="thing_name.wav")
    
    if recognized_text:
        text_to_speech(f"추가된 물품: {recognized_text}", "thing_added.mp3")
        add_socket_content(recognized_text)  # 데이터베이스에 저장
        text_to_speech("물건 정보가 저장되었습니다.", "save_success.mp3")
    else:
        text_to_speech("음성을 인식하지 못했습니다.", "speech_fail.mp3")

    # 다시 물건 추가 여부 질문 반복
    ask_for_another_thing()


def delete_thing():
    print("물건삭제 실행")
    text = "물건 정보를 삭제합니다. 몇번 소켓의 물건을 삭제 할 것인가요"
    text_to_speech(text, "del_thing_prompt.mp3")

    del_thing_standby()
    return

def describe_thing():
    print("물건묘사 실행")
    return

def press_button(socket):
    print("소켓내용 설명 실행")
    return

def analyze_memo():
    converter = MedicineScheduleConverter()
    converter.analyze_memo()

def main():
    init_db()
    print("Medication database initialized.\n")
    cap = init_camera()
    print("Webcam initialized and ready.")
    # standby()
    main_function1()
    release_camera(cap)

if __name__ == "__main__":
    main()
