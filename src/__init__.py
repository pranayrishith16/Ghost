
"""
Legal RAG Project - Source Code Package

This package contains all the source code for the Legal RAG project,
including data processing, embedding, and MLflow pipeline modules.
"""

from .data_processing import get_ocr_reader, extract_text_using_ocr, extract_normal_pdf, process_case_pdf, clean_case_text, split_text
from .utils import config_load
from .mlflow_pipeline import process_pillar1, process_everything

__all__ = [
    'process_pillar1',
    'process_everything',
    'get_ocr_reader', 
    'extract_text_using_ocr', 
    'extract_normal_pdf',
    'process_case_pdf', 
    'clean_case_text', 
    'split_text',
    'config_load',
]