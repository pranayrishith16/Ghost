from curses import meta
from pathlib import Path
import pymupdf
import pdfplumber
import fitz

import sys

#correct import
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.settings import get_config

from src.interfaces.document_processing_interface import DocumentProcessorInterface

class PDFExtractor(DocumentProcessorInterface):
    def __init__(self):
        self.config = get_config()

    def extract_text(self, file_path):
        doc = fitz.open(file_path)
        full_txt = ""
        for page in doc:
            txt = page.get_text()
            full_txt += txt
        return full_txt

    def extract_metadata(self, file_path):
        with pdfplumber.open(file_path) as pdf:
            metadata = pdf.metadata or {}

        file_metadata = {
                'filename': file_path.name,
                'file_size': file_path.stat().st_size,
                'pages': len(pdf.pages),
                'creation_date': file_path.stat().st_ctime,
            }

        return {
            **metadata, 
            **file_metadata
            }


    def process_document(self, file_path):
        if not self.validate_document(file_path):
            raise ValueError(f'Invalid file document: {file_path}')
        
        text = self.extract_text(file_path)
        metadata = self.extract_metadata(file_path)

        return {
            'text':text,
            'metadata':metadata,
            'word_count': len(text.split()),
            'char_count': len(text)
        }

    def validate_document(self, file_path):
        if not file_path.exists():
            return False
        
        if file_path.suffix.lower() != '.pdf':
            return False

        return True