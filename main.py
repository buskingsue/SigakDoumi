# main.py

import serial
from speak import text_to_speech
from stt import record_and_recognize
from camera import init_camera, capture_image, release_camera
from ocr import send_image_for_ocr  # New import
import os
import time, datetime
from chat import send_to_fastapi  # Import send_to_fastapi from chat.py
from wake_word_detector import WakeWordDetector

from threading import Thread
from image_analysis import analyze_thing
from medication_db import (
    init_db,
    get_cabinet_by_box_num,
    update_cabinet
)

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "credentials.json"

# 카메라 인스턴스 전역으로 선언
cap = None

#Dummy get_serial to simulate UART signals via keyboard input.
# def get_serial():
#     class DummySerial:
#         @property
#         def in_waiting(self):
#             # Always return 1, indicating there is user input waiting.
#             return 1

#         def read(self, size):
#             # Prompt the user to enter a simulated UART signal.
#             user_input = input("Simulated UART input (enter one character): ")
#             if user_input:
#                 # Return the first character as bytes.
#                 return user_input[0].encode()
#             else:
#                 return b''
#     return DummySerial()

# 버튼과 센서 쿨 타임 계산할 시간 기준
last_event_time = {}

def get_serial():
    ser = serial.Serial(
        port='/dev/ttyACM0',  # ST-LINK VCP port
        baudrate=115200,      # Baud rate (must match STM32 setting)
        timeout=1             # Read timeout (seconds)
    )

    print("Waiting for data from STM32...")
    print("Displaying data for 5 buttons (A, B, C, Q, O) and 3 IR sensors (1, 2, 3).")
    print("Press Ctrl+C to exit.\n")
    return ser

def standby():
    print("main stanby entered...")
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
            elif standby_change == 'A':
                take_medicine('A')
            elif standby_change == 'B':
                take_medicine('B')
            elif standby_change == 'C':
                take_medicine('C')

def react_to_event(event):
    current_time = time.time()
    # 만일 현재 이벤트가 5초 안에 연속으로 일어난것이면 무시
    if event in last_event_time and (current_time - last_event_time[event] < 5):
        print(f"Ignored repeated event: {event}")
        return None  # Don't return a valid command

    # 시간 업데이트
    last_event_time[event] = current_time

    if event == b'1':
        print("1번 소켓 버튼 눌림")
        return '1'
    elif event == b'2':
        print("1번 소켓 버튼 눌림")
        return '2'
    elif event == b'3':
        print("1번 소켓 버튼 눌림")
        return '3'
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
    # 음성인식 실행
    recognized_text = record_and_recognize(duration=7, filename="recorded_audio.wav")
    
    if recognized_text:
        # Normalize by removing all spaces
        normalized_text = recognized_text.replace(" ", "")
        print(f"Recognized Speech: {normalized_text}")

    else:
        print("No speech recognized.")
    return


