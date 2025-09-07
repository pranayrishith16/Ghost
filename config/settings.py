from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Any, List, Dict
import os

from dotenv import load_dotenv

load_dotenv()  # Load .env variables into environment


@dataclass
class ChunkingConfig:
    """Text chunking configuration"""
    strategy: str  # "semantic", "fixed_size", "legal", "hybrid"
    chunk_size: int = 1000  # Characters or tokens
    overlap: int = 200  # Overlap between chunks

@dataclass
class AppConfig:
    """Main application Configuration Container"""
    chunking:ChunkingConfig

    #Global settings
    environment:str = 'development'
    data_dir:str = 'data'

#singleton instance
_config_instance : Optional[AppConfig] = None

def config_load(config_path: Optional[str] = None) -> AppConfig:
    """Load configuration from files and environment variables"""
    global _config_instance

    if _config_instance is not None:
        return _config_instance
    
    # Get environment-specific settings
    env = os.getenv("ENVIRONMENT", "development")

    chunking_cfg = ChunkingConfig(
        strategy=os.getenv("CHUNKING_STRATEGY", "legal"),
        chunk_size=int(os.getenv("CHUNK_SIZE", "1000")),
        overlap=int(os.getenv("CHUNK_OVERLAP", "200")),
    )

    #creating main config
    _config_instance = AppConfig(
        chunking=chunking_cfg,
        environment=env,
        data_dir=os.getenv("DATA_DIR", "data/raw/"),
    )

    return _config_instance

def get_config() -> AppConfig:
    """Get singleton configuration instance"""
    if _config_instance is None:
        return config_load()
    return _config_instance