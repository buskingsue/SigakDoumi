import cv2

def init_camera():
    """Initializes and returns a persistent webcam capture object."""
    cap = cv2.VideoCapture(0)  # Open the webcam (adjust the index if needed)
    if not cap.isOpened():
        raise RuntimeError("Cannot open webcam")
    return cap

def capture_image(cap, save_path="captured_image.jpg"):
    """
    Captures an image from the given webcam capture object when 's' is pressed.
    Displays the live feed so the user can decide when to capture.
    """
    print("Press 's' to capture an image, or 'q' to cancel.")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not capture frame.")
            return None

        cv2.imshow("Webcam Feed", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('s'):
            cv2.imwrite(save_path, frame)
            print(f"Image captured and saved as {save_path}")
            cv2.destroyWindow("Webcam Feed")
            return save_path
        elif key == ord('q'):
            print("Image capture cancelled.")
            cv2.destroyWindow("Webcam Feed")
            return None

def release_camera(cap):
    """Releases the camera and closes all OpenCV windows."""
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    cap = init_camera()
    capture_image(cap)
    release_camera(cap)
