"""
Data Processing Module

This module contains all data processing functionality for the Legal RAG project,
including PDF extraction, OCR, text splitting, and pillar-specific processors.
"""

from .base_extractor import get_ocr_reader, extract_text_using_ocr, extract_normal_pdf
from .case_extractor import process_case_pdf, clean_case_text, split_text

__all__ = [
    'get_ocr_reader', 
    'extract_text_using_ocr', 
    'extract_normal_pdf',
    'process_case_pdf', 
    'clean_case_text', 
    'split_text'
]