def del_medicine_standby():
    
#약 삭제 실행
def delete_medicine():
    print("약삭제 실행")
    text = "약을 제거해 주신후 원터치 눌러주세요 취소하시려면 물음표를 눌러주세요"
    text_to_speech(text, "output.mp3")
    del_medicine_standby()
    return

