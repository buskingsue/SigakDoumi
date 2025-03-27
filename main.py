# main.py

import serial
from speak import text_to_speech
from stt import record_and_recognize
from camera import init_camera, capture_image, release_camera
from ocr import send_image_for_ocr  # New import
import os
import time
# from image_analysis import analyze_thing
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

# 카메라 인스턴스 전역으로 선언
cap = None

# def get_serial():
#     return serial.Serial('/dev/ttyUSB0', 9600, timeout=1)

# Dummy get_serial to simulate UART signals via keyboard input.
def get_serial():
    class DummySerial:
        @property
        def in_waiting(self):
            # Always return 1, indicating there is user input waiting.
            return 1

        def read(self, size):
            # Prompt the user to enter a simulated UART signal.
            user_input = input("Simulated UART input (enter one character): ")
            if user_input:
                # Return the first character as bytes.
                return user_input[0].encode()
            else:
                return b''
    return DummySerial()


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
    while True:
        if ser.in_waiting > 0:
            event = ser.read(1)
            standby_change = react_to_event(event)
            if standby_change == 'O':
                analyze_memo()
            elif standby_change == 'Q':
                standby()

def delete_medicine_standby(socket_num): ## a번 약을 제거하려고함함
    ser = get_serial()
    while(True): # True가 어떤 역할인지? 신호를 받았을때 인지?
        if ser.in_waiting > 0: # 대기 시간?
            event = ser.read(1) #시리얼로 신호를 받을때
            standby_change = react_to_event(event)

        if standby_change == 'O':
            text_to_speech("약을 스케쥴에서 제거 합니다", "output.mp3")
            #delete_schedule(str(a).encode()) # 엔코드가 b<-이거 붙여줌
            #약 스케줄 삭제 변수가 stm32 통신으로 받을 변수랑 똑같을 경우

            delete_schedule(socket_num) # 이거 데이터베이스 번호랑 맞춰줘야함

            #딜레이 고민중
            # text_to_speech("처음으로 돌아갑니다", "output.mp3")

            #딜레이 고민중
            standby() # 처음으로 돌아가는 함수
            
        if standby_change == 'Q':
            text_to_speech("취소하였습니다.", "output.mp3")
            #딜레이 고민중
            standby() # 처음으로 돌아가는함수

def delete_thing_standby(socket_num): ## a번 약을 제거하려고함함
    ser = get_serial()
    while(True): # True가 어떤 역할인지? 신호를 받았을때 인지?
        if ser.in_waiting > 0: # 대기 시간?
            event = ser.read(1) #시리얼로 신호를 받을때
            standby_change = react_to_event(event)

        if standby_change == 'O':
            text_to_speech("물건정보를 제거 합니다", "output.mp3")
            #delete_schedule(str(a).encode()) # 엔코드가 b<-이거 붙여줌
            #약 스케줄 삭제 변수가 stm32 통신으로 받을 변수랑 똑같을 경우

            delete_socket_content(socket_num) # 이거 데이터베이스 번호랑 맞춰줘야함

            #딜레이 고민중
            # text_to_speech("처음으로 돌아갑니다", "output.mp3")

            #딜레이 고민중
            standby() # 처음으로 돌아가는 함수
            
        if standby_change == 'Q':
            text_to_speech("취소하였습니다.", "output.mp3")
            #딜레이 고민중
            standby() # 처음으로 돌아가는함수

def add_thing_standby_one():
    
    ser = get_serial()
    while True:
        if ser.in_waiting > 0:
            event = ser.read(1)
            standby_change = react_to_event(event)

            if standby_change == 'Q':  # 물음표 버튼 → standby() 호출
                text_to_speech("메뉴로 돌아갑니다.", "output.mp3")
                standby()
            elif standby_change == 'O':  # 원터치 버튼 → 음성 인식 실행
                analyze_thing()
                text_to_speech("이 물품을 보관하시겠습니까? 보관하시려면 원터치버튼을, 취소하시려면 물음표 버튼을 눌러주세요.", "output.mp3")
                add_thing_standby_two()
                
            else:
                print("잘못된 입력 감지")

