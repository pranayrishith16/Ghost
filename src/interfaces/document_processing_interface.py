from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List
from enum import Enum

class DocumentFormat(Enum):
    PDF='pdf'
    DOCX='docx'
    TXT='txt'


class DocumentProcessorInterface(ABC):
    @abstractmethod
    def process_document(self, file_path: Path) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def validate_document(self, file_path: Path) -> bool:
        raise NotImplementedError

    @abstractmethod
    def extract_text(self, file_path: Path) -> str:
        raise NotImplementedError

    @abstractmethod
    def extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        raise NotImplementedError
    
    @abstractmethod
    def get_supported_formats(self) -> List[DocumentFormat]:
        """Get list of supported document formats"""
        raise NotImplementedError