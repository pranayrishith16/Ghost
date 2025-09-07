from abc import ABC, abstractmethod
from typing import List, Dict, Any
from pathlib import Path


class DocumentProcessorInterface(ABC):
    """Abstract interface for document processing"""

    @abstractmethod
    def extract_text(self,file_path:Path):
        """Extract text from document"""
        pass
    
    @abstractmethod
    def extract_metadata(self,file_path:Path):
        """Extract metadata from document"""
        pass

    @abstractmethod
    def process_document(self,file_path:Path):
        """Process document and return text + metadata"""
        pass

    @abstractmethod
    def validate_document(self,file_path:Path):
        """Valid if document id valid and processable"""
        pass