# from typing import List, Optional
# import numpy as np
# import openai
# from tenacity import retry, stop_after_attempt, wait_exponential
# import sys
# from pathlib import Path

# # Fix import path
# sys.path.append(str(Path(__file__).parent.parent.parent))
# from config.settings import get_config

# from source.interfaces.embedder import EmbedderInterface

# class OpenAIEmbedder(EmbedderInterface):
#     """OpenAI embeddings implementation"""

#     def __init__(self):
#         self.config = get_config().embedding
        
#         # Validate configuration
#         if self.config.provider != "openai":
#             raise ValueError(f"Invalid provider: {self.config.provider}. Expected 'openai'")
        
#         if not self.config.api_key:
#             raise ValueError("OpenAI API key is required")
        
#         # Initialize OpenAI client
#         openai.api_key = self.config.api_key
        
#         self.logger.info(f"Initialized OpenAIEmbedder with model: {self.config.model_name}")

#     @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
#     def embed_text(self, text: str) -> List[float]:
#         """Generate embedding for single text"""
#         if not text.strip():
#             raise ValueError("Text cannot be empty")
        
#         try:
#             response = openai.embeddings.create(
#                 model=self.config.model_name,
#                 input=text,
#                 encoding_format="float"
#             )
#             return response.data[0].embedding
            
#         except Exception as e:
#             self.logger.error(f"OpenAI embedding failed for text: {e}")
#             raise

#     @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
#     def embed_batch(self, texts: List[str]) -> List[List[float]]:
#         """Generate embeddings for batch of texts"""
#         if not texts:
#             return []
        
#         # Filter out empty texts
#         valid_texts = [text for text in texts if text.strip()]
#         if not valid_texts:
#             return [[] for _ in texts]
        
#         try:
#             response = openai.embeddings.create(
#                 model=self.config.model_name,
#                 input=valid_texts,
#                 encoding_format="float"
#             )
            
#             # Map back to original positions (handling empty texts)
#             embeddings = []
#             text_index = 0
#             for text in texts:
#                 if text.strip():
#                     embeddings.append(response.data[text_index].embedding)
#                     text_index += 1
#                 else:
#                     embeddings.append([])
            
#             return embeddings
            
#         except Exception as e:
#             self.logger.error(f"OpenAI batch embedding failed: {e}")
#             raise

#     def get_dimension(self) -> int:
#         """Get embedding dimension"""
#         return self.config.dimension

#     def get_model_name(self) -> str:
#         """Get model name/identifier"""
#         return self.config.model_name

#     def similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
#         """Calculate cosine similarity between embeddings"""
#         if not embedding1 or not embedding2:
#             return 0.0
        
#         if len(embedding1) != len(embedding2):
#             raise ValueError("Embeddings must have the same dimension")
        
#         # Convert to numpy arrays for efficient calculation
#         emb1 = np.array(embedding1)
#         emb2 = np.array(embedding2)
        
#         # Cosine similarity
#         similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
#         return float(similarity)