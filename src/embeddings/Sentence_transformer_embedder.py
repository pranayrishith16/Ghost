# import logging
# from typing import List
# import numpy as np
# from sentence_transformers import SentenceTransformer
# import sys
# from pathlib import Path

# # Fix import path
# sys.path.append(str(Path(__file__).parent.parent.parent))
# from config.settings import get_config

# from src.interfaces.embedder import EmbedderInterface

# class SentenceTransformerEmbedder(EmbedderInterface):
#     """Sentence Transformers embeddings implementation"""

#     def __init__(self):
#         self.config = get_config().embedding
#         self.logger = logging.getLogger(__name__)
        
#         # Validate configuration
#         if self.config.provider != "sentence_transformers":
#             raise ValueError(f"Invalid provider: {self.config.provider}. Expected 'sentence_transformers'")
        
#         # Initialize Sentence Transformer model
#         self.logger.info(f"Loading SentenceTransformer model: {self.config.model_name}")
        
#         self.model = SentenceTransformer(
#             self.config.model_name,
#             device=self.config.device
#         )
        
#         # Override model dimension with actual dimension
#         actual_dimension = self.model.get_sentence_embedding_dimension()
#         if actual_dimension != self.config.dimension:
#             self.logger.warning(f"Config dimension {self.config.dimension} doesn't match model dimension {actual_dimension}. Using model dimension.")
        
#         self.logger.info(f"Initialized SentenceTransformerEmbedder with model: {self.config.model_name}")

#     def embed_text(self, text: str) -> List[float]:
#         """Generate embedding for single text"""
#         if not text.strip():
#             raise ValueError("Text cannot be empty")
        
#         return self.embed_batch([text])[0]

#     def embed_batch(self, texts: List[str]) -> List[List[float]]:
#         """Generate embeddings for batch of texts"""
#         if not texts:
#             return []
        
#         # Filter out empty texts
#         valid_texts = [text for text in texts if text.strip()]
#         if not valid_texts:
#             return [[] for _ in texts]
        
#         try:
#             # Generate embeddings
#             embeddings = self.model.encode(
#                 valid_texts,
#                 batch_size=self.config.batch_size,
#                 show_progress_bar=False,
#                 normalize_embeddings=self.config.normalize,
#                 convert_to_numpy=True
#             )
            
#             # Map back to original positions (handling empty texts)
#             result = []
#             text_index = 0
#             for text in texts:
#                 if text.strip():
#                     result.append(embeddings[text_index].tolist())
#                     text_index += 1
#                 else:
#                     result.append([])
            
#             return result
            
#         except Exception as e:
#             self.logger.error(f"SentenceTransformer batch embedding failed: {e}")
#             raise

#     def get_dimension(self) -> int:
#         """Get embedding dimension"""
#         return self.model.get_sentence_embedding_dimension()

#     def get_model_name(self) -> str:
#         """Get model name/identifier"""
#         return self.config.model_name

#     def similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
#         """Calculate cosine similarity between embeddings"""
#         if not embedding1 or not embedding2:
#             return 0.0
        
#         if len(embedding1) != len(embedding2):
#             raise ValueError("Embeddings must have the same dimension")
        
#         # Use the model's similarity function if available, otherwise compute manually
#         try:
#             # Convert to numpy arrays
#             emb1 = np.array(embedding1)
#             emb2 = np.array(embedding2)
            
#             # Use model's similarity calculation
#             if hasattr(self.model, 'similarity'):
#                 return float(self.model.similarity(emb1, emb2))
#             else:
#                 # Manual cosine similarity
#                 similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
#                 return float(similarity)
                
#         except Exception:
#             # Fallback to manual calculation
#             emb1 = np.array(embedding1)
#             emb2 = np.array(embedding2)
#             similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
#             return float(similarity)