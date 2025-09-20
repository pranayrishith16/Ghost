import logging
from typing import List

from loguru import logger
import numpy as np
from sentence_transformers import SentenceTransformer

from config.settings import get_config
from src.interfaces.embedder import EmbedderInterface

class SentenceTransformersEmbedder(EmbedderInterface):
    """Sentence Transformers embeddings implementation"""

    def __init__(self) -> None:
        self.logger = logger
        cfg = get_config().embedding
        if getattr(cfg, 'provider', None) != "sentence-transformers":
            raise ValueError(f"Invalid provider: {getattr(cfg, 'provider', None)}. Expected 'sentence-transformers'")

        # If device is not available fallback to 'cpu'
        self.config = cfg
        self.model = SentenceTransformer(self.config.model_name, device=self.config.device)
        self._dimension = self.model.get_sentence_embedding_dimension()

    def embed_text(self, text: str) -> List[float]:
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        embeddings = self.embed_batch([text])
        return embeddings[0] if embeddings else []

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        # Preserve positions; compute only for non-empty strings
        positions = []
        payload = []

        for idx, t in enumerate(texts):
            if t and t.strip():
                positions.append(idx)
                payload.append(t)
        
        if not payload:
            return [[] for _ in texts]

        try:
            embeddings = self.model.encode(
                payload,
                batch_size=self.config.batch_size,
                show_progress_bar=False,
                normalize_embeddings=getattr(self.config, "normalize", True),
                convert_to_numpy=True,
            )
            # Map back to original positions
            result = [[] for _ in texts]
            for i, pos in enumerate(positions):
                vec = embeddings[i].tolist() if hasattr(embeddings[i], "tolist") else list(embeddings[i])
                result[pos] = vec
            return result
        except Exception as e:
            self.logger.error(f"SentenceTransformer batch embedding failed: {e}")
            raise

    def get_dimension(self) -> int:
        return self._dimension

    def get_model_name(self) -> str:
        return self.config.model_name

    def similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        if not embedding1 or not embedding2:
            return 0.0
        if len(embedding1) != len(embedding2):
            raise ValueError("Embeddings must have the same dimension")
        emb1 = np.array(embedding1, dtype=np.float32)
        emb2 = np.array(embedding2, dtype=np.float32)
        denom = (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        if denom == 0.0:
            self.logger.warning("One or both embeddings have zero norm. Similarity set to 0.0")
            return 0.0
        return float(np.dot(emb1, emb2) / denom)
