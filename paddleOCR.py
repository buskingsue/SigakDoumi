import cv2
import numpy as np
import platform
from PIL import ImageFont, ImageDraw, Image
from matplotlib import pyplot as plt
from paddleocr import PaddleOCR, draw_ocr
from paddleocr.paddleocr import MODEL_URLS

# ==========================
# Utility Functions
# ==========================
def plt_imshow(title='image', img=None, figsize=(8, 5)):
    plt.figure(figsize=figsize)
    if isinstance(img, str):
        img = cv2.imread(img)
    if isinstance(img, list):
        if isinstance(title, list):
            titles = title
        else:
            titles = [title] * len(img)
        for i in range(len(img)):
            if len(img[i].shape) <= 2:
                rgbImg = cv2.cvtColor(img[i], cv2.COLOR_GRAY2RGB)
            else:
                rgbImg = cv2.cvtColor(img[i], cv2.COLOR_BGR2RGB)
            plt.subplot(1, len(img), i + 1), plt.imshow(rgbImg)
            plt.title(titles[i])
            plt.xticks([]), plt.yticks([])
        plt.show()
    else:
        if len(img.shape) < 3:
            rgbImg = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        else:
            rgbImg = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        plt.imshow(rgbImg)
        plt.title(title)
        plt.xticks([]), plt.yticks([])
        plt.show()


def put_text(image, text, x, y, color=(0, 255, 0), font_size=22):
    if isinstance(image, np.ndarray):
        color_converted = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(color_converted)
    if platform.system() == 'Darwin':
        font_path = 'AppleGothic.ttf'
    elif platform.system() == 'Windows':
        font_path = 'malgun.ttf'
    else:
        font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    image_font = ImageFont.truetype(font_path, font_size)
    draw = ImageDraw.Draw(image)
    draw.text((x, y), text, font=image_font, fill=color)
    numpy_image = np.array(image)
    opencv_image = cv2.cvtColor(numpy_image, cv2.COLOR_RGB2BGR)
    return opencv_image


def group_text_by_columns(ocr_results, threshold=50):
    """
    Groups OCR detections (each is [bbox, (text, confidence)]) into columns.
    The grouping is based on the x-coordinate of the top-left point.
    """
    detections = []
    for det in ocr_results:
        x_val = det[0][0][0]
        y_val = det[0][0][1]
        text = det[1][0]
        detections.append((x_val, y_val, text))
    detections.sort(key=lambda d: d[0])
    columns = []
    for d in detections:
        if not columns:
            columns.append([d])
        else:
            placed = False
            for col in columns:
                col_avg_x = sum([item[0] for item in col]) / len(col)
                if abs(d[0] - col_avg_x) < threshold:
                    col.append(d)
                    placed = True
                    break
            if not placed:
                columns.append([d])
    for col in columns:
        col.sort(key=lambda d: d[1])
    columns.sort(key=lambda col: sum([item[0] for item in col]) / len(col))
    return columns


def format_columns_text(columns):
    """
    Returns a formatted string that reflects the text in each column.
    Columns are separated by a blank line.
    """
    column_texts = []
    for col in columns:
        texts = [d[2] for d in col]
        col_text = "\n".join(texts)
        column_texts.append(col_text)
    return "\n\n".join(column_texts)


# ==========================
# MyPaddleOCR Class (Modified)
# ==========================
class MyPaddleOCR:
    def __init__(self, lang: str = "korean", **kwargs):
        self.lang = lang
        self._ocr = PaddleOCR(lang="korean")
        self.img = None  # holds the current image (numpy array)
        self.ocr_result = {}

    def get_available_langs(self):
        langs_info = []
        for idx, model_name in enumerate(list(MODEL_URLS['OCR'].keys())):
            for lang in list(MODEL_URLS['OCR'][model_name]['rec'].keys()):
                if lang not in langs_info:
                    langs_info.append(lang)
        print('Available Language : {}'.format(langs_info))

    def get_available_models(self):
        for idx, model_name in enumerate(list(MODEL_URLS['OCR'].keys())):
            models = list(MODEL_URLS['OCR'][model_name]['rec'].keys())
            print('#{} Model Version : [{}] - Language : {}'.format(idx + 1, model_name, models))

    def get_ocr_result(self):
        return self.ocr_result

    def show_img(self):
        plt_imshow("Image", self.img)

    def run_ocr(self, img_input, debug: bool = False):
        """
        Accepts either a file path (str) or a numpy array.
        """
        if isinstance(img_input, str):
            self.img = cv2.imread(img_input)
        else:
            self.img = img_input.copy()

        result = self._ocr.ocr(self.img, cls=False)
        if result and len(result) > 0:
            self.ocr_result = result[0]
        else:
            self.ocr_result = []
        ocr_text = []
        if self.ocr_result:
            for r in self.ocr_result:
                ocr_text.append(r[1][0])
        else:
            ocr_text = "No text detected."

        if debug:
            self.show_img_with_ocr()

        return ocr_text

    def show_img_with_ocr(self):
        img = self.img.copy()
        roi_img = img.copy()
        for text_result in self.ocr_result:
            text = text_result[1][0]
            tlX = int(text_result[0][0][0])
            tlY = int(text_result[0][0][1])
            trX = int(text_result[0][1][0])
            trY = int(text_result[0][1][1])
            brX = int(text_result[0][2][0])
            brY = int(text_result[0][2][1])
            blX = int(text_result[0][3][0])
            blY = int(text_result[0][3][1])
            topLeft = (tlX, tlY)
            topRight = (trX, trY)
            bottomRight = (brX, brY)
            bottomLeft = (blX, blY)
            cv2.line(roi_img, topLeft, topRight, (0, 255, 0), 2)
            cv2.line(roi_img, topRight, bottomRight, (0, 255, 0), 2)
            cv2.line(roi_img, bottomRight, bottomLeft, (0, 255, 0), 2)
            cv2.line(roi_img, bottomLeft, topLeft, (0, 255, 0), 2)
            roi_img = put_text(roi_img, text, topLeft[0], topLeft[1] - 20, font_size=15)
        plt_imshow(["Original", "OCR ROI"], [self.img, roi_img], figsize=(16, 10))


