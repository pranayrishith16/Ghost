from pathlib import Path
from src.core.pipeline import RAGPipeline
import sys

#correcting import
from config.settings import get_config

config = get_config()
dir = Path(config.data_dir)

pipeline = RAGPipeline()
pipeline.batch_injest(dir)