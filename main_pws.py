# main.py

import serial
from tts import text_to_speech
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
#===================================추가부분============================================        
def delete_medicine_standby(a): ## a번 약을 제거하려고함함
    ser = get_serial()
    while(True): # True가 어떤 역할인지? 신호를 받았을때 인지?
        if ser.in_waiting > 0: # 대기 시간?
            event = ser.read(1) #시리얼로 신호를 받을때
            standby_change = react_to_event(event)

        if standby_change == '0':
            text_to_speech("약을 제거합니다", "output.mp3")
            #delete_schedule(str(a).encode()) # 엔코드가 b<-이거 붙여줌
            #약 스케줄 삭제 변수가 stm32 통신으로 받을 변수랑 똑같을 경우

            delete_schedule(a) # 이거 데이터베이스 번호랑 맞춰줘야함

            #딜레이 고민중
            text_to_speech("처음으로 돌아갑니다", "output.mp3")
            #딜레이 고민중
            standby() # 처음으로 돌아가는 함수
            
        if standby_change == 'Q':
            text_to_speech("취소", "output.mp3")
            #딜레이 고민중
            standby() # 처음으로 돌아가는함수
#===================================추가부분============================================     
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
    text_to_speech(text, "output.mp3")
    recognized_text = record_and_recognize(duration=7, filename="recorded_audio.wav")

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
#===================================추가부분============================================     
def delete_medicine():
    print("약삭제 실행")
    text = "몇번 소켓의 약을 삭제 하시겠습니까?"
    text_to_speech(text, "output.mp3")
    if react_to_event(b'0'): 
        standby()
    #delete_medicine_standby() 스탠바이를 어떤 형식으로 써야하는지
    #번호를 누르면 그거에따라 번호누르는 신호가 와야함
    recognized_text = record_and_recognize(duration=7, filename="recorded_audio.wav")
    
    if recognized_text:
        print(f"Recognized Speech: {recognized_text}")
    if recognized_text == "일번":
        text_to_speech("1번", "output.mp3")
        delete_number = 1
    elif recognized_text == "이번":
        text_to_speech("2번", "output.mp3")
        delete_number = 2
    elif recognized_text == "삼삼번":
        text_to_speech("3번", "output.mp3")
        delete_number = 3

    # 여기에 딜레이를 넣어야할지 고민중
    text = "약을 제거해 주신 후 원터치 버튼을 눌러주세요, 취소하시려면 물음표버튼을 눌러주세요"
    text_to_speech(text, "output.mp3")
    delete_medicine_standby(delete_number) #이 함수에 딜리트 넘버를 넣음

#===================================추가부분============================================     

def take_medicine(socket):
    print("약복용 실행")
    return

def add_thing():
    print("물건추가 실행")
    return

def delete_thing():
    print("물건삭제 실행")
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

