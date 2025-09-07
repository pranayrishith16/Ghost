from abc import ABC, abstractmethod
from typing import List, Dict, Any
from pathlib import Path

class ChunkingInterface(ABC):
    """Abstract interface for text chunking"""

    @abstractmethod
    def chunk_text(self,text,metadata=None):
        """Split text into chunks with metadata"""
        pass

    @abstractmethod
    def get_chunk_size(self,text,metadata) -> int:
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