def take_medicine(sensor):
    """
    Called when a sensor signal (e.g., b'A', b'B', b'C') is received.
    For non-medicine items, simply announces that the item was taken.
    For medicines, checks if it's the correct time to take it. If so,
    decrements total_amount and marks the status as taken (1). If not the right time,
    announces that either the medicine is already taken or it is not the correct time.
    If the cabinet is empty, announces that no item is registered.
    """
    print("약복용 실행")
    
    # Map sensor signals to cabinet box numbers.
    sensor_to_box = {'A': 1, 'B': 2, 'C': 3}
    box_num = sensor_to_box.get(sensor, sensor)  # Use sensor value as fallback if not found

    # Retrieve the cabinet details for the given box number
    cabinet_details = get_cabinet_by_box_num(box_num)
    
    if not cabinet_details:
        message = f"{box_num}번 보관함에 대한 정보를 찾을 수 없습니다."
        text_to_speech(message, "output.mp3")
        return message
    
    # Table column order:
    # 0: cabinet_id, 1: name, 2: box_num, 3: taken, 4: medicine_bool, 5: total_amount,
    # 6: breakfast, 7: lunch, 8: dinner, 9: breakfast_status, 10: lunch_status, 11: dinner_status, ...
    medicine_name    = cabinet_details[1]  # Name of the medicine or item
    taken            = cabinet_details[3]  # Boolean: whether the cabinet is occupied
    medicine_bool    = cabinet_details[4]  # Boolean: whether it's medicine or not
    total_amount     = cabinet_details[5]  # Total amount of medicine
    breakfast_flag   = cabinet_details[6]  # 1 if scheduled for breakfast, 0 otherwise
    lunch_flag       = cabinet_details[7]  # 1 if scheduled for lunch, 0 otherwise
    dinner_flag      = cabinet_details[8]  # 1 if scheduled for dinner, 0 otherwise
    breakfast_status = cabinet_details[9]  # 0 if not taken, 1 if taken (breakfast)
    lunch_status     = cabinet_details[10] # 0 if not taken, 1 if taken (lunch)
    dinner_status    = cabinet_details[11] # 0 if not taken, 1 if taken (dinner)
    
    # If the cabinet is empty, announce that nothing is registered.
    if not taken:
        message = f"{box_num}번 보관함에는 약이나 물건이 등록되어있지 않습니다."
        text_to_speech(message, "output.mp3")
        return message

    # If it's not medicine, announce that the item was taken.
    if not medicine_bool:
        message = f"{medicine_name}을 꺼내셨습니다."
        text_to_speech(message, "output.mp3")
        return message

    # Determine current time slot based on current hour.
    now = datetime.datetime.now()
    current_hour = now.hour
    slot = None
    if 6 <= current_hour < 11:
        slot = "breakfast"
    elif 11 <= current_hour < 16:
        slot = "lunch"
    elif 17 <= current_hour < 22:
        slot = "dinner"
    else:
        slot = "breakfast"  # Default to breakfast if out of range

    # Check if the scheduled flag is set and the status is not taken (0) for the current slot.
    scheduled = False
    if slot == "breakfast" and breakfast_flag == 1 and breakfast_status == 0:
        scheduled = True
    elif slot == "lunch" and lunch_flag == 1 and lunch_status == 0:
        scheduled = True
    elif slot == "dinner" and dinner_flag == 1 and dinner_status == 0:
        scheduled = True

    if scheduled:
        # If it's the right time, decrement total_amount and update the status to taken (1).
        new_total_amount = total_amount - 1
        if new_total_amount >= 0:
            # Prepare updated status values
            new_breakfast_status = breakfast_status
            new_lunch_status = lunch_status
            new_dinner_status = dinner_status
            if slot == "breakfast":
                new_breakfast_status = 1
            elif slot == "lunch":
                new_lunch_status = 1
            elif slot == "dinner":
                new_dinner_status = 1
            
            # Update the cabinet record.
            update_cabinet(
                medicine_name,
                box_num,
                taken=True,
                medicine_bool=True,
                total_amount=new_total_amount,
                breakfast=breakfast_flag,
                lunch=lunch_flag,
                dinner=dinner_flag,
                breakfast_status=new_breakfast_status,
                lunch_status=new_lunch_status,
                dinner_status=new_dinner_status
            )
            announcement = f"{medicine_name}을 복용하시기 위해 꺼내셨습니다. 남은 약은 {new_total_amount}일치입니다."
            text_to_speech(announcement, "output.mp3")
            return announcement
        else:
            announcement = f"{medicine_name}의 약이 부족하여 복용할 수 없습니다."
            text_to_speech(announcement, "output.mp3")
            return announcement
    else:
        # If it's not the right time or the medicine has already been taken.
        if slot == "breakfast" and breakfast_status == 1:
            message = f"{medicine_name}은 이미 복용하셨습니다."
            text_to_speech(message, "output.mp3")
            return message
        elif slot == "lunch" and lunch_status == 1:
            message = f"{medicine_name}은 이미 복용하셨습니다."
            text_to_speech(message, "output.mp3")
            return message
        elif slot == "dinner" and dinner_status == 1:
            message = f"{medicine_name}은 이미 복용하셨습니다."
            text_to_speech(message, "output.mp3")
            return message
        else:
            message = f"{medicine_name}을 복용하실 시간이 아닙니다."
            text_to_speech(message, "output.mp3")
            return message