def add_thing_standby_two():
    ser = get_serial()
    while True:
        if ser.in_waiting > 0:
            event = ser.read(1)
            standby_change = react_to_event(event)
            
            if standby_change == 'Q':  # 물음표 버튼 → standby() 호출
                text_to_speech("메뉴로 돌아갑니다.", "output.mp3")
                standby()
            elif standby_change == 'O':  # 원터치 버튼 → 음성 인식 실행
                text_to_speech("이 물품의 이름을 말해주세요.", "output.mp3")
                record_and_save_thing()
    return

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
        
    if normalized_text == "약추가" or normalized_text == "역추가":
        add_medicine()
    elif normalized_text == "약삭제" or normalized_text == "역삭제":
        delete_medicine()
    elif normalized_text == "약스케쥴" or normalized_text == "역스케쥴":
        listen_medicine_schedule()
    elif normalized_text == "물건추가" or normalized_text == "물품추가":
        add_thing()
    elif normalized_text == "물건삭제" or normalized_text == "물품삭제":
        delete_thing()
    else:
        print("No speech recognized.")
    return

def main_function2():
    text = "메뉴는 다음과 같습니다. 약추가. 약삭제. 약스케쥴 설명. 물품추가. 물품삭제. 물품묘사"
    text_to_speech(text, "output.mp3")
    main_function1()    
    return

# 약 추가 함수
def add_medicine():
    print("약추가 실행")
    text = "약 정보 메모지를 스테이지에 올려놓으신 후 원터치 버튼을 눌러주세요. 취소하시려면 물음표 버튼을 눌러주세요"
    text_to_speech(text, "output.mp3")
    try:
        # cap = init_camera()
        add_medicine_standby()
    except RuntimeError as e:
        print("Warning: Webcam initialization failed:", e)
    return

# 약 삭제 함수
def delete_medicine():
    print("약삭제 실행")
    text = "몇번 소켓의 약을 삭제 하시겠습니까?"
    text_to_speech(text, "output.mp3")
    
    #취소 누른 경우
    # if react_to_event(b'Q'): 
    #     standby()
    #delete_medicine_standby() 스탠바이를 어떤 형식으로 써야하는지
    #번호를 누르면 그거에따라 번호누르는 신호가 와야함
    recognized_text = record_and_recognize(duration=7, filename="recorded_audio.wav")
    
    if recognized_text:
        print(f"Recognized Speech: {recognized_text}")
        
        if recognized_text == "일번" or "1번" or "일본":
            text_to_speech("1번", "output.mp3")
            delete_number = 1
        elif recognized_text == "이번" or "2번":
            text_to_speech("2번", "output.mp3")
            delete_number = 2
        elif recognized_text == "삼번" or "3번":
            text_to_speech("3번", "output.mp3")
            delete_number = 3
        else:
            text_to_speech("죄송합니다. 소켓 번호를 인식하지 못했습니다.", "output.mp3")
            #다시 약삭제 함수 실행
            delete_medicine()

    # 여기에 딜레이를 넣어야할지 고민중
    text = "소켓에서 약을 제거해 주신 후 원터치 버튼을 눌러주세요. 취소하시려면 물음표버튼을 눌러주세요."
    text_to_speech(text, "output.mp3")
    delete_medicine_standby(delete_number) #이 함수에 딜리트 넘버를 넣음

    return

