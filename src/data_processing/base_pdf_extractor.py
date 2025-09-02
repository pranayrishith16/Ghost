import fitz
import easyocr
from PIL import Image
import io
import numpy as np
from pathlib import Path

# Initialize OCR engine once (singleton pattern)
_reader = None

def get_ocr_reader():
    """Initialize and return the OCR reader (singleton)"""
    global _reader
    if _reader is None:
        print('Initializing OCR engine...')
        _reader = easyocr.Reader(['en'])
    return _reader

def extract_text_using_ocr(pdf_path):
    """Shared OCR function for all pillars"""
    reader = get_ocr_reader()
    doc = fitz.open(pdf_path)
    full_txt = ""

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        mat = fitz.Matrix(2.0, 2.0)
        pix = page.get_pixmap(matrix=mat)
        
        img_bytes = pix.tobytes("ppm")
        pil_image = Image.open(io.BytesIO(img_bytes))
        img_array = np.array(pil_image)

        results = reader.readtext(img_array, detail=0)
        page_text = " ".join(results)
        full_txt += page_text + "\n"
    
    doc.close()
    return full_txt

def extract_normal_pdf(pdf_path):
    """Shared normal PDF extraction for all pillars"""
    doc = fitz.open(pdf_path)
    full_text = ""
    
    for page in doc:
        text = page.get_text()
        if text.strip():
            full_text += text + "\n"
    
    doc.close()
    return full_text if full_text.strip() else None