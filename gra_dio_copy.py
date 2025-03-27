import cv2
import requests
import gradio as gr
import numpy as np
from time import time

# 서버 및 인증 정보 설정
SERVER_IP = "61.108.166.15"  # 서버 IP를 올바르게 설정하세요
PORT_N = 5051
USER_ID = "team01"
USER_PW = "1234"  # 비밀번호 입력 필요
url = f"http://{SERVER_IP}:{PORT_N}/ocr"
auth = (USER_ID, USER_PW)

def capture_frame():
    """카메라에서 프레임을 캡처하여 RGB 이미지로 변환"""
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        return None
    
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return frame

def capture_and_ocr():
    """이미지를 캡처하고 OCR 서버에 전송한 후, 텍스트와 이미지를 반환"""
    frame = capture_frame()
    if frame is None:
        return "카메라 캡처 실패", None  # 두 개의 출력 값 반환
    
    img_path = "captured_image.jpg"
    cv2.imwrite(img_path, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
    
    # OCR 서버로 이미지 전송
    with open(img_path, "rb") as img_file:
        files = {"image": img_file}
        start_time = time()
        response = requests.post(url, auth=auth, files=files)
        end_time = time()
        print(f"처리 시간: {end_time - start_time:.2f}초")
    
    if response.status_code == 200:
        ocr_text = response.json().get("text", "OCR 결과 없음")
    else:
        ocr_text = f"Error: {response.status_code}"
    
    return ocr_text, frame  # OCR 결과와 캡처된 이미지 반환

# Gradio 인터페이스 설정
gui = gr.Interface(
    fn=capture_and_ocr,
    inputs=[],
    outputs=[gr.Textbox(label="OCR 결과"), gr.Image(label="캡처된 이미지")],
    title="OCR 카메라 인식",
    live=True
)

# Gradio 실행
gui.launch(share=True)
