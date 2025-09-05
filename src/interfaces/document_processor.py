from abc import ABC, abstractmethod
from typing import Dict, Any, List
from pathlib import Path

class DocumentProcessorInterface(ABC):
    """Abstract interface for document processing"""
    
    @abstractmethod
    def extract_text(self, file_path: Path) -> str:
        """Extract text from document"""
        pass

    @abstractmethod
    def extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from document"""
        pass

    @abstractmethod
    def process_document(self, file_path: Path) -> Dict[str, Any]:
        """Process document and return text + metadata"""
        pass

    @abstractmethod
    def validate_document(self, file_path: Path) -> bool:
        """Check if document is valid and processable"""
        pass