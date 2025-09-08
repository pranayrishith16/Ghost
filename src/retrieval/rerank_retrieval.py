import logging
import time
from typing import List, Dict, Any, Optional

from src.retrieval.hybrid_retrieval import HybridRetriever
from src.interfaces.vector_store_interface import VectorStoreInterface
from src.interfaces.embedder import EmbedderInterface

# For cross-encoder reranking - install with: pip install sentence-transformers
try:
    from sentence_transformers import CrossEncoder
    HAS_CROSS_ENCODER = True
except ImportError:
    HAS_CROSS_ENCODER = False
    logging.warning("sentence-transformers not available. Reranking will be skipped.")

class RerankRetriever(HybridRetriever):
    """Advanced retriever with cross-encoder reranking for improved precision"""
    
    def __init__(self, vector_store: VectorStoreInterface, embedder: EmbedderInterface,
                 semantic_weight: float = 0.7, keyword_weight: float = 0.3,
                 rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
                 rerank_top_k: int = 50):
        super().__init__(vector_store, embedder, semantic_weight, keyword_weight)
        
        self.rerank_top_k = rerank_top_k
        self.cross_encoder = None
        
        # Initialize cross-encoder model
        if HAS_CROSS_ENCODER:
            try:
                self.cross_encoder = CrossEncoder(rerank_model)
                self.logger.info(f"Initialized cross-encoder: {rerank_model}")
            except Exception as e:
                self.logger.error(f"Failed to load cross-encoder {rerank_model}: {str(e)}")
                self.cross_encoder = None
        else:
            self.logger.warning("Cross-encoder not available - using hybrid retrieval only")
    
    def retrieve(self, query: str, k: int = 10, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Advanced retrieval with cross-encoder reranking
        
        Args:
            query: Search query text
            k: Number of documents to retrieve
            filters: Optional metadata filters
            
        Returns:
            List of retrieved and reranked documents
        """
        start_time = time.time()
        
        try:
            if not self.validate_query(query):
                raise Exception(f"Invalid query: {query}")
            
            # First stage: Get more candidates for reranking
            initial_k = min(self.rerank_top_k, k * 5)  # Get 5x more for reranking
            
            # Get hybrid results
            initial_results = super().retrieve(query, initial_k, filters)
            
            if not initial_results:
                return []
            
            # Second stage: Rerank with cross-encoder
            if self.cross_encoder and len(initial_results) > k:
                reranked_results = self._rerank_results(query, initial_results)
            else:
                self.logger.info("Skipping reranking - cross-encoder not available or insufficient results")
                reranked_results = initial_results
                for result in reranked_results:
                    result['retrieval_method'] = 'hybrid_only'
            
            # Take top k results
            final_results = reranked_results[:k]
            
            # Update final rankings
            for i, result in enumerate(final_results):
                result['rank'] = i + 1
            
            # Update statistics
            retrieval_time = time.time() - start_time
            self._update_stats(retrieval_time, len(final_results))
            
            self.logger.info(f"Rerank retrieval found {len(final_results)} documents in {retrieval_time:.3f}s")
            
            return final_results
            
        except Exception as e:
            self.logger.error(f"Rerank retrieval failed for query '{query[:50]}...': {str(e)}")
            raise Exception(f"Rerank retrieval failed: {str(e)}")
    
    def _rerank_results(self, query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rerank results using cross-encoder"""
        if not self.cross_encoder:
            return results
        
        self.logger.info(f"Reranking {len(results)} results with cross-encoder")
        
        try:
            # Prepare query-document pairs for cross-encoder
            pairs = []
            for result in results:
                text = result.get('text', '')
                # Truncate text if too long for cross-encoder
                if len(text) > 512:
                    text = text[:512]
                pairs.append([query, text])
            
            # Get cross-encoder scores
            cross_scores = self.cross_encoder.predict(pairs)
            
            # Add cross-encoder scores to results
            for result, score in zip(results, cross_scores):
                result['cross_encoder_score'] = float(score)
                
                # Combine with existing scores
                hybrid_score = result.get('hybrid_score', 0.0)
                # Weight: 60% cross-encoder, 40% hybrid
                result['final_score'] = 0.6 * score + 0.4 * hybrid_score
                result['retrieval_method'] = 'hybrid_with_reranking'
            
            # Sort by final score
            results.sort(key=lambda x: x.get('final_score', 0), reverse=True)
            
            # Add legal-specific reranking
            results = self._apply_legal_reranking(query, results)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Reranking failed: {str(e)}")
            # Return original results if reranking fails
            return results
    
    def _apply_legal_reranking(self, query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply legal domain-specific reranking adjustments"""
        
        query_lower = query.lower()
        legal_query_types = {
            'precedent': ['precedent', 'case law', 'similar case', 'ruling'],
            'statute': ['statute', 'law', 'code', 'section'],
            'procedure': ['motion', 'procedure', 'rules', 'process'],
            'analysis': ['analysis', 'reasoning', 'holding', 'rationale']
        }
        
        # Determine query type
        query_type = None
        for qtype, keywords in legal_query_types.items():
            if any(keyword in query_lower for keyword in keywords):
                query_type = qtype
                break
        
        if not query_type:
            return results
        
        self.logger.info(f"Applying legal reranking for query type: {query_type}")
        
        # Apply type-specific boosts
        for result in results:
            metadata = result.get('metadata', {})
            text = result.get('text', '').lower()
            
            legal_boost = 0.0
            
            if query_type == 'precedent':
                # Boost court opinions and cases with citations
                if metadata.get('document_type') == 'opinion':
                    legal_boost += 0.1
                if metadata.get('citations'):
                    legal_boost += 0.05
                if 'holding' in text or 'precedent' in text:
                    legal_boost += 0.05
                    
            elif query_type == 'statute':
                # Boost statutory references
                if 'section' in text or '§' in text:
                    legal_boost += 0.1
                if metadata.get('document_type') == 'statute':
                    legal_boost += 0.15
                    
            elif query_type == 'procedure':
                # Boost procedural documents
                if metadata.get('document_type') in ['motion', 'order']:
                    legal_boost += 0.1
                if any(word in text for word in ['procedure', 'rule', 'motion']):
                    legal_boost += 0.05
                    
            elif query_type == 'analysis':
                # Boost analytical content
                if any(word in text for word in ['analysis', 'reasoning', 'conclusion']):
                    legal_boost += 0.1
                if metadata.get('document_type') == 'opinion':
                    legal_boost += 0.05
            
            # Apply boost
            final_score = result.get('final_score', 0)
            result['final_score'] = min(final_score + legal_boost, 1.0)
            result['legal_rerank_boost'] = legal_boost
        
        # Re-sort after legal adjustments
        results.sort(key=lambda x: x.get('final_score', 0), reverse=True)
        
        return results
    
    def get_retrieval_stats(self) -> Dict[str, Any]:
        """Get comprehensive retrieval statistics"""
        base_stats = super().get_retrieval_stats()
        
        base_stats.update({
            'reranking_enabled': self.cross_encoder is not None,
            'rerank_model': str(self.cross_encoder) if self.cross_encoder else None,
            'rerank_top_k': self.rerank_top_k
        })
        
        return base_stats