# ==========================
# Main: Webcam Capture, Real-time Processing, GUI & OCR
# ==========================
def main():
    # Create an instance of MyPaddleOCR
    ocr_processor = MyPaddleOCR(lang="korean")

    # Open the external webcam (adjust index as needed)
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Cannot open webcam")

    # Disable autofocus and set manual focus (adjust value as needed)
    cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
    cap.set(cv2.CAP_PROP_FOCUS, 100)

    # Set high resolution for better OCR accuracy
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

    # Define the crop box (ROI) coordinates
    box_width, box_height = 600, 500  # Target area dimensions
    start_x = 170
    start_y = 150
    end_x = start_x + box_width
    end_y = start_y + box_height

    # Create a window for settings and add trackbars
    cv2.namedWindow("Settings")
    cv2.createTrackbar("ClipLimit", "Settings", 2, 10, lambda x: None)      # CLAHE clipLimit (1-10)
    cv2.createTrackbar("Erosion", "Settings", 0, 5, lambda x: None)           # Erosion iterations (0-5)
    cv2.createTrackbar("Kernel Size", "Settings", 0, 10, lambda x: None)      # Kernel size (1-10)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Can't receive frame. Exiting...")
            break

        # Draw the rectangle on the live feed to indicate the OCR target area
        cv2.rectangle(frame, (start_x, start_y), (end_x, end_y), (0, 255, 0), 2)

        # Crop the ROI from the frame
        roi = frame[start_y:end_y, start_x:end_x]

        # Retrieve settings from trackbars
        clip_val = cv2.getTrackbarPos("ClipLimit", "Settings")
        erosion_iter = cv2.getTrackbarPos("Erosion", "Settings")
        kernel_size = cv2.getTrackbarPos("Kernel Size", "Settings")
        if kernel_size < 1:
            kernel_size = 1
        if kernel_size % 2 == 0:
            kernel_size += 1

        # --- Image Processing Pipeline ---
        gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=float(clip_val), tileGridSize=(8, 8))
        contrast_roi = clahe.apply(gray_roi)
        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        processed_roi = cv2.erode(contrast_roi, kernel, iterations=erosion_iter)
        # --- End Processing Pipeline ---

        cv2.imshow("Webcam - Original", frame)
        cv2.imshow("Processed ROI", processed_roi)

        key = cv2.waitKey(1) & 0xFF

        if key == ord('s'):
            cv2.imwrite("processed_roi.jpg", processed_roi)
            print("Processed ROI saved as 'processed_roi.jpg'")

            # Convert processed ROI back to BGR (3-channel) for PaddleOCR
            processed_roi_bgr = cv2.cvtColor(processed_roi, cv2.COLOR_GRAY2BGR)
            texts = ocr_processor.run_ocr(processed_roi_bgr, debug=True)
            print("\nRaw OCR Texts:")
            if isinstance(texts, list):
                for t in texts:
                    print(t)
            else:
                print(texts)

            # --- Group detections into columns ---
            if ocr_processor.ocr_result:
                columns = group_text_by_columns(ocr_processor.ocr_result, threshold=50)
                formatted_text = format_columns_text(columns)
                print("\nFormatted OCR Text (Grouped by Columns):")
                print(formatted_text)
            else:
                print("No OCR detections to group.")

        if key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
