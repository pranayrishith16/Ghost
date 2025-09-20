import loguru
import time
from typing import List, Dict, Any, Optional
import math

from sympy import limit

from src.retrieval.basic_retrieval import BasicRetriever
from src.interfaces.vector_store_interface import VectorStoreInterface
from src.interfaces.embedder import EmbedderInterface

# For BM25 keyword search - install with: pip install rank-bm25
try:
    from rank_bm25 import BM25Okapi
    HAS_BM25 = True
except ImportError:
    HAS_BM25 = False
    loguru.logger.warning("rank-bm25 not available. Hybrid retrieval will use basic similarity only.")

class HybridRetriever(BasicRetriever):
    """Hybrid retriever combining semantic similarity with keyword search (BM25)"""
    
    def __init__(self, vector_store: VectorStoreInterface, embedder: EmbedderInterface, 
                 semantic_weight: float = 0.7, keyword_weight: float = 0.3):
        super().__init__(vector_store, embedder)
        self.semantic_weight = semantic_weight
        self.keyword_weight = keyword_weight
        
        # Initialize BM25 corpus if available
        self.bm25 = None
        self.corpus_texts = []
        self.corpus_metadata = []
        
        if HAS_BM25:
            self._initialize_bm25_corpus()
        else:
            self.logger.warning("BM25 not available - using semantic search only")
    
    def _initialize_bm25_corpus(self):
        """Initialize BM25 corpus from vector store"""
        try:
            # Get all documents from vector store for BM25 indexing
            # This is a simplified approach - in production, you'd want a more efficient method
            all_docs = self.vector_store.get_all_documents()  # Implement this method
            
            self.corpus_texts = []
            self.corpus_metadata = []
            
            for doc in all_docs:
                self.corpus_texts.append(doc.get('text', ''))
                self.corpus_metadata.append(doc.get('metadata', {}))
            
            # Tokenize corpus for BM25
            tokenized_corpus = [text.split() for text in self.corpus_texts]
            self.bm25 = BM25Okapi(tokenized_corpus)
            
            self.logger.info(f"Initialized BM25 with {len(self.corpus_texts)} documents")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize BM25 corpus: {str(e)}",exc_info=True)
            self.bm25 = None
    
    def retrieve(self, query: str, k: int = 10, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Hybrid retrieval combining semantic and keyword search
        
        Args:
            query: Search query text
            k: Number of documents to retrieve  
            filters: Optional metadata filters
            
        Returns:
            List of retrieved documents with hybrid scores
        """
        start_time = time.time()
        
        try:
            if not self.validate_query(query):
                raise Exception(f"Invalid query: {query}")
            
            # Get semantic results
            semantic_results = self._get_semantic_results(query, k * 2, filters)  # Get more for fusion
            
            # Get keyword results if BM25 is available
            if self.bm25 and HAS_BM25:
                keyword_results = self._get_keyword_results(query, k * 2)
                # Combine results using hybrid scoring
                hybrid_results = self._combine_results(semantic_results, keyword_results, query)
            else:
                # Fall back to semantic only
                self.logger.warning("Using semantic search only - BM25 not available")
                hybrid_results = semantic_results
                for result in hybrid_results:
                    result['retrieval_method'] = 'semantic_only'
            
            # Sort by hybrid score and take top k
            hybrid_results.sort(key=lambda x: x.get('hybrid_score', x.get('similarity_score', 0)), reverse=True)
            final_results = hybrid_results[:k]
            
            # Update rankings
            for i, result in enumerate(final_results):
                result['rank'] = i + 1
            
            # Update statistics
            retrieval_time = time.time() - start_time
            self._update_stats(retrieval_time, len(final_results))
            
            self.logger.info(f"Hybrid retrieval found {len(final_results)} documents in {retrieval_time:.3f}s")
            
            return final_results
            
        except Exception as e:
            self.logger.error(f"Hybrid retrieval failed for query '{query[:50]}...': {str(e)}")
            raise Exception(f"Hybrid retrieval failed: {str(e)}")
    
    def _get_semantic_results(self, query: str, k: int, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get semantic similarity results"""
        query_embedding = self.embedder.embed_text(query)
        results = self.vector_store.search(
            query=query_embedding[0],
            limit=k,
            filters=filters
        )
        
        processed_results = []
        for i, result in enumerate(results):
            distance = result.get('distance', None)
            if distance is None:
                similarity_score = 0.0
            else:
                # Convert distance to similarity for ranking purposes (assuming cosine distance)
                similarity_score = max(0.0, 1.0 - distance)

            processed = {
                'text': result.get('text', ''),
                'metadata': result.get('metadata', {}),
                'similarity_score': similarity_score,
                'chunk_id': result.get('id', ''),
                'query': query,
                'retrieval_method': 'hybrid'
            }
            processed_results.append(processed)
            
        return processed_results
    
    def _get_keyword_results(self, query: str, k: int) -> List[Dict[str, Any]]:
        """Get BM25 keyword search results"""
        if not self.bm25:
            return []
            
        query_tokens = query.split()
        bm25_scores = self.bm25.get_scores(query_tokens)
        
        # Get top k results
        scored_docs = [(i, score) for i, score in enumerate(bm25_scores)]
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        keyword_results = []
        for i, (doc_idx, score) in enumerate(scored_docs[:k]):
            if doc_idx < len(self.corpus_texts):
                result = {
                    'text': self.corpus_texts[doc_idx],
                    'metadata': self.corpus_metadata[doc_idx],
                    'bm25_score': score,
                    'chunk_id': f"doc_{doc_idx}",  # Simplified ID
                    'query': query,
                    'retrieval_method': 'hybrid'
                }
                keyword_results.append(result)
        
        return keyword_results
    
    def _combine_results(self, semantic_results: List[Dict[str, Any]], 
                        keyword_results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Combine semantic and keyword results using weighted scoring"""
        
        # Create lookup for semantic scores
        semantic_lookup = {result['chunk_id']: result for result in semantic_results}
        keyword_lookup = {result['chunk_id']: result for result in keyword_results}
        
        # Normalize scores
        semantic_scores = [r['similarity_score'] for r in semantic_results]
        keyword_scores = [r['bm25_score'] for r in keyword_results]
        
        max_semantic = max(semantic_scores) if semantic_scores else 1.0
        max_keyword = max(keyword_scores) if keyword_scores else 1.0
        
        # Combine results
        all_chunk_ids = set(semantic_lookup.keys()) | set(keyword_lookup.keys())
        combined_results = []
        
        for chunk_id in all_chunk_ids:
            semantic_result = semantic_lookup.get(chunk_id)
            keyword_result = keyword_lookup.get(chunk_id)
            
            # Calculate normalized scores
            semantic_score_norm = (semantic_result['similarity_score'] / max_semantic) if semantic_result else 0.0
            keyword_score_norm = (keyword_result['bm25_score'] / max_keyword) if keyword_result else 0.0
            
            # Calculate hybrid score
            hybrid_score = (self.semantic_weight * semantic_score_norm + 
                          self.keyword_weight * keyword_score_norm)
            
            # Use semantic result as base, add keyword info
            if semantic_result:
                result = semantic_result.copy()
                result['bm25_score'] = keyword_score_norm if keyword_result else 0.0
            else:
                result = keyword_result.copy()
                result['similarity_score'] = 0.0
            
            result['hybrid_score'] = hybrid_score
            result['semantic_score_norm'] = semantic_score_norm
            result['keyword_score_norm'] = keyword_score_norm
            
            # Add legal-specific processing
            result = self._add_legal_context(result)
            result = self._add_hybrid_legal_signals(result, query)
            
            combined_results.append(result)
        
        return combined_results
    
    def _add_hybrid_legal_signals(self, result: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Add legal-specific signals for hybrid ranking"""
        text = result.get('text', '').lower()
        query_lower = query.lower()
        metadata = result.get('metadata', {})
        
        # Legal document type matching
        legal_type_boost = 0.0
        if 'case law' in query_lower and metadata.get('document_type') == 'opinion':
            legal_type_boost += 0.1
        elif 'statute' in query_lower and 'statute' in text:
            legal_type_boost += 0.1
        elif 'regulation' in query_lower and 'regulation' in text:
            legal_type_boost += 0.1
        
        # Citation authority boost
        citation_boost = 0.0
        if metadata.get('citations'):
            citation_count = len(metadata['citations'])
            citation_boost = min(citation_count * 0.02, 0.1)  # Max 0.1 boost
        
        # Jurisdiction matching
        jurisdiction_boost = 0.0
        if metadata.get('court'):
            court = metadata['court'].lower()
            if any(jur in query_lower for jur in ['federal', 'supreme', 'circuit']):
                if any(jur in court for jur in ['federal', 'supreme', 'circuit']):
                    jurisdiction_boost = 0.05
        
        # Apply boosts to hybrid score
        total_boost = legal_type_boost + citation_boost + jurisdiction_boost
        result['hybrid_score'] = min(result.get('hybrid_score', 0) + total_boost, 1.0)
        
        # Store boost information
        result['legal_boosts'] = {
            'legal_type_boost': legal_type_boost,
            'citation_boost': citation_boost,
            'jurisdiction_boost': jurisdiction_boost,
            'total_boost': total_boost
        }
        
        return result
