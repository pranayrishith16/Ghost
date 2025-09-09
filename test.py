import weaviate
from src.embedder.sentence_transformer_embedder import SentenceTransformersEmbedder

embedder = SentenceTransformersEmbedder()

client = weaviate.connect_to_local()
client.collections.delete_all()
client.close()