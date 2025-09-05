import json
from sentence_transformers import SentenceTransformer


class ChunkEmbedder:
    def __init__(self,model_name='sentence-transformers/all-MiniLM-L6-v2',batch_size=64):
        self.model = SentenceTransformer(model_name)
        self.batch_size = batch_size

        