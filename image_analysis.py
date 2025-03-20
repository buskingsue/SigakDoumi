from google.cloud import vision
import io


def analyze_image(image_path):
    """Analyzes an image and provides object descriptions & text extraction."""

    # Initialize Google Cloud Vision client
    client = vision.ImageAnnotatorClient()

    # Read image file
    with io.open(image_path, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    # Perform label detection (describes objects in image)
    response = client.label_detection(image=image)
    labels = response.label_annotations

    print("\n🖼️ Image Analysis Result:")
    descriptions = [label.description for label in labels]
    print("Detected Objects:", ", ".join(descriptions))

    # Perform text detection (OCR)
    text_response = client.text_detection(image=image)
    texts = text_response.text_annotations

    if texts:
        print("\n📝 Detected Text:")
        print(texts[0].description)
    else:
        print("\n❌ No text detected.")

    return {"labels": descriptions, "text": texts[0].description if texts else None}


if __name__ == "__main__":
    analyze_image("captured_image.jpg")  # Run standalone with an image
