from abc import ABC, abstractmethod
from typing import List, Dict, Any

class ChunkerInterface(ABC):
    """Abstract interface for text chunking"""

    @abstractmethod
    def chunk_text(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Split text into chunks with metadata"""
        pass

    @abstractmethod
    def get_chunk_size(self) -> int:
        """Get the target chunk size"""
        pass

    @abstractmethod
    def get_overlap(self) -> int:
        """Get the overlap between chunks"""
        pass

    @abstractmethod
    def validate_chunks(self, chunks: List[Dict[str, Any]]) -> bool:
        """Validate that chunks meet quality criteria"""
        pass