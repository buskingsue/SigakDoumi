import cv2
import base64
from openai import OpenAI
from speak import text_to_speech  # Ensure this import matches your project structure

def read_api_key(file_path="api_gpt.txt"):
    """Read the API key from a file."""
    try:
        with open(file_path, "r") as file:
            api_key = file.read().strip()
            return api_key
    except FileNotFoundError:
        print(f"Error: '{file_path}' file not found.")
        return None
    except Exception as e:
        print(f"Error reading API key: {e}")
        return None

def encode_frame_to_base64(frame):
    """Encodes a frame (image) to a Base64 string."""
    ret, buffer = cv2.imencode('.jpg', frame)
    if not ret:
        print("Error: Could not encode frame to JPEG.")
        return None
    base64_image = base64.b64encode(buffer).decode('utf-8')
    return base64_image

def analyze_image(processed_image):
    """
    Encodes the processed image and uses OpenAI's ChatGPT to analyze it.
    The image is sent as a data URI along with a prompt asking for a description
    of the pharmaceutical information in the image.
    """
    base64_image = encode_frame_to_base64(processed_image)
    if base64_image is None:
        return None

    data_uri = f"data:image/jpeg;base64,{base64_image}"
    api_key = read_api_key()
    if not api_key:
        print("OpenAI API key not found.")
        return None

    client = OpenAI(api_key=api_key)
    try:
        response = client.chat.completions.create(
            model="chatgpt-4o-latest",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "첨부된 이미지가 어떤 물건인지 설명해줘. 만일 물건이 아니라 약 정보라면 어떤 질병에 먹는 약인지 알려줘. 한국어로 3문장 정도로 간단히 설명해줘 "
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": data_uri, "detail": "high"}
                        }
                    ]
                }
            ],
        )
        analysis = response.choices[0].message.content
        return analysis
    except Exception as e:
        print(f"Error during API call: {e}")
        return None

def capture_image_for_analysis(cap):
    """
    Captures one frame from the webcam, sets a high resolution,
    crops the region of interest (ROI), and returns the cropped image.
    """

    # Set high resolution for better detail
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    
    ret, frame = cap.read()
    cap.release()
    if not ret:
        print("Failed to capture frame from camera")
        return None

    # Define the crop box (ROI) coordinates similar to paddle_client.py
    start_x, start_y = 570, 150
    box_width, box_height = 800, 700
    end_x, end_y = start_x + box_width, start_y + box_height
    roi = frame[start_y:end_y, start_x:end_x]
    
    return roi

def analyze_thing(cap):
    """
    Captures an image from the webcam, analyzes it using ChatGPT via analyze_image,
    preprocesses the resulting text by removing all symbols, and then speaks the result using text_to_speech.
    """
    processed_image = capture_image_for_analysis(cap)
    if processed_image is None:
        print("Failed to capture image for analysis.")
        return

    analysis = analyze_image(processed_image)
    if analysis:
        # Preprocess the analysis text: remove all symbols, keeping only alphanumeric characters and whitespace.
        cleaned_analysis = ''.join(ch for ch in analysis if ch.isalnum() or ch.isspace() or ch == '.')
        print("ChatGPT Analysis (cleaned):")
        print(cleaned_analysis)
        text_to_speech(cleaned_analysis, "output.mp3")
    else:
        print("Image analysis failed.")
    return

if __name__ == "__main__":
    # Standalone test: initialize camera, capture image, and analyze it.
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open webcam")
    else:
        analyze_thing(cap)
