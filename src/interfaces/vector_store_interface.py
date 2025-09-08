from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple

class VectorStoreInterface(ABC):
    """Abstract interface for vector database operations"""

    @abstractmethod
    def create_collection(self, name: str, dimension: int, metadata_schema: Dict[str, Any] = None):
        """Create a new collection/index"""
        pass

    @abstractmethod
    def insert(self, vectors: List[List[float]], metadata: List[Dict[str, Any]], ids: List[str]):
        """Insert vectors with metadata"""
        pass

    @abstractmethod
    def search(self, query_vector: List[float], k: int = 10, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search for similar vectors"""
        pass

    @abstractmethod
    def delete(self, ids: List[str]) -> bool:
        """Delete vectors by IDs"""
        pass

    @abstractmethod
    def update(self, ids: List[str], vectors: List[List[float]], metadata: List[Dict[str, Any]]):
        """Update existing vectors"""
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        pass