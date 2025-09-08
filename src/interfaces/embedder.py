from abc import ABC, abstractmethod
from typing import List, Optional

class EmbedderInterface(ABC):
    """Abstract interface for embedding generation"""

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for single text"""
        raise NotImplementedError

    @abstractmethod
    def embed_batch(self, texts: List[str],batch_size:Optional[int] = None) -> List[List[float]]:
        """Generate embeddings for batch of texts"""
        raise NotImplementedError

    @abstractmethod
    def get_dimension(self) -> int:
        """Get embedding dimension"""
        raise NotImplementedError

    @abstractmethod
    def get_model_name(self) -> str:
        """Get model name/identifier"""
        raise NotImplementedError

    @abstractmethod
    def similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate similarity between embeddings"""
        raise NotImplementedError
