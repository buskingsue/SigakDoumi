def del_medicine_standby():
    """ 약 삭제 대기 함수: 사용자의 버튼 입력을 감지하여 삭제 실행 """
    ser = get_serial()
    while True:
        if ser.in_waiting > 0:
            event = ser.read(1)
            standby_change = react_to_event(event)

            if standby_change == 'O':  # 원터치 버튼 눌림 → 약 삭제 실행
                execute_delete_medicine()
            elif standby_change == 'Q':  # 물음표 버튼 눌림 → 대기 모드 복귀
                standby()
            else:
                print("잘못된 입력 감지")
    
#약 삭제 실행
def delete_medicine():
    print("약삭제 실행")
    text = "약을 제거해 주신후 원터치 눌러주세요 취소하시려면 물음표를 눌러주세요"
    text_to_speech(text, "output.mp3")
    del_medicine_standby()
    return

def add_thing_standby():
    """ 물건 추가 대기 함수: 사용자의 버튼 입력을 감지하여 OCR 실행 """
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

def analyze_thing_memo():
    """ 카메라로 물건 메모지 촬영 후 OCR 분석 """
    text_to_speech("메모지를 촬영합니다.", "capture_prompt.mp3")
    image_path = capture_image()  # 카메라로 이미지 촬영
    recognized_text = send_image_for_ocr(image_path)  # OCR 실행
    
    if recognized_text:
        text_to_speech(f"인식된 내용: {recognized_text}", "recognized.mp3")
        print(f"OCR 결과: {recognized_text}")
        add_socket_content(recognized_text)  # 데이터베이스에 저장
        text_to_speech("물건 정보가 저장되었습니다.", "save_success.mp3")
    else:
        text_to_speech("문자를 인식하지 못했습니다.", "ocr_fail.mp3")

def add_thing():
    """ 물건 추가 실행 함수: 음성 안내 후 대기 모드로 전환 """
    print("물건추가 실행")
    text_to_speech("물건 정보를 메모지에 적고, 스테이지에 올려놓은 후 원터치 버튼을 눌러주세요.", "add_thing_prompt.mp3")
    add_thing_standby()
