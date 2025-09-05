# import logging
# from typing import Optional

# from src.interfaces.document_processor import DocumentProcessorInterface
# from src.interfaces.chunker import ChunkerInterface
# from src.interfaces.embedder import EmbedderInterface
# from src.interfaces.vector_store import VectorStoreInterface
# from src.interfaces.llm_provider import LLMProviderInterface
# from src.interfaces.monitor import MonitorInterface
# from src.config.settings import get_config
# from src.core.exceptions import ConfigurationError

# # Import concrete implementations
# from src.document_processing.pdf_extractor import PDFExtractor
# from src.chunking.semantic_chunker import SemanticChunker
# from src.chunking.fixed_size_chunker import FixedSizeChunker
# from src.chunking.legal_chunker import LegalChunker
# from src.embeddings.openai_embedder import OpenAIEmbedder
# from src.embeddings.huggingface_embedder import HuggingFaceEmbedder
# from src.embeddings.sentence_transformer_embedder import SentenceTransformerEmbedder
# from src.vector_stores.chroma_store import ChromaStore
# from src.vector_stores.pinecone_store import PineconeStore
# from src.llm_providers.openai_provider import OpenAIProvider
# from src.llm_providers.anthropic_provider import AnthropicProvider
# from src.llm_providers.huggingface_provider import HuggingFaceProvider
# from src.llm_providers.local_provider import LocalProvider
# from src.monitoring.mlflow_monitor import MLflowMonitor
# from src.monitoring.zenml_monitor import ZenMLMonitor

# class DocumentProcessorFactory:
#     """Factory for creating document processor instances"""
    
#     @staticmethod
#     def create(processor_type: Optional[str] = None) -> DocumentProcessorInterface:
#         config = get_config()
#         processor_type = processor_type or config.processing.default_processor
        
#         if processor_type == "pdf":
#             return PDFExtractor()
#         # Add more document processor types as needed
#         else:
#             raise ConfigurationError(f"Unknown document processor type: {processor_type}")

# class ChunkerFactory:
#     """Factory for creating chunker instances"""
    
#     @staticmethod
#     def create(chunker_type: Optional[str] = None) -> ChunkerInterface:
#         config = get_config()
#         chunker_type = chunker_type or config.chunking.strategy
        
#         if chunker_type == "semantic":
#             return SemanticChunker()
#         elif chunker_type == "fixed_size":
#             return FixedSizeChunker()
#         elif chunker_type == "legal":
#             return LegalChunker()
#         else:
#             raise ConfigurationError(f"Unknown chunker type: {chunker_type}")

# class EmbedderFactory:
#     """Factory for creating embedder instances"""
    
#     @staticmethod
#     def create(embedder_type: Optional[str] = None) -> EmbedderInterface:
#         config = get_config()
#         embedder_type = embedder_type or config.embedding.provider
        
#         if embedder_type == "openai":
#             return OpenAIEmbedder()
#         elif embedder_type == "huggingface":
#             return HuggingFaceEmbedder()
#         elif embedder_type == "sentence_transformers":
#             return SentenceTransformerEmbedder()
#         else:
#             raise ConfigurationError(f"Unknown embedder type: {embedder_type}")

# class VectorStoreFactory:
#     """Factory for creating vector store instances"""
    
#     @staticmethod
#     def create(store_type: Optional[str] = None) -> VectorStoreInterface:
#         config = get_config()
#         store_type = store_type or config.database.type
        
#         if store_type == "chroma":
#             return ChromaStore()
#         elif store_type == "pinecone":
#             return PineconeStore()
#         # Add more vector store types as needed
#         else:
#             raise ConfigurationError(f"Unknown vector store type: {store_type}")

# class LLMProviderFactory:
#     """Factory for creating LLM provider instances"""
    
#     @staticmethod
#     def create(provider_type: Optional[str] = None) -> LLMProviderInterface:
#         config = get_config()
#         provider_type = provider_type or config.llm.provider
        
#         if provider_type == "openai":
#             return OpenAIProvider()
#         elif provider_type == "anthropic":
#             return AnthropicProvider()
#         elif provider_type == "huggingface":
#             return HuggingFaceProvider()
#         elif provider_type == "local":
#             return LocalProvider()
#         else:
#             raise ConfigurationError(f"Unknown LLM provider type: {provider_type}")

# class MonitorFactory:
#     """Factory for creating monitor instances"""
    
#     @staticmethod
#     def create(monitor_type: Optional[str] = None) -> MonitorInterface:
#         config = get_config()
#         monitor_type = monitor_type or config.monitoring.type
        
#         if monitor_type == "mlflow":
#             return MLflowMonitor()
#         elif monitor_type == "zenml":
#             return ZenMLMonitor()
#         # Add more monitor types as needed
#         else:
#             raise ConfigurationError(f"Unknown monitor type: {monitor_type}")