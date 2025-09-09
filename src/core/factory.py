# interfaces
from typing import Optional
import config
from src.generation.rag_generator import RAGGenerator
from src.interfaces import llm_provider_interface
from src.interfaces.document_processing_interface import DocumentProcessorInterface
from src.interfaces.chunking_interface import ChunkingInterface
from src.interfaces.monitor import MonitorInterface
from src.interfaces.embedder import EmbedderInterface
from src.interfaces.vector_store_interface import VectorStoreInterface
from src.interfaces.retriever_interface import RetrieverInterface
from src.interfaces.llm_provider_interface import LLMProviderInterface

## concrete implementations
from src.document_processor.pdf_extractor import PDFExtractor
from src.chunking.legal_chunker import LegalChunker
from src.embedder.sentence_transformer_embedder import SentenceTransformersEmbedder
from src.vector_store.weaviate import WeaviateStore
from src.retrieval.basic_retrieval import BasicRetriever
from src.retrieval.hybrid_retrieval import HybridRetriever
from src.retrieval.rerank_retrieval import RerankRetriever
from src.llm_provider.openrouter_llm import OpenRouterProvider


# Simple no-op monitor to replace MLflow
class NoOpMonitor(MonitorInterface):
    def log_metrics(self, metrics, step=None):
        pass  # Do nothing
    
    def log_artifact(self, path, artifact_path=None):
        pass  # Do nothing

class DocumentProcessorFactory:
    @staticmethod
    def create(processor_type=None) -> DocumentProcessorInterface:
        if processor_type == 'pdf':
            return PDFExtractor()
        else:
            raise Exception(f'The document is not pdf')

class ChunkingFactory:
    @staticmethod
    def create(chunker_type=None) -> ChunkingInterface:
        if chunker_type == 'legal':
            return LegalChunker()
        else:
            raise Exception(f'Chunker not working')

class MonitoringFactory:
    @staticmethod
    def create(monitor_type=None) -> MonitorInterface:
        # Always return NoOpMonitor (no MLflow)
        return NoOpMonitor()

class EmbedderFactory:
    @staticmethod
    def create(embedder_type=None) -> EmbedderInterface:
        if embedder_type == 'sentence-transformers':
            return SentenceTransformersEmbedder()
        else:
            raise Exception(f'Sentence transformers not working')


class VectorStoreFactory:
    """Factory for creating vector stores"""
    @staticmethod
    def create(store_type: str = "weaviate") -> VectorStoreInterface:
        if store_type == "weaviate":
            return WeaviateStore()
        raise ValueError(f"Unsupported vector store type: {store_type}")
    

class RetrieverFactory:
    """Factory for creating retriever instances"""
    
    @staticmethod
    def create(retriever_type: str, vector_store: VectorStoreInterface, 
               embedder: EmbedderInterface, **kwargs) -> RetrieverInterface:
        """Create retriever based on type"""
        
        if retriever_type == "basic":
            return BasicRetriever(vector_store, embedder)
            
        elif retriever_type == "hybrid":
            semantic_weight = kwargs.get('semantic_weight', 0.7)
            keyword_weight = kwargs.get('keyword_weight', 0.3)
            return HybridRetriever(vector_store, embedder, semantic_weight, keyword_weight)
            
        elif retriever_type == "rerank":
            semantic_weight = kwargs.get('semantic_weight', 0.7)
            keyword_weight = kwargs.get('keyword_weight', 0.3)
            rerank_model = kwargs.get('rerank_model', "cross-encoder/ms-marco-MiniLM-L-6-v2")
            rerank_top_k = kwargs.get('rerank_top_k', 50)
            return RerankRetriever(vector_store, embedder, semantic_weight, keyword_weight, 
                                 rerank_model, rerank_top_k)
        else:
            raise ValueError(f"Unknown retriever type: {retriever_type}")
        

class GenerationFactory:
    """Factory for creating generation components"""
    
    @staticmethod
    def create_rag_generator(retriever: RetrieverInterface, 
                           llm_provider: llm_provider_interface) -> RAGGenerator:
        """Create RAG generator with specified retriever and LLM provider"""
        return RAGGenerator(retriever, llm_provider)
    

class LLMProviderFactory:
    """factory for creating LLM instances"""

    @staticmethod
    def create(provider_type: Optional[str] = None) -> LLMProviderInterface:
        if provider_type == 'openrouter':
            return OpenRouterProvider()