def listen_medicine_schedule(socket):
    """
    Listens to the cabinet details when a button is pressed, provides information about
    which medicine is in that cabinet, how much is left, the schedule of when to take it,
    and whether it has been taken or not. If it's not medicine (i.e., medicine_bool is False),
    it will announce the item stored in the cabinet. If the cabinet is empty (taken is False),
    it will announce that the cabinet is empty.
    """
    # Get cabinet details for the given socket (box_num).
    cabinet_details = get_cabinet_by_box_num(socket)
    
    if not cabinet_details:
        message = f"보관함 {socket}에 대한 정보를 찾을 수 없습니다."
        text_to_speech(message, "output.mp3")
        return message

    # Column mapping based on the new table structure:
    # 0: cabinet_id, 1: name, 2: box_num, 3: taken, 4: medicine_bool, 5: total_amount,
    # 6: breakfast, 7: lunch, 8: dinner, 9: breakfast_status, 10: lunch_status, 11: dinner_status
    medicine_name    = cabinet_details[1]
    taken            = cabinet_details[3]
    medicine_bool    = cabinet_details[4]
    total_amount     = cabinet_details[5]
    breakfast_flag   = cabinet_details[6]
    lunch_flag       = cabinet_details[7]
    dinner_flag      = cabinet_details[8]
    breakfast_status = cabinet_details[9]
    lunch_status     = cabinet_details[10]
    dinner_status    = cabinet_details[11]
    
    # If the cabinet is empty, announce it.
    if not taken:
        message = f"{socket}번 보관함은 현재 비어있습니다."
        text_to_speech(message, "output.mp3")
        return message

    # If it's not medicine, announce that the item is stored.
    if not medicine_bool:
        message = f"{socket}번 보관함에는 {medicine_name}이 보관되어 있습니다."
        text_to_speech(message, "output.mp3")
        return message

    # Build the schedule time string for medicine.
    scheduled_times = []
    if breakfast_flag:
        scheduled_times.append("아침")
    if lunch_flag:
        scheduled_times.append("점심")
    if dinner_flag:
        scheduled_times.append("저녁")
    
    if not scheduled_times:
        scheduled_str = "복용 스케쥴이 지정되어 있지 않습니다."
    else:
        scheduled_str = " ".join(scheduled_times) + "으로 복용하고 계십니다."

    # Build the intake status string.
    intake_status_parts = []
    if breakfast_flag:
        status = "드셨습니다." if breakfast_status == 1 else "아직 안드셨습니다."
        intake_status_parts.append(f"아침약은 {status}")
    if lunch_flag:
        status = "드셨습니다." if lunch_status == 1 else "아직 안드셨습니다."
        intake_status_parts.append(f"점심약은 {status}")
    if dinner_flag:
        status = "드셨습니다." if dinner_status == 1 else "아직 안드셨습니다."
        intake_status_parts.append(f"저녁약은 {status}")
    
    intake_status_str = " , ".join(intake_status_parts)
    
    # Build the remaining medicine amount string.
    remaining_str = f"현재 약은 {total_amount}일치가 남아있습니다." if total_amount is not None else ""
    
    # Final message.
    final_message = (
        f"{medicine_name}은 {socket}번 보관함에 보관되어 있으며, {scheduled_str} "
        f"{remaining_str} 오늘 {intake_status_str}."
    )
    
    text_to_speech(final_message, "output.mp3")
    return final_message

def analyze_thing_main():
    analyze_thing(cap)

def press_button(socket):
    """
    Function to press a button, check the cabinet info, and announce the schedule and
    remaining amount of medicine.
    """
    # Listen to the medicine schedule in the cabinet
    message = listen_medicine_schedule(socket)
    print(message)
    return message

#쓰레드로 시리얼 신호 받기 준비
def serial_standby():
    print("main serial standby entered...")
    # Start the serial listener in the background
    serial_thread = Thread(target=standby, daemon=True)
    serial_thread.start()

    # Main logic for standby mode (other tasks can go here, e.g., wait for a button press)
    while True:
        time.sleep(1)  # This prevents blocking and keeps the main loop running

def chat_with_agent():
    #Start speech recognition
    recognized_text = record_and_recognize(duration=10, filename="recorded_audio.wav")
    
    if recognized_text:
        # Normalize by removing all spaces
        normalized_text = recognized_text.replace(" ", "")
        print(f"Recognized Speech: {normalized_text}")

        # Send recognized text to FastAPI for processing
        conversation_id = "default"  # Default or dynamically generated conversation ID
        current_step = None  # This can be updated based on backend responses

        # Send to FastAPI and receive response
        answer, intent, current_step, context = send_to_fastapi(normalized_text, conversation_id, current_step)

        # Print FastAPI response
        print("AI:", answer)
        print("Intent:", intent)

        # Speak the response out loud
        text_to_speech(answer, "output.mp3")

        # Handle the intent (trigger actions, etc.)
        if intent:
            print(f"Intent detected: {intent}")
            handle_action(intent)
    else:
        print("No speech recognized.")

def wake_standby():
    """Starts the wake word detector in its own thread."""
    access_key = '4Oq64nx56v+RmQxw19SRrmshUDz3enMp6oDoUKn1aO7TITdw3BtkwQ=='
    # Provide the keyword file as a list.
    keyword_paths = ['/home/abcd/PythonProjects/SigakDoumi/yakson_ko_raspberry-pi_v3_0_0.ppn']
    model_path = '/home/abcd/PythonProjects/SigakDoumi/porcupine_params_ko.pv'

    detector = WakeWordDetector(
        callback=chat_with_agent,
        access_key=access_key,
        keyword_paths=keyword_paths,  # Now explicitly a list.
        model_path=model_path
    )
    
    wake_thread = Thread(target=detector.run, daemon=True)
    wake_thread.start()
def main():
    global cap
    print("Starting main function: Speech recognition and interaction with FastAPI")
    
    # Initialize the camera and the database
    init_db()
    print("Medication database initialized.\n")
    cap = init_camera()
    print("Webcam initialized and ready.")
    wake_standby()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
        release_camera(cap)

def handle_action(intent):
    global cap
    print("handle action method")
    if intent == "DESCRIBE_THING":
        print("handle action: describe thing")
        analyze_thing(cap)
        print("Performing action: analyze image")
        # Trigger the corresponding action on Raspberry Pi or your system
        # You can add more logic here to interact with databases, APIs, etc.



if __name__ == "__main__":
    serial_thread = Thread(target=serial_standby, daemon=True)
    serial_thread.start()
    # serial_standby()
    main()