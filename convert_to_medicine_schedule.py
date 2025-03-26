from camera import capture_image  # removed init_camera and release_camera here
from ocr import send_image_for_ocr
from medication_db import add_schedule, get_all_schedules
import time

class MedicineScheduleConverter:
    def analyze_memo(self, cap):
        print("메모 분석 OCR 실행")
        image_path = capture_image(cap, save_path="memo_image.jpg")
        
        time.sleep(1)
        
        if image_path:
            ocr_text = send_image_for_ocr(image_path)
            time.sleep(1)
            
            print("OCR 결과:", ocr_text)
            self.parse_and_save(ocr_text)
        else:
            print("이미지를 캡처하지 못했습니다.")

    def get_empty_socket(self):
        schedules = get_all_schedules()
        used_sockets = {sched[2] for sched in schedules}
        for sock in ['1', '2', '3']:
            if sock not in used_sockets:
                return sock
        return None

    def parse_and_save(self, ocr_text):
        lines = ocr_text.splitlines()
        for line in lines:
            line = line.strip()
            if not line:
                continue
            tokens = [token.strip() for token in line.split(',') if token.strip()]
            if not tokens:
                continue
            medicine = tokens[0]
            morning = lunch = dinner = False
            for token in tokens[1:]:
                if "세번" in token:
                    morning, lunch, dinner = True, True, True
                elif "두번" in token:
                    morning, dinner = True, True
                if "아침" in token:
                    morning = True
                if "점심" in token or "중식" in token:
                    lunch = True
                if "저녁" in token:
                    dinner = True
                if "한번" in token and not (morning or lunch or dinner):
                    morning = True
            socket = self.get_empty_socket()
            if socket is None:
                print(f"No available socket found for medicine: {medicine}. Skipping entry.")
                continue
            add_schedule(medicine, socket, morning, lunch, dinner)
            print(f"Added schedule: {medicine}, socket: {socket}, morning: {morning}, lunch: {lunch}, dinner: {dinner}")
