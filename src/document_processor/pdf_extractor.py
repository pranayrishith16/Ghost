from pathlib import Path
from typing import Dict, Any
from loguru import logger

import fitz  # PyMuPDF

from src.interfaces.document_processing_interface import DocumentProcessorInterface

class PDFExtractor(DocumentProcessorInterface):
    def extract_text(self, file_path: Path) -> str:
        
        try:
            with fitz.open(str(file_path)) as doc:
                full_txt = []
                for page in doc:
                    full_txt.append(page.get_text())
                return "".join(full_txt)
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            raise RuntimeError(f"Failed to extract text from {file_path}") from e

    def extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        try:
            with fitz.open(str(file_path)) as doc:
                pdf_meta = doc.metadata or {}
                stat = file_path.stat()

                file_meta = {
                    "filename": file_path.name,
                    "file_size": stat.st_size,
                    "pages": len(doc),
                    "creation_date": pdf_meta.get("creationDate") or stat.st_ctime,
                    "modification_date": pdf_meta.get("modDate") or stat.st_mtime,
                }

                # PDF metadata prioritized over file system metadata
                merged_meta = {**file_meta, **pdf_meta}
                return merged_meta
        except Exception as e:
            logger.error(f"Error extracting metadata from {file_path}: {e}")
            return {}

    def process_document(self, file_path: Path) -> Dict[str, Any]:
        if not self.validate_document(file_path):
            raise ValueError(f"Invalid file document: {file_path}")
        text = self.extract_text(file_path)
        metadata = self.extract_metadata(file_path)
        return {
            "text": text,
            "metadata": metadata,
            "word_count": len(text.split()),
            "char_count": len(text),
        }

    def validate_document(self, file_path: Path) -> bool:
        if not file_path.exists() or file_path.suffix.lower() != ".pdf":
            logger.warning(f"File does not exist or is not a PDF: {file_path}")
            return False

        # Additional check: try opening the file to ensure it's a valid PDF
        try:
            with fitz.open(str(file_path)) as doc:
                return len(doc) > 0  # Must have at least one page
        except Exception as e:
            logger.error(f"Failed to validate PDF file {file_path}: {e}")
            return False

    def get_supported_formats(self):
        return [".pdf"]