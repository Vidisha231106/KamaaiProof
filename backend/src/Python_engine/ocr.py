import pytesseract
from PIL import Image
import cv2
import numpy as np

# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def preprocess_image(image):
    img = np.array(image)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    
    # Scale up the image — bigger image = Tesseract reads small text better
    scale = 2
    width = int(gray.shape[1] * scale)
    height = int(gray.shape[0] * scale)
    gray = cv2.resize(gray, (width, height), interpolation=cv2.INTER_CUBIC)
    
    # Sharpen the image
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    gray = cv2.filter2D(gray, -1, kernel)
    
    # Threshold
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    
    return Image.fromarray(thresh)


def extract_text_from_image(image_path: str) -> str:
    """
    Main function. Takes a path to any image file.
    Returns the raw text found in that image as a string.
    
    Example:
        text = extract_text_from_image("documents/phonePe_sample.jpg")
        print(text)
        # "Paid ₹2500 to Rahul Sharma SUCCESS 15/03/2025 ..."
    """
    # Open the image
    image = Image.open(image_path)
    
    # Convert to RGB — important for PNGs that have transparency
    image = image.convert("RGB")
    
    # Preprocess to improve accuracy
    image = preprocess_image(image)
    
    # Run OCR — lang="eng" tells Tesseract to look for English text
    raw_text = pytesseract.image_to_string(image, lang="eng", config='--psm 6')
    
    # Strip leading/trailing whitespace and return
    return raw_text.strip()


# This block only runs if you run this file directly
# Use it to quickly test OCR on any image
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python ocr.py <path_to_image>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    text = extract_text_from_image(image_path)
    
    print("=== RAW TEXT EXTRACTED ===")
    print(text)
    print("==========================")