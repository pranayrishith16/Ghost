import yaml
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path

# @dataclass
# class DatabaseConfig:
    # """Vector database configuration"""
    # type: str  # "chroma", "pinecone", "weaviate", "qdrant"
    # host: str = "localhost"
    # port: int = 8000
    # collection_name: str = "law_cases"
    # api_key: Optional[str] = None
    # index_name: Optional[str] = None
    # environment: Optional[str] = None  # For Pinecone
    
    # # Advanced settings
    # distance_metric: str = "cosine"
    # ef_construction: int = 200  # HNSW parameter
    # m: int = 16  # HNSW parameter
    
    # def get_connection_string(self) -> str:
    #     """Generate connection string based on database type"""
    #     if self.type == "chroma":
    #         return f"http://{self.host}:{self.port}"
    #     elif self.type == "pinecone":
    #         return f"{self.environment}-{self.api_key}"
    #     # Add more database types
    #     return f"{self.host}:{self.port}"

# @dataclass
# class EmbeddingConfig:
#     """Embedding model configuration"""
#     provider: str  # "openai", "huggingface", "sentence_transformers"
#     model_name: str
#     dimension: int
#     batch_size: int = 32
#     max_length: int = 512
#     normalize: bool = True
    
#     # Provider-specific settings
#     api_key: Optional[str] = None
#     device: str = "cpu"  # For local models
#     trust_remote_code: bool = False
    
#     # Performance settings
#     cache_embeddings: bool = True
#     cache_dir: str = "data/embeddings/"

# @dataclass
# class LLMCondig:
#     """Large Language Model configuration"""
#     provider: str  # "openai", "anthropic", "huggingface", "local"
#     model_name: str
#     api_key: Optional[str] = None
#     base_url: Optional[str] = None  # For local models
    
#     # Generation parameters
#     temperature: float = 0.1  # Low temp for factual responses
#     max_tokens: int = 2000
#     top_p: float = 0.9
#     frequency_penalty: float = 0.0
#     presence_penalty: float = 0.0
    
#     # Legal-specific settings
#     system_prompt: str = "You are a legal research assistant."
#     max_context_length: int = 8000
#     enable_citations: bool = True

@dataclass
class ChunkingConfig:
    """Text chunking configuration"""
    strategy: str  # "semantic", "fixed_size", "legal", "hybrid"
    chunk_size: int = 1000  # Characters or tokens
    overlap: int = 200  # Overlap between chunks
    min_chunk_size: int = 100  # Minimum viable chunk size
    
    # Legal-specific settings
    preserve_sections: bool = True
    section_headers: list = field(default_factory=lambda: [
        "BACKGROUND", "FACTS", "ANALYSIS", "CONCLUSION", "HOLDING"
    ])
    
    # Semantic chunking settings
    similarity_threshold: float = 0.7
    use_spacy: bool = True
    spacy_model: str = "en_core_web_sm"

# @dataclass
# class APIConfig:
#     """API server configuration"""
#     host: str = "0.0.0.0"
#     port: int = 8000
#     workers: int = 1
#     max_request_size: int = 10 * 1024 * 1024  # 10MB
#     timeout: int = 300  # 5 minutes
    
#     # Security
#     api_key_required: bool = True
#     cors_origins: list = field(default_factory=lambda: ["*"])
#     rate_limit: str = "100/hour"

@dataclass
class ProcessingConfig:
    """Document processing configuration"""
    supported_formats: list = field(default_factory=lambda: ["pdf"])
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    ocr_enabled: bool = True
    ocr_confidence_threshold: float = 0.8
    
    # Parallel processing
    max_workers: int = 4
    batch_size: int = 10

@dataclass
class AppConfig:
    """Main application configuration container"""
    # database: DatabaseConfig
    # embedding: EmbeddingConfig
    # llm: LLMConfig
    chunking: ChunkingConfig
    # api: APIConfig
    processing: ProcessingConfig
    
    # Global settings
    environment: str = "development"  # "development", "staging", "production"
    debug: bool = False
    data_dir: str = "data"
    temp_dir: str = "/tmp/law_rag/"


# Singleton instance
_config_instance: Optional[AppConfig] = None

def load_config(config_path: Optional[str] = None) -> AppConfig:
    """Load configuration from files and environment variables"""
    global _config_instance
    
    if _config_instance is not None:
        return _config_instance
    
    # Default config path
    if config_path is None:
        config_path = Path(__file__).parent / "model_configs"
    else:
        config_path = Path(config_path)
    
#     # Load YAML configurations
#     embedding_config = _load_yaml_config(config_path / "embedding_config.yaml")
#     llm_config = _load_yaml_config(config_path / "llm_config.yaml")
#     vectordb_config = _load_yaml_config(config_path / "vectordb_config.yaml")
    
    # Get environment-specific settings
    env = os.getenv("ENVIRONMENT", "development")
    
#     # Build configuration objects
#     database_cfg = DatabaseConfig(
#         type=os.getenv("VECTOR_DB_TYPE", vectordb_config.get("default", {}).get("type", "chroma")),
#         host=os.getenv("VECTOR_DB_HOST", vectordb_config.get("default", {}).get("host", "localhost")),
#         port=int(os.getenv("VECTOR_DB_PORT", vectordb_config.get("default", {}).get("port", 8000))),
#         collection_name=os.getenv("COLLECTION_NAME", "law_cases"),
#         api_key=os.getenv("VECTOR_DB_API_KEY"),
#     )
    
#     # Select embedding provider based on environment
#     embed_provider = os.getenv("EMBEDDING_PROVIDER", "openai")
#     embed_settings = embedding_config.get(embed_provider, {})
    
#     embedding_cfg = EmbeddingConfig(
#         provider=embed_provider,
#         model_name=os.getenv("EMBEDDING_MODEL", embed_settings.get("model_name", "")),
#         dimension=int(os.getenv("EMBEDDING_DIMENSION", embed_settings.get("dimension", 1536))),
#         batch_size=int(os.getenv("EMBEDDING_BATCH_SIZE", embed_settings.get("batch_size", 32))),
#         api_key=os.getenv("OPENAI_API_KEY") if embed_provider == "openai" else None,
#     )
    
#     # Select LLM provider
#     llm_provider = os.getenv("LLM_PROVIDER", "openai")
#     llm_settings = llm_config.get(llm_provider, {})
    
#     llm_cfg = LLMConfig(
#         provider=llm_provider,
#         model_name=os.getenv("LLM_MODEL", llm_settings.get("model_name", "")),
#         api_key=os.getenv("OPENAI_API_KEY") if llm_provider == "openai" else os.getenv("ANTHROPIC_API_KEY"),
#         temperature=float(os.getenv("LLM_TEMPERATURE", llm_settings.get("temperature", 0.1))),
#         max_tokens=int(os.getenv("LLM_MAX_TOKENS", llm_settings.get("max_tokens", 2000))),
#     )
    
    chunking_cfg = ChunkingConfig(
        strategy=os.getenv("CHUNKING_STRATEGY", "semantic"),
        chunk_size=int(os.getenv("CHUNK_SIZE", "1000")),
        overlap=int(os.getenv("CHUNK_OVERLAP", "200")),
    )
    
#     api_cfg = APIConfig(
#         host=os.getenv("API_HOST", "0.0.0.0"),
#         port=int(os.getenv("API_PORT", "8000")),
#         workers=int(os.getenv("API_WORKERS", "1")),
#     )
    
    processing_cfg = ProcessingConfig(
        max_workers=int(os.getenv("MAX_WORKERS", "4")),
        batch_size=int(os.getenv("PROCESSING_BATCH_SIZE", "10")),
    )
    
    # Create main config
    _config_instance = AppConfig(
        # database=database_cfg,
        # embedding=embedding_cfg,
        # llm=llm_cfg,
        chunking=chunking_cfg,
        # api=api_cfg,
        processing=processing_cfg,
        environment=env,
        debug=os.getenv("DEBUG", "false").lower() == "true",
        data_dir=os.getenv("DATA_DIR", "data/"),
        temp_dir=os.getenv("TEMP_DIR", "/tmp/law_rag/"),
    )
    
    return _config_instance

def _load_yaml_config(file_path: Path) -> Dict[str, Any]:
    """Load YAML configuration file"""
    if not file_path.exists():
        return {}
    
    try:
        with open(file_path, 'r') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"Warning: Could not load config file {file_path}: {e}")
        return {}

def get_config() -> AppConfig:
    """Get the singleton configuration instance"""
    if _config_instance is None:
        return load_config()
    return _config_instance

# def reload_config(config_path: Optional[str] = None):
#     """Force reload configuration"""
#     global _config_instance
#     _config_instance = None
#     return load_config(config_path)

# def validate_config(config: AppConfig) -> List[str]:
#     """Validate configuration and return list of errors"""
#     errors = []
    
#     # Validate required API keys
#     if config.embedding.provider == "openai" and not config.embedding.api_key:
#         errors.append("OpenAI API key is required for OpenAI embeddings")
    
#     if config.llm.provider == "openai" and not config.llm.api_key:
#         errors.append("OpenAI API key is required for OpenAI LLM")
    
#     # Validate paths
#     data_path = Path(config.data_dir)
#     if not data_path.exists():
#         try:
#             data_path.mkdir(parents=True, exist_ok=True)
#         except Exception as e:
#             errors.append(f"Cannot create data directory: {e}")
    
#     # Validate chunk settings
#     if config.chunking.chunk_size <= config.chunking.overlap:
#         errors.append("Chunk size must be greater than overlap")
    
#     if config.chunking.overlap < 0:
#         errors.append("Chunk overlap cannot be negative")
    
#     # Validate embedding dimensions
#     if config.embedding.dimension <= 0:
#         errors.append("Embedding dimension must be positive")
    
#     return errors