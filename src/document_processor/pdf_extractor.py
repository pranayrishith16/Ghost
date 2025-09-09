from pathlib import Path
from typing import Dict, Any
import os
import fitz  # PyMuPDF

from src.interfaces.document_processing_interface import DocumentProcessorInterface

class PDFExtractor(DocumentProcessorInterface):
    def extract_text(self, file_path: Path) -> str:
        doc = fitz.open(str(file_path))
        try:
            full_txt = []
            for page in doc:
                full_txt.append(page.get_text())
            return "".join(full_txt)
        finally:
            doc.close()

    def extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        doc = fitz.open(str(file_path))
        try:
            meta = doc.metadata or {}
            stat = file_path.stat()
            file_metadata = {
                "filename": file_path.name,
                "file_size": stat.st_size,
                "pages": len(doc),
                "creation_date": meta.get("creationDate") or stat.st_ctime,
                "mod_date": meta.get("modDate") or stat.st_mtime,
            }
            # Merge file metadata with PDF intrinsic metadata (file wins on conflicts)
            merged = {**meta, **file_metadata}
            return merged
        finally:
            doc.close()

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
        return file_path.exists() and file_path.suffix.lower() == ".pdf"

    def get_supported_formats(self):
        pass