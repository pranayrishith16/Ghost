from abc import ABC, abstractmethod
from typing import List, Dict, Any
import numpy as np

class EmbedderInterface(ABC):
    """Abstract interface for embedding generation"""

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for single text"""
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for batch of texts"""
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        """Get embedding dimension"""
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Get model name/identifier"""
        pass

    @abstractmethod
    def similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate similarity between embeddings"""
        pass