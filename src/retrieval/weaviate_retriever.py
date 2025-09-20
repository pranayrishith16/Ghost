import time
from typing import List, Dict, Any, Optional
from loguru import logger

from src.interfaces.retriever_interface import RetrieverInterface
from src.interfaces.vector_store_interface import VectorStoreInterface
from src.interfaces.embedder import EmbedderInterface
from config.settings import get_config

class WeaviateBuiltinRetriever(RetrieverInterface):
    """Retriever using Weaviate's built-in v4 query methods"""

    def __init__(self, vector_store: VectorStoreInterface, embedder: EmbedderInterface = None):
        self.config = get_config()
        self.vector_store = vector_store
        self.embedder = embedder
        self.logger = logger
        
        # Retrieval statistics
        self.stats = {
            'total_queries': 0,
            'avg_retrieval_time': 0.0,
            'total_documents_retrieved': 0,
            'method_usage': {
                'near_text': 0,
                'near_vector': 0,
                'hybrid': 0,
                'bm25': 0
            }
        }

    def retrieve(self, query: str, k: int = 10, filters: Dict[str, Any] = None, method: str = "near_vector") -> List[Dict[str, Any]]:
        """
        Retrieve documents using Weaviate's built-in methods
        
        Args:
            query: Search query text
            k: Number of documents to retrieve
            filters: Optional metadata filters
            method: Retrieval method ('near_text', 'near_vector', 'hybrid', 'bm25')
            
        Returns:
            List of retrieved documents with metadata and scores
        """
        start_time = time.time()
        
        try:
            if not self.validate_query(query):
                raise Exception(f"Invalid query: {query}")

            self.logger.info(f"Using {method} retrieval for query: {query[:100]}...")
            
            # Route to appropriate Weaviate built-in method
            if method == "near_text":
                results = self.vector_store.near_text_search(query, k, filters)
            elif method == "near_vector":
                if not self.embedder:
                    raise ValueError("Embedder required for near_vector method")
                query_embedding = self.embedder.embed_text(query)
                results = self.vector_store.near_vector_search(query_embedding[0], k, filters)
            elif method == "hybrid":
                alpha = filters.pop("alpha", 0.5) if filters else 0.5
                results = self.vector_store.hybrid_search(query, k, alpha, filters)
            elif method == "bm25":
                results = self.vector_store.bm25_search(query, k, filters)
            else:
                raise ValueError(f"Unknown retrieval method: {method}")

            # Update statistics
            retrieval_time = time.time() - start_time
            self._update_stats(retrieval_time, len(results), method)
            
            self.logger.info(f"Retrieved {len(results)} documents in {retrieval_time:.3f}s using {method}")
            return results

        except Exception as e:
            self.logger.error(f"Retrieval failed for query '{query[:50]}...': {str(e)}")
            raise

    def retrieve_near_text(self, query: str, k: int = 10, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Vector similarity search using automatic text embedding"""
        return self.retrieve(query, k, filters, "near_text")

    def retrieve_hybrid(self, query: str, k: int = 10, alpha: float = 0.5, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Hybrid search combining vector similarity and BM25"""
        if filters is None:
            filters = {}
        filters["alpha"] = alpha
        return self.retrieve(query, k, filters, "hybrid")

    def retrieve_bm25(self, query: str, k: int = 10, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """BM25 keyword search"""
        return self.retrieve(query, k, filters, "bm25")

    def _update_stats(self, retrieval_time: float, num_results: int, method: str):
        """Update retrieval statistics"""
        self.stats['total_queries'] += 1
        self.stats['total_documents_retrieved'] += num_results
        self.stats['method_usage'][method] = self.stats['method_usage'].get(method, 0) + 1
        
        # Update average retrieval time
        total_time = self.stats['avg_retrieval_time'] * (self.stats['total_queries'] - 1)
        self.stats['avg_retrieval_time'] = (total_time + retrieval_time) / self.stats['total_queries']

    def get_retrieval_stats(self) -> Dict[str, Any]:
        """Get retrieval performance statistics"""
        return {
            **self.stats,
            'vector_store_stats': self.vector_store.get_stats(),
            'embedder_model': self.embedder.get_model_name() if self.embedder else None,
        }

    def validate_query(self, query: str) -> bool:
        """Validate if query is suitable for retrieval"""
        if not query or not query.strip():
            return False
        if len(query.strip()) < 3:
            self.logger.warning("Query too short for effective retrieval")
            return False
        if len(query) > 1000:
            self.logger.warning("Query too long, may be truncated")
        return True

    def explain_retrieval(self, query, document_id):
        """Explain retrieval results (placeholder for future implementation)"""
        return {"message": "Explanation not implemented for built-in retriever"}

    def get_index_info(self):
        """Get index information"""
        return self.vector_store.get_stats()

    def get_supported_filters(self):
        """Get supported filter types"""
        return {
            "metadata_filters": ["source_file", "document_type", "court", "case_number"],
            "numeric_filters": ["word_count_min", "word_count_max"],
            "retrieval_params": ["alpha"]  # for hybrid search
        }
