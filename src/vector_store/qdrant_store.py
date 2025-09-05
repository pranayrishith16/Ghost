import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models
import sys
from pathlib import Path

# Fix import path
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.settings import get_config

from archive_src.interfaces.vector_store import VectorStoreInterface

class QdrantStore(VectorStoreInterface):
    """Qdrant vector store implementation"""

    def __init__(self):
        self.config = get_config().database
        self.logger = logging.getLogger(__name__)
        
        if self.config.type != "qdrant":
            raise ValueError(f"Invalid database type: {self.config.type}. Expected 'qdrant'")
        
        # Initialize Qdrant client
        self.client = QdrantClient(
            host=self.config.host,
            port=self.config.port,
            prefer_grpc=False
        )
        
        self._ensure_collection()
        
        self.logger.info(f"Initialized QdrantStore with collection: {self.config.collection_name}")

    def _ensure_collection(self):
        """Ensure collection exists with proper configuration"""
        try:
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.config.collection_name not in collection_names:
                # Create collection
                self.client.create_collection(
                    collection_name=self.config.collection_name,
                    vectors_config=models.VectorParams(
                        size=1536,  # Will be updated dynamically
                        distance=models.Distance.COSINE
                    )
                )
                self.logger.info(f"Created new collection: {self.config.collection_name}")
                
        except Exception as e:
            self.logger.error(f"Failed to ensure collection: {e}")
            raise

    def create_collection(self, name: str, dimension: int, metadata_schema: Dict[str, Any] = None):
        """Create a new collection"""
        try:
            self.client.create_collection(
                collection_name=name,
                vectors_config=models.VectorParams(
                    size=dimension,
                    distance=models.Distance.COSINE
                )
            )
            self.logger.info(f"Created collection: {name}")
        except Exception as e:
            self.logger.error(f"Failed to create collection {name}: {e}")
            raise

    def insert(self, vectors: List[List[float]], metadata: List[Dict[str, Any]], ids: List[str]):
        """Insert vectors with metadata"""
        if not all([vectors, metadata, ids]):
            raise ValueError("Vectors, metadata, and ids must be provided")
        
        if len(vectors) != len(metadata) != len(ids):
            raise ValueError("Vectors, metadata, and ids must have the same length")
        
        try:
            # Prepare points for Qdrant
            points = []
            for i, (vector, meta, id_) in enumerate(zip(vectors, metadata, ids)):
                points.append(models.PointStruct(
                    id=id_,
                    vector=vector,
                    payload=meta
                ))
            
            # Upsert points
            self.client.upsert(
                collection_name=self.config.collection_name,
                points=points
            )
            
            self.logger.info(f"Inserted {len(ids)} vectors into Qdrant")
            
        except Exception as e:
            self.logger.error(f"Failed to insert vectors: {e}")
            raise

    def search(self, query_vector: List[float], k: int = 10, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search for similar vectors"""
        if not query_vector:
            raise ValueError("Query vector cannot be empty")
        
        try:
            # Convert filters to Qdrant format
            filter_condition = None
            if filters:
                must_conditions = []
                for key, value in filters.items():
                    if isinstance(value, list):
                        must_conditions.append(models.FieldCondition(
                            key=key,
                            match=models.MatchAny(any=value)
                        ))
                    else:
                        must_conditions.append(models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=value)
                        ))
                
                filter_condition = models.Filter(must=must_conditions)
            
            results = self.client.search(
                collection_name=self.config.collection_name,
                query_vector=query_vector,
                limit=k,
                query_filter=filter_condition,
                with_payload=True,
                with_vectors=True
            )
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'id': result.id,
                    'metadata': result.payload,
                    'distance': result.score,
                    'embedding': result.vector,
                    'score': result.score
                })
            
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            raise

    def delete(self, ids: List[str]) -> bool:
        """Delete vectors by IDs"""
        if not ids:
            return True
        
        try:
            self.client.delete(
                collection_name=self.config.collection_name,
                points_selector=models.PointIdsList(
                    points=ids
                )
            )
            self.logger.info(f"Deleted {len(ids)} vectors from Qdrant")
            return True
        except Exception as e:
            self.logger.error(f"Delete failed: {e}")
            return False

    def update(self, ids: List[str], vectors: List[List[float]], metadata: List[Dict[str, Any]]):
        """Update existing vectors"""
        if len(ids) != len(vectors) != len(metadata):
            raise ValueError("IDs, vectors, and metadata must have the same length")
        
        try:
            # For Qdrant, update is the same as insert (upsert behavior)
            self.insert(vectors, metadata, ids)
        except Exception as e:
            self.logger.error(f"Update failed: {e}")
            raise

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            info = self.client.get_collection(collection_name=self.config.collection_name)
            return {
                'vector_count': info.vectors_count,
                'collection_name': self.config.collection_name,
                'database_type': 'qdrant',
                'dimension': info.config.params.vectors.size,
                'distance': info.config.params.vectors.distance.name
            }
        except Exception as e:
            self.logger.error(f"Failed to get stats: {e}")
            return {'error': str(e)}