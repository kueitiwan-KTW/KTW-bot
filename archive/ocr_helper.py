import pytesseract
from PIL import Image
import io

class OCRHelper:
    def __init__(self):
        # You might need to set the tesseract path if it's not in PATH
        # pytesseract.pytesseract.tesseract_cmd = r'/usr/local/bin/tesseract'
        pass

    def extract_text_from_image(self, image_data):
        """
        Extracts text from image bytes.
        :param image_data: Bytes of the image
        :return: Extracted text string
        """
        try:
            image = Image.open(io.BytesIO(image_data))
            text = pytesseract.image_to_string(image, lang='eng+chi_tra') # Support English and Traditional Chinese
            return text
        except Exception as e:
            print(f"OCR Error: {e}")
            return ""
