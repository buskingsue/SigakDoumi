# convert_to_medicine_schedule.py

from paddle_client import send_image_for_ocr
from medication_db import add_schedule, get_all_schedules, get_socket_content
from speak import text_to_speech
import time

class MedicineScheduleConverter:
    def analyze_memo(self, cap):
        print("메모 분석 OCR 실행")
        # Use the paddle_client function to capture and send the image for OCR
        ocr_text = send_image_for_ocr(cap)
        time.sleep(1)
        
        if ocr_text:
            print("OCR 결과:", ocr_text)
            self.parse_and_save(ocr_text)
        else:
            print("이미지를 캡처하지 못했습니다.")

    def get_empty_socket(self):
        """Returns the first socket ('1','2','3') that is not in use either by a medication schedule or a stored thing."""
        used_sockets = set()
        # Sockets used for medicine schedules.
        schedules = get_all_schedules()
        used_sockets.update({sched[2] for sched in schedules})
        # Sockets used for things.
        for sock in ['1', '2', '3']:
            if get_socket_content(sock) is not None:
                used_sockets.add(sock)
        for sock in ['1', '2', '3']:
            if sock not in used_sockets:
                return sock
        return None

    @staticmethod
    def process_medicine_tokens(tokens):
        """
        Combines tokens into a single medicine name. Any occurrence of '약'
        is removed from its original location and appended to the end.
        """
        medicine_parts = []
        has_yak = False
        for token in tokens:
            if "약" in token:
                token_without_yak = token.replace("약", "")
                if token_without_yak:
                    medicine_parts.append(token_without_yak)
                has_yak = True
            else:
                medicine_parts.append(token)
        medicine_name = "".join(medicine_parts)
        if has_yak:
            medicine_name += "약"
        return medicine_name

    def parse_and_save(self, ocr_text):
        lines = ocr_text.splitlines()
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # First, try splitting by comma. If only one token is found and it has spaces, split by whitespace.
            tokens = [token.strip() for token in line.split(',') if token.strip()]
            if len(tokens) == 1 and " " in tokens[0]:
                tokens = tokens[0].split()
            if not tokens:
                continue

            # Define scheduling keywords that denote schedule-related information.
            # Note that "하루" is included only to trigger scheduling extraction and will be ignored for naming.
            scheduling_keywords = ["아침", "점심", "저녁", "중식", "세번", "두번", "한번", "하루", "서번"]
            scheduling_tokens = []
            medicine_tokens = []
            for token in tokens:
                if any(keyword in token for keyword in scheduling_keywords):
                    scheduling_tokens.append(token)
                else:
                    medicine_tokens.append(token)

            # Process scheduling tokens for flags.
            morning = lunch = dinner = False
            for token in scheduling_tokens:
                # If token contains "세번" or "서번", set all scheduling flags.
                if "세번" in token or "서번" in token:
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
                # We ignore "하루" here as it is redundant.

            # Combine remaining tokens into the medicine name.
            medicine = MedicineScheduleConverter.process_medicine_tokens(medicine_tokens)
            if not medicine:
                print("No medicine name detected. Skipping entry.")
                continue

            socket = self.get_empty_socket()
            if socket is None:
                print(f"No available socket found for medicine: {medicine}. Skipping entry.")
                continue

            add_schedule(medicine, socket, morning, lunch, dinner)
            print(f"Added schedule: {medicine}, socket: {socket}, morning: {morning}, lunch: {lunch}, dinner: {dinner}")

            # Announce the addition via text-to-speech.
            announcement = f"{medicine} 을 {socket}번 소켓 스케쥴에 추가하였습니다"
            text_to_speech(announcement, "output.mp3")
