# paddle_client.py

import cv2
import numpy as np
import requests
from requests.auth import HTTPBasicAuth

# Server connection settings
SERVER_URL = "http://61.108.166.15:5057/ocr"
USER_ID = "team01"
USER_PW = "1234"

def send_image_for_ocr(cap):
    """
    Captures one frame from the provided camera instance,
    crops the ROI, sends it to the OCR server, and returns the recognized text.
    """
    # Set high resolution for better OCR accuracy
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    
    ret, frame = cap.read()
    if not ret:
        print("Failed to capture frame from camera")
        return None

    # Define the crop box (ROI) coordinates
    start_x, start_y = 170, 150
    box_width, box_height = 600, 500
    end_x, end_y = start_x + box_width, start_y + box_height
    roi = frame[start_y:end_y, start_x:end_x]



    # Encode ROI as JPEG in memory
    ret2, buffer = cv2.imencode('.jpg', roi)
    if not ret2:
        print("Failed to encode ROI")
        return None

    img_bytes = buffer.tobytes()
    files = {'image': ('roi.jpg', img_bytes, 'image/jpeg')}

    try:
        response = requests.post(SERVER_URL, files=files, auth=HTTPBasicAuth(USER_ID, USER_PW))
        if response.status_code == 200:
            result = response.json()
            return result.get("text")
        else:
            print("Error:", response.status_code, response.text)
            return None
    except Exception as e:
        print("Request error:", str(e))
        return None

# Optional standalone test function
def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open webcam")
        return

    # Wait a moment for the camera to adjust
    cv2.waitKey(1000)
    
    ocr_text = send_image_for_ocr(cap)
    if ocr_text:
        print("OCR Text:", ocr_text)
    else:
        print("Failed to get OCR text.")
    
    cap.release()

if __name__ == "__main__":
    main()
