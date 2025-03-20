import cv2
import base64
from openai import OpenAI

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
                            "text": "첨부된 이미지는 약 정보야. 이것들이 어떤 약인지, 어떤 질병에 먹는 약인지 알려줘 "
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

if __name__ == "__main__":
    # For standalone testing, load an image file named 'captured_image.jpg'
    test_image = cv2.imread("captured_image.jpg")
    if test_image is not None:
        result = analyze_image(test_image)
        print("ChatGPT Analysis:")
        print(result)
    else:
        print("Test image not found.")
