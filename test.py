import weaviate
from src.embedder.sentence_transformer_embedder import SentenceTransformersEmbedder

embedder = SentenceTransformersEmbedder()

client = weaviate.connect_to_local()
try:
    collection = client.collections.get('LegalDocument')
    
    # Generate vector
    query_text = "Appellee’s statutory claims"
    query_vector = embedder.embed_text(query_text)
    
    # Fix: Flatten the nested list
    if query_vector and isinstance(query_vector[0], list):
        query_vector = query_vector[0]  # Extract the actual vector from the nested structure
    
    print(f"Flattened vector length: {len(query_vector)}")
    
    # Now this should work
    response = collection.query.near_vector(
        near_vector=query_vector,
        limit=5
    )
    
    print("Semantic Search Results:")
    for obj in response.objects:
        print(f"UUID: {obj.uuid}")
        print(f"Properties: {obj.properties}")
        print("---")
        
finally:
    client.close()
