import pytesseract
from PIL import Image
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def run_ocr(image_path: str) -> str:
    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image)
        return text.strip()
    except Exception as e:
        print("OCR ERROR:", e)
        raise

# from PIL import Image
# import pytesseract

# # If Tesseract is not in your PATH, you must point to the executable

# # Open the image using PIL (Pillow)
# img = Image.open('xpost.jpeg')

# # Use PyTesseract to convert image to string
# text = pytesseract.image_to_string(img)

# print("Extracted Text:")
# print(text)