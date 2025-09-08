from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class RetrievalResult:
    """Structure for retrieval results"""
    def __init__(self, document: Dict[str, Any], score: float, rank: int):
        self.document = document
        self.score = score
        self.rank = rank

class RetrieverInterface(ABC):
    """Abstract interface for document retrieval"""

    @abstractmethod
    def retrieve(self, 
                query: str, 
                k: int = 10, 
                filters: Optional[Dict[str, Any]] = None,
                min_score: Optional[float] = None) -> List[RetrievalResult]:
        """Retrieve relevant documents for a query
        
        Args:
            query: Search query
            k: Number of documents to retrieve
            filters: Optional filters (format depends on implementation)
            min_score: Minimum relevance score threshold
            
        Returns:
            List of RetrievalResult objects with documents, scores, and ranks
            
        Raises:
            RetrievalError: If retrieval fails
            InvalidQueryError: If query is invalid
        """
        pass

    @abstractmethod
    def get_retrieval_stats(self) -> Dict[str, Any]:
        """Get retrieval performance statistics
        
        Returns:
            Dict with stats like 'total_documents', 'avg_retrieval_time', etc.
        """
        pass

    @abstractmethod
    def validate_query(self, query: str) -> bool:
        """Validate if query is suitable for retrieval"""
        pass
    
    @abstractmethod
    def get_supported_filters(self) -> List[str]:
        """Get list of supported filter types"""
        pass
        
    @abstractmethod
    def explain_retrieval(self, query: str, document_id: str) -> Dict[str, Any]:
        """Explain why a document was retrieved for a query"""
        pass
        
    @abstractmethod
    def get_index_info(self) -> Dict[str, Any]:
        """Get information about the underlying index"""
        pass
