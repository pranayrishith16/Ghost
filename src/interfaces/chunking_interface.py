from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class ChunkingInterface(ABC):
    """Abstract interface for text chunking"""

    @abstractmethod
    def chunk_text(self, text: str, meta:Optional[Dict[str,Any]] = None) -> List:
        """Split text into chunks with metadata"""
        raise NotImplementedError

    @abstractmethod
    def get_chunk_size(self, text: str, meta:Optional[Dict[str,Any]] = None) -> int:
        """Get the target chunk size"""
        raise NotImplementedError

    @abstractmethod
    def get_overlap(self) -> int:
        """Get the overlap between chunks"""
        raise NotImplementedError

    @abstractmethod
    def validate_chunks(self, chunks: List[Dict[str, Any]]) -> bool:
        """Validate that chunks meet quality criteria"""
        raise NotImplementedError
