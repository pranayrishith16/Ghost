# import logging
# from typing import List
# import numpy as np
# from transformers import AutoTokenizer, AutoModel
# import torch
# import sys
# from pathlib import Path

# # Fix import path
# sys.path.append(str(Path(__file__).parent.parent.parent))
# from config.settings import get_config

# from src.interfaces.embedder import EmbedderInterface

# class HuggingFaceEmbedder(EmbedderInterface):
#     """HuggingFace transformers embeddings implementation"""

#     def __init__(self):
#         self.config = get_config().embedding
#         self.logger = logging.getLogger(__name__)
        
#         # Validate configuration
#         if self.config.provider != "huggingface":
#             raise ValueError(f"Invalid provider: {self.config.provider}. Expected 'huggingface'")
        
#         # Initialize model and tokenizer
#         self.logger.info(f"Loading HuggingFace model: {self.config.model_name}")
        
#         self.tokenizer = AutoTokenizer.from_pretrained(
#             self.config.model_name,
#             trust_remote_code=self.config.trust_remote_code
#         )
        
#         self.model = AutoModel.from_pretrained(
#             self.config.model_name,
#             trust_remote_code=self.config.trust_remote_code,
#             device_map=self.config.device
#         )
        
#         self.model.eval()  # Set to evaluation mode
        
#         self.logger.info(f"Initialized HuggingFaceEmbedder with model: {self.config.model_name}")

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
#             # Tokenize texts
#             inputs = self.tokenizer(
#                 valid_texts,
#                 padding=True,
#                 truncation=True,
#                 max_length=self.config.max_length,
#                 return_tensors="pt"
#             )
            
#             # Move to appropriate device
#             inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
            
#             # Generate embeddings
#             with torch.no_grad():
#                 outputs = self.model(**inputs)
#                 embeddings = self._mean_pooling(outputs, inputs['attention_mask'])
                
#                 if self.config.normalize:
#                     embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
                
#                 embeddings = embeddings.cpu().numpy().tolist()
            
#             # Map back to original positions (handling empty texts)
#             result = []
#             text_index = 0
#             for text in texts:
#                 if text.strip():
#                     result.append(embeddings[text_index])
#                     text_index += 1
#                 else:
#                     result.append([])
            
#             return result
            
#         except Exception as e:
#             self.logger.error(f"HuggingFace batch embedding failed: {e}")
#             raise

#     def _mean_pooling(self, model_output, attention_mask):
#         """Mean pooling to get sentence embeddings"""
#         token_embeddings = model_output.last_hidden_state
#         input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
#         sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
#         sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
#         return sum_embeddings / sum_mask

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