def listen_medicine_schedule():
    """
    Retrieves the medication schedules and status from the database and
    returns a descriptive string about which medicines (by socket) are scheduled
    and which time slots have not been taken yet.
    """
    from medication_db import get_all_schedules, get_all_statuses

    # Get all scheduled medications and their statuses.
    schedules = get_all_schedules()   # Each record: (id, medicine, socket, morning, lunch, dinner)
    statuses = get_all_statuses()       # Each record: (id, medicine, socket, morning, lunch, dinner)
    
    # Build a dictionary mapping socket to status record for easier lookup.
    status_dict = {}
    for stat in statuses:
        # Assuming the tuple structure is: (id, medicine, socket, morning, lunch, dinner)
        status_dict[stat[2]] = stat

    messages = []
    for sched in schedules:
        socket = sched[2]
        medicine = sched[1]
        # Determine which time slots are scheduled.
        scheduled_slots = []
        if sched[3]:
            scheduled_slots.append("아침")
        if sched[4]:
            scheduled_slots.append("점심")
        if sched[5]:
            scheduled_slots.append("저녁")
        
        # Check the corresponding status to see which slots remain not taken.
        not_taken = []
        stat = status_dict.get(socket)
        if stat:
            # Here, we assume that a value of 1 (or True) in the status means it has been taken.
            # So if the schedule indicates a slot (e.g., sched[3] is True) but the status is 0, it's not taken.
            if sched[3] and not stat[3]:
                not_taken.append("아침")
            if sched[4] and not stat[4]:
                not_taken.append("점심")
            if sched[5] and not stat[5]:
                not_taken.append("저녁")
        else:
            # No status record found; assume none of the scheduled slots have been taken.
            not_taken = scheduled_slots.copy()
        
        if not_taken:
            slots_str = ", ".join(not_taken)
            messages.append(f"{medicine} (소켓 {socket})은(는) {slots_str}에 복용 예정이나 아직 복용하지 않으셨습니다.")
        else:
            messages.append(f"{medicine} (소켓 {socket})은(는) 모두 복용하셨습니다.")
    
    if messages:
        return " ".join(messages)
    else:
        return "현재 복용 예정인 약이 없습니다."


def add_thing():
    print("물건추가 실행")
        
    text = "물건을 스테이지에 올려놓으신 후 원터치 버튼을 눌러주세요. 취소하시려면 물음표 버튼을 눌러주세요"
    text_to_speech(text, "output.mp3")
    add_thing_standby_one()

    return

def delete_thing():
    print("물건삭제 실행")
    text = "몇번 소켓의 물건을 삭제 하시겠습니까?"
    text_to_speech(text, "output.mp3")
    recognized_text = record_and_recognize(duration=7, filename="recorded_audio.wav")

    if recognized_text:
        print(f"Recognized Speech: {recognized_text}")
        
        if recognized_text == "일번" or "1번" or "일본":
            text_to_speech("1번", "output.mp3")
            delete_number = 1
        elif recognized_text == "이번" or "2번":
            text_to_speech("2번", "output.mp3")
            delete_number = 2
        elif recognized_text == "삼번" or "3번":
            text_to_speech("3번", "output.mp3")
            delete_number = 3
        else:
            text_to_speech("죄송합니다 소켓 번호를 인식하지 못했습니다", "output.mp3")
            #다시 물건삭제 함수 실행
            delete_thing()

    # 여기에 딜레이를 넣어야할지 고민중
    text = "소켓에서 물건을 제거해 주신 후 원터치 버튼을 눌러주세요, 취소하시려면 물음표버튼을 눌러주세요"
    text_to_speech(text, "output.mp3")
    delete_thing_standby(delete_number)

    return

def take_medicine(socket):
    """
    Called when a sensor signal (e.g., b'A', b'B', b'C') is received.
    Determines the current time slot and, if the medicine scheduled in the given socket
    has that slot enabled, increments the corresponding counter and announces the event.
    """
    print("약복용 실행")
    now = datetime.datetime.now()
    current_hour = now.hour
    slot = None
    # Define time ranges (adjust as needed)
    if 6 <= current_hour < 11:
        slot = "morning"
    elif 11 <= current_hour < 16:
        slot = "lunch"
    elif 17 <= current_hour < 22:
        slot = "dinner"
    else:
        # Default to morning if out of range
        slot = "morning"

    # Retrieve the medication schedule for this socket.
    schedule = get_schedule_by_socket(socket)
    if schedule is None:
        text_to_speech("해당 소켓의 약 정보가 없습니다.", "output.mp3")
        return

    # The schedule record is assumed to be:
    # (id, medicine, socket, morning, lunch, dinner)
    medicine = schedule[1]  # medicine name
    scheduled = False
    if slot == "morning" and schedule[3]:
        scheduled = True
    elif slot == "lunch" and schedule[4]:
        scheduled = True
    elif slot == "dinner" and schedule[5]:
        scheduled = True

    if scheduled:
        if increment_status_by_socket(socket, slot):
            announcement = f"{medicine} 약을 복용하셨습니다"
            text_to_speech(announcement, "output.mp3")
        else:
            text_to_speech("약 복용 처리에 실패하였습니다", "output.mp3")
    else:
        text_to_speech("현재 시간에 해당하는 복용 스케줄이 없습니다", "output.mp3")

def press_button(socket):
    from medication_db import get_schedule_by_socket, get_socket_content
    from speak import text_to_speech

    # Look for a medicine schedule in the given socket.
    schedule = get_schedule_by_socket(socket)
    # Look for a stored thing in the given socket.
    thing = get_socket_content(socket)

    announcement = ""
    if schedule:
        # The schedule record is assumed to be: (id, medicine, socket, morning, lunch, dinner)
        medicine = schedule[1]
        time_slots = []
        if schedule[3]:
            time_slots.append("아침")
        if schedule[4]:
            time_slots.append("점심")
        if schedule[5]:
            time_slots.append("저녁")
        if time_slots:
            slots_str = ", ".join(time_slots)
            announcement += f"소켓 {socket}에는 {medicine} 약이 있으며, {slots_str}에 섭취 예정입니다. "
        else:
            announcement += f"소켓 {socket}에는 {medicine} 약이 등록되어 있습니다. "
    if thing:
        announcement += f"{socket}번 소켓에는 {thing}가 보관되어 있습니다."
    if not announcement:
        announcement = f"소켓 {socket}은 비어있습니다."
    
    print("소켓내용 설명 실행:", announcement)
    text_to_speech(announcement, "output.mp3")
    return

# 빈 소켓을 찾는 함수
def get_empty_shared_socket():
    """Returns the first socket (from '1','2','3') that is not occupied by either a medication or a thing."""
    used = set()
    schedules = get_all_schedules()
    used.update({sched[2] for sched in schedules})
    for sock in ['1', '2', '3']:
        if get_socket_content(sock) is not None:
            used.add(sock)
    for sock in ['1', '2', '3']:
        if sock not in used:
            return sock
    return None

def record_and_save_thing():
    """사용자의 음성을 인식하여 물품명을 저장하고, 빈 소켓에 저장 후 안내 메시지를 음성 출력."""
    recognized_text = record_and_recognize(duration=5, filename="recorded_audio.wav")
    
    if recognized_text:
        empty_socket = get_empty_shared_socket()
        if empty_socket is None:
            text_to_speech("빈 소켓이 없습니다.", "output.mp3")
        else:
            add_socket_content(empty_socket, recognized_text)  # Save into the chosen socket.
            announcement = f"{recognized_text}가 {empty_socket}번 소켓에 보관 되었습니다."
            text_to_speech(announcement, "output.mp3")
    else:
        text_to_speech("음성을 인식하지 못했습니다.", "output.mp3")
        record_and_save_thing()  # Retry if recognition failed.

    # After adding, return to standby.
    standby()


def analyze_memo():
    global cap
    converter = MedicineScheduleConverter()
    converter.analyze_memo(cap)

    # 약 스케쥴 추가 한후 메인 스탠바이로 복귀
    standby()


def main():
    global cap

    init_db()
    print("Medication database initialized.\n")
    cap = init_camera()
    print("Webcam initialized and ready.")
    standby()
    # main_function1()
    # analyze_memo(cap)
    # capture_image(cap)

    release_camera(cap)

if __name__ == "__main__":
    main()
