from pathlib import Path
from typing import Dict,Any
import fitz
import easyocr
import pdfplumber

import sys

#FIXING IMPORT PATH
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.settings import get_config

from src.interfaces.document_processor import DocumentProcessorInterface
from src.document_processing.text_cleaner import TextCleaner
from src.document_processing.metadata_extractor import MetadataExtractor

class PDFExtractor(DocumentProcessorInterface):
    """Implementation for PDF extraction"""
    def __init__(self):
        self.config = get_config()
        self.text_cleaner = TextCleaner()
        # self.metadata_extractor = MetadataExtractor()

    def extract_text(self, file_path):
        try:
            #primary extraction using fitz
            doc = fitz.open(file_path)
            full_txt = ""

            for page in doc:
                text = page.get_text()
                if text:
                    full_txt += text + '\n'
            
            if text.strip():
                return self.text_cleaner.clean_text(full_txt)

        except Exception as e:
            pass

    def extract_metadata(self, file_path):
        """Extract metadata of the file"""
        try:
            with pdfplumber.open(file_path) as pdf:
                metadata = pdf.metadata or {}

            # #extract legal case metadata from text
            # text = self.extract_text(file_path)
            # case_metadata = self.metadata_extractor.extract_legal_metadata(text)

            #file metadata
            file_metadata = {
                'filename': file_path.name,
                'file_size': file_path.stat().st_size,
                'pages': len(pdf.pages),
                'creation_date': file_path.stat().st_ctime,
            }

            return {
                **metadata, 
                # **case_metadata, 
                **file_metadata
                }

        except:
            pass

    def process_document(self, file_path):
        """Main processing method"""
        if not self.validate_document(file_path):
            raise ValueError(f"Invalid PDF file: {file_path}")

        text = self.extract_text(file_path)
        metadata = self.extract_metadata(file_path)

        return {
            'text': text,
            'metadata': metadata,
            'word_count': len(text.split()),
            'char_count': len(text)
        }
    
    def validate_document(self, file_path):
        """Validate PDF file"""
        if not file_path.exists():
            return False

        if file_path.suffix.lower() != '.pdf':
            return False

        try:
            with pdfplumber.open(file_path) as pdf:
                return len(pdf.pages) > 0
        except:
            return False


