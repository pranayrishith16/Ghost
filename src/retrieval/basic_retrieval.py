import time
from typing import List, Dict, Any

from loguru import logger

from src.interfaces.retriever_interface import RetrieverInterface
from src.interfaces.vector_store_interface import VectorStoreInterface
from src.interfaces.embedder import EmbedderInterface
from config.settings import get_config

LEGAL_KEYWORDS = {
    "jurisdiction": ["jurisdiction", "court", "province", "state", "territory"],
    "islegaldoc": ["legal", "law", "case", "judgment"],
    "citation": ["citation", "cite"],
}


class InvalidQueryException(Exception):
    pass


class BasicRetriever(RetrieverInterface):
    """Simple similarity search retriever using vector embeddings"""
    
    def __init__(self, vector_store: VectorStoreInterface, embedder: EmbedderInterface):
        self.config = get_config()
        self.vector_store = vector_store
        self.embedder = embedder
        self.logger = logger
        
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

        if k <= 0:
            raise ValueError("Parameter k must be positive")
        if filters is not None and not isinstance(filters, dict):
            raise ValueError("Filters must be a dictionary if provided")
        
        try:
            if len(query)>1000:
                self.logger.warning("Query too long, truncating to 1000 characters")
                query = query[:1000]

            if not self.validate_query(query):
                raise InvalidQueryException(f"Invalid query: {query}")
            
            # Generate query embedding
            self.logger.debug(f"Generating embedding for query: {query[:100]}...")
            query_embedding = self.embedder.embed_text(query)
            
            # Search vector store
            self.logger.info(f"Searching vector store for top {k} results")
            results = self.vector_store.search(
                query=query_embedding,
                limit=k,
                filters=filters
            )
            
            # Process and enrich results
            processed_results = self._process_results(results, query)
            
            # Update statistics
            retrieval_time = time.time() - start_time
            self._update_stats(retrieval_time, len(processed_results))
            
            self.logger.info(f"Retrieved {len(processed_results)} documents in {retrieval_time:.3f}s")
            
            return processed_results
            
        except InvalidQueryException as e:
            self.logger.error(f"Invalid Query: {str(e)}")
            raise

        except Exception as e:
            self.logger.error(f"Retrieval failed for query '{query[:50]}...': {str(e)}")
    
    def _process_results(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        processed = []
        for i, result in enumerate(results):
            distance = result.get('distance', None)
            if distance is None:
                similarity_score = 0.0
            else:
                # Convert distance to similarity for ranking purposes (assuming cosine distance)
                similarity_score = max(0.0, 1.0 - distance)
        
            processed_result = {
                'rank': i + 1,
                'text': result.get('text', ''),
                'metadata': result.get('metadata', {}),
                'similarity_score': similarity_score,
                'chunk_id': result.get('id', ''),
                'retrieval_method': 'basic_similarity',
                'query': query
            }
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
    
    def _update_stats(self, retrievaltime: float, numdocuments: int) -> None:
        self.stats['total_queries'] += 1
        totalqueries = self.stats['total_queries']
        self.stats['avg_retrieval_time'] = (
            (self.stats['avg_retrieval_time'] * (totalqueries - 1) + retrievaltime) / totalqueries
        )
        self.stats['total_documents_retrieved'] += numdocuments


    
    def get_retrieval_stats(self) -> Dict[str, Any]:
        """Get retrieval performance statistics"""
        return {
            **self.stats,
            'embedder_model': self.embedder.get_model_name(),
            'vector_store_stats': self.vector_store.get_stats()
        }
    
    def validate_query(self, query: str) -> bool:
        if not query or not query.strip():
            return False
        if len(query.strip()) < 3:
            self.logger.warning("Query too short for effective retrieval")
            return False
        return True