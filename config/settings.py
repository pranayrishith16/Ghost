from dataclasses import dataclass
from pathlib import Path
from turtle import st
from typing import Optional, Any, Dict
import os
import yaml
from dotenv import load_dotenv

load_dotenv()

@dataclass
class ChunkingConfig:
    strategy: str
    chunk_size: int = 1000
    overlap: int = 200

@dataclass
class EmbeddingConfig:
    provider: str
    model_name: str
    dimension: int
    batch_size: int
    max_length: int
    normalize: bool
    api_key: Optional[str] = None
    device: Optional[str] = None

@dataclass
class LLMConfig:
    provider:str
    model_name:str
    api_key:str
    base_url: Optional[str] = None
    max_tokens:int = 2000
    temperature:float=0.1
    top_p:float=0.9
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    max_context_length: int = 16000
    system_prompt: str = "You are a legal research assistant. Provide accurate and comprehensive legal analysis."
    enable_citations: bool = True

@dataclass
class VectorStoreConfig:
    provider:str
    host:str = 'localhost'
    port:int = 8080
    collection_name:str = 'legal_case_files'
    index_type:str = 'hnsw'
    distance_metric:str = 'cosine'

@dataclass
class MonitoringConfig:
    type: str
    tracking_uri: str
    experiment_name: str

@dataclass
class AppConfig:
    chunking: ChunkingConfig
    monitoring: MonitoringConfig
    embedding: EmbeddingConfig
    llm:LLMConfig
    vector_store:VectorStoreConfig
    environment: str = "development"
    data_dir: str = "data"

_config_instance: Optional[AppConfig] = None

def _load_yaml_config(file_path: Path) -> Dict[str, Any]:
    if not file_path.exists():
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        print(f'failed to load YAML file {file_path}')
        return {}

def _to_bool(val: Any, default: bool = True) -> bool:
    """Converts various value types into boolean"""
    if isinstance(val, bool):
        return val
    if val is None:
        return default
    s = str(val).strip().lower()
    return s in {"1", "true", "t", "yes", "y", "on"}

def config_load(config_path: Optional[str] = None) -> AppConfig:
    """Load application configuration from environment variables and YAML files"""
    global _config_instance
    if _config_instance is not None:
        return _config_instance

    base = Path(config_path) if config_path else Path(__file__).parent
    env = os.getenv("ENVIRONMENT", "development")

    #loading YAML files
    embedding_yaml = _load_yaml_config(base / "embedding_config.yaml")
    llm_yaml = _load_yaml_config(base / "llm_config.yaml")

    # Embedding provider and defaults
    embed_provider = os.getenv("EMBEDDING_PROVIDER", "sentence-transformers")
    provider_defaults: Dict[str, Any] = embedding_yaml.get(embed_provider, {})
    # Support both 'normalize' and 'normalize_embeddings' keys from YAML
    normalize_default = provider_defaults.get("normalize", provider_defaults.get("normalize_embeddings", True))

    chunking_cfg = ChunkingConfig(
        strategy=os.getenv("CHUNKING_STRATEGY", "legal"),
        chunk_size=int(os.getenv("CHUNK_SIZE", "1000")),
        overlap=int(os.getenv("CHUNK_OVERLAP", "200")),
    )

    embedding_cfg = EmbeddingConfig(
        provider=embed_provider,
        model_name=os.getenv("EMBEDDING_MODEL", provider_defaults.get("model_name", "")),
        dimension=int(os.getenv("EMBEDDING_DIMENSION", provider_defaults.get("dimension", 1536))),
        batch_size=int(os.getenv("EMBEDDING_BATCH_SIZE", provider_defaults.get("batch_size", 32))),
        max_length=int(os.getenv("EMBEDDING_MAX_LENGTH", provider_defaults.get("max_length", 512))),
        normalize=_to_bool(os.getenv("EMBEDDING_NORMALIZE", normalize_default), True),
        device=os.getenv("EMBEDDING_DEVICE", provider_defaults.get("device", "cpu")),
        api_key=os.getenv("EMBEDDING_API_KEY"),
    )

    # LLM configuration
    llm_provider = os.getenv("LLM_PROVIDER",'openrouter')
    llm_defaults = llm_yaml.get(llm_provider, {})

    llm_config = LLMConfig(
        provider=llm_provider,
        model_name=os.getenv("LLM_MODEL", llm_defaults.get("model_name", "openai/gpt-oss-20b:free")),
        api_key=os.getenv("LLM_API_KEY", ""),
        base_url=os.getenv("LLM_BASE_URL", llm_defaults.get("base_url")),
        max_tokens=int(os.getenv("LLM_MAX_TOKENS", llm_defaults.get("max_tokens", 2000))),
        temperature=float(os.getenv("LLM_TEMPERATURE", llm_defaults.get("temperature", 0.1))),
        top_p=float(os.getenv("LLM_TOP_P", llm_defaults.get("top_p", 0.9))),
        frequency_penalty=float(os.getenv("LLM_FREQUENCY_PENALTY", llm_defaults.get("frequency_penalty", 0.0))),
        presence_penalty=float(os.getenv("LLM_PRESENCE_PENALTY", llm_defaults.get("presence_penalty", 0.0))),
        max_context_length=int(os.getenv("LLM_MAX_CONTEXT", llm_defaults.get("max_context_length", 16000))),
        system_prompt=os.getenv("LLM_SYSTEM_PROMPT", llm_defaults.get("system_prompt", 
            "You are a legal research assistant. Provide accurate and comprehensive legal analysis.")),
        enable_citations=_to_bool(os.getenv("LLM_ENABLE_CITATIONS", llm_defaults.get("enable_citations", True))),
    )

    # Vector Store Configuration
    vector_store_cfg = VectorStoreConfig(
        provider=os.getenv("VECTOR_STORE_PROVIDER", "weaviate"),
        host=os.getenv("VECTOR_STORE_HOST", "localhost"),
        port=int(os.getenv("VECTOR_STORE_PORT", "8080")),
        collection_name=os.getenv("VECTOR_STORE_COLLECTION", "legal_documents"),
        index_type=os.getenv("VECTOR_STORE_INDEX_TYPE", "hnsw"),
        distance_metric=os.getenv("VECTOR_STORE_DISTANCE_METRIC", "cosine"),
    )

    monitoring_type = os.getenv("MONITORING_TYPE")
    monitoring_uri = os.getenv("MLFLOW_TRACKING_URI")
    experiment_name = os.getenv("EXPERIMENT_NAME")

    monitoring_cfg = None
    if monitoring_type and monitoring_uri and experiment_name:
        monitoring_cfg = MonitoringConfig(
            type=monitoring_type,
            tracking_uri=monitoring_uri,
            experiment_name=experiment_name,
        )

    _config_instance = AppConfig(
        chunking=chunking_cfg,
        llm=llm_config,
        vector_store=vector_store_cfg,
        embedding=embedding_cfg,
        environment=env,
        monitoring=monitoring_cfg,
        data_dir=os.getenv("DATA_DIR", "data/raw/"),
    )
    return _config_instance

def get_config() -> AppConfig:
    return config_load()

def reset_config():
    """reset configurations"""
    global _config_instance
    _config_instance = None
