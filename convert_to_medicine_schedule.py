# convert_to_medicine_schedule.py

from camera import init_camera, capture_image, release_camera
from ocr import send_image_for_ocr
from medication_db import add_schedule, get_all_schedules

class MedicineScheduleConverter:
    def analyze_memo(self):
        print("메모 분석 OCR 실행")
        cap = init_camera()
        image_path = capture_image(cap, save_path="memo_image.jpg")
        release_camera(cap)
        if image_path:
            ocr_text = send_image_for_ocr(image_path)
            print("OCR 결과:", ocr_text)
            self.parse_and_save(ocr_text)
        else:
            print("이미지를 캡처하지 못했습니다.")

    def get_empty_socket(self):
        """
        Checks the medication_schedule table for used sockets and returns
        the next available socket number (as a string) from '1', '2', or '3'.
        Returns None if all sockets are occupied.
        """
        schedules = get_all_schedules()
        used_sockets = set()
        for sched in schedules:
            # Each schedule row: (id, medicine, socket, morning, lunch, dinner)
            used_sockets.add(sched[2])
        for sock in ['1', '2', '3']:
            if sock not in used_sockets:
                return sock
        return None

    def parse_and_save(self, ocr_text):
        # Process each line of the OCR result; each line represents one memo.
        lines = ocr_text.splitlines()
        for line in lines:
            line = line.strip()
            if not line:
                continue  # Skip empty lines

            # Split by commas to extract tokens.
            tokens = [token.strip() for token in line.split(',') if token.strip()]
            if not tokens:
                continue

            # The first token is the medicine name.
            medicine = tokens[0]
            # Default schedule: all times set to False.
            morning = False
            lunch = False
            dinner = False

            # Process each additional token to detect schedule times.
            for token in tokens[1:]:
                # If token indicates three times a day, set all True.
                if "세번" in token:
                    morning, lunch, dinner = True, True, True
                # If token indicates twice a day, assume morning and dinner.
                elif "두번" in token:
                    morning, dinner = True, True

                # Check for explicit time keywords.
                if "아침" in token:
                    morning = True
                if "점심" in token or "중식" in token:
                    lunch = True
                if "저녁" in token:
                    dinner = True

                # If only "한번" is mentioned without any specific time, default to morning.
                if "한번" in token and not (morning or lunch or dinner):
                    morning = True

            # Determine the next empty socket.
            socket = self.get_empty_socket()
            if socket is None:
                print(f"No available socket found for medicine: {medicine}. Skipping entry.")
                continue

            # Insert the medicine schedule into the database using the found socket.
            add_schedule(medicine, socket, morning, lunch, dinner)
            print(f"Added schedule: {medicine}, socket: {socket}, morning: {morning}, lunch: {lunch}, dinner: {dinner}")
