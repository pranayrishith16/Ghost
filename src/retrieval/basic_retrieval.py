import logging
import time
from typing import List, Dict, Any, Optional

from src.interfaces.retriever_interface import RetrieverInterface
from src.interfaces.vector_store_interface import VectorStoreInterface
from src.interfaces.embedder import EmbedderInterface
from config.settings import get_config

class BasicRetriever(RetrieverInterface):
    """Simple similarity search retriever using vector embeddings"""
    
    def __init__(self, vector_store: VectorStoreInterface, embedder: EmbedderInterface):
        self.config = get_config()
        self.vector_store = vector_store
        self.embedder = embedder
        self.logger = logging.getLogger(__name__)
        
        # Retrieval statistics
        self.stats = {
            'total_queries': 0,
            'avg_retrieval_time': 0.0,
            'total_documents_retrieved': 0
        }
        
    def retrieve(self, query: str, k: int = 10, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Retrieve documents using simple similarity search
        
        Args:
            query: Search query text
            k: Number of documents to retrieve
            filters: Optional metadata filters
            
        Returns:
            List of retrieved documents with metadata and scores
        """
        start_time = time.time()
        
        try:
            if not self.validate_query(query):
                raise Exception(f"Invalid query: {query}")
            
            # Generate query embedding
            self.logger.info(f"Generating embedding for query: {query[:100]}...")
            query_embedding = self.embedder.embed_text(query)
            
            # Search vector store
            self.logger.info(f"Searching vector store for top {k} results")
            results = self.vector_store.search(
                query_vector=query_embedding,
                k=k,
                filters=filters
            )
            
            # Process and enrich results
            processed_results = self._process_results(results, query)
            
            # Update statistics
            retrieval_time = time.time() - start_time
            self._update_stats(retrieval_time, len(processed_results))
            
            self.logger.info(f"Retrieved {len(processed_results)} documents in {retrieval_time:.3f}s")
            
            return processed_results
            
        except Exception as e:
            self.logger.error(f"Retrieval failed for query '{query[:50]}...': {str(e)}")
    
    def _process_results(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Process and enrich search results"""
        processed = []
        
        for i, result in enumerate(results):
            processed_result = {
                'rank': i + 1,
                'text': result.get('text', ''),
                'metadata': result.get('metadata', {}),
                'similarity_score': result.get('score', 0.0),
                'chunk_id': result.get('id', ''),
                'retrieval_method': 'basic_similarity',
                'query': query
            }
            
            # Add legal-specific processing
            processed_result = self._add_legal_context(processed_result)
            processed.append(processed_result)
            
        return processed
    
    def _add_legal_context(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Add legal document context to results"""
        metadata = result.get('metadata', {})
        
        # Extract legal document information
        result['legal_context'] = {
            'document_type': metadata.get('document_type', 'unknown'),
            'court': metadata.get('court', 'unknown'),
            'case_number': metadata.get('case_number', 'unknown'),
            'legal_areas': metadata.get('legal_areas', []),
            'citation_count': len(metadata.get('citations', [])),
            'parties': {
                'plaintiff': metadata.get('plaintiff', 'unknown'),
                'defendant': metadata.get('defendant', 'unknown')
            }
        }
        
        # Add relevance indicators for legal documents
        text = result.get('text', '').lower()
        result['legal_indicators'] = {
            'has_citations': bool(metadata.get('citations')),
            'has_case_law': 'precedent' in text or 'holding' in text,
            'has_statute_ref': 'section' in text or '§' in text,
            'procedural_content': any(word in text for word in ['motion', 'order', 'ruling']),
            'substantive_content': any(word in text for word in ['analysis', 'reasoning', 'conclusion'])
        }
        
        return result
    
    def _update_stats(self, retrieval_time: float, num_results: int):
        """Update retrieval statistics"""
        self.stats['total_queries'] += 1
        self.stats['total_documents_retrieved'] += num_results
        
        # Update average retrieval time
        total_time = self.stats['avg_retrieval_time'] * (self.stats['total_queries'] - 1)
        self.stats['avg_retrieval_time'] = (total_time + retrieval_time) / self.stats['total_queries']
    
    def get_retrieval_stats(self) -> Dict[str, Any]:
        """Get retrieval performance statistics"""
        return {
            **self.stats,
            'embedder_model': self.embedder.get_model_name(),
            'vector_store_stats': self.vector_store.get_stats()
        }
    
    def validate_query(self, query: str) -> bool:
        """Validate if query is suitable for retrieval"""
        if not query or not query.strip():
            return False
            
        if len(query.strip()) < 3:
            self.logger.warning("Query too short for effective retrieval")
            return False
            
        if len(query) > 1000:
            self.logger.warning("Query too long, truncating")
            return True
            
        return True
