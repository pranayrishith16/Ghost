import logging
from typing import List, Dict, Any, Optional
import pinecone
from pinecone import ServerlessSpec
import sys
from pathlib import Path

# Fix import path
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.settings import get_config

from archive_src.interfaces.vector_store import VectorStoreInterface

class PineconeStore(VectorStoreInterface):
    """Pinecone vector store implementation"""

    def __init__(self):
        self.config = get_config().database
        self.logger = logging.getLogger(__name__)
        
        if self.config.type != "pinecone":
            raise ValueError(f"Invalid database type: {self.config.type}. Expected 'pinecone'")
        
        if not self.config.api_key:
            raise ValueError("Pinecone API key is required")
        
        # Initialize Pinecone
        pinecone.init(
            api_key=self.config.api_key,
            environment=self.config.environment
        )
        
        self.index = None
        self._ensure_index()
        
        self.logger.info(f"Initialized PineconeStore with index: {self.config.index_name}")

    def _ensure_index(self):
        """Ensure index exists with proper configuration"""
        try:
            # Check if index exists
            if self.config.index_name not in pinecone.list_indexes():
                # Create index
                pinecone.create_index(
                    name=self.config.index_name,
                    dimension=1536,  # Will be updated dynamically
                    metric=self.config.distance_metric,
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-west-2"
                    )
                )
                self.logger.info(f"Created new index: {self.config.index_name}")
            
            # Connect to index
            self.index = pinecone.Index(self.config.index_name)
            
        except Exception as e:
            self.logger.error(f"Failed to ensure index: {e}")
            raise

    def create_collection(self, name: str, dimension: int, metadata_schema: Dict[str, Any] = None):
        """Create a new index (Pinecone equivalent of collection)"""
        try:
            pinecone.create_index(
                name=name,
                dimension=dimension,
                metric=self.config.distance_metric,
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-west-2"
                )
            )
            self.logger.info(f"Created index: {name}")
        except Exception as e:
            self.logger.error(f"Failed to create index {name}: {e}")
            raise

    def insert(self, vectors: List[List[float]], metadata: List[Dict[str, Any]], ids: List[str]):
        """Insert vectors with metadata"""
        if not all([vectors, metadata, ids]):
            raise ValueError("Vectors, metadata, and ids must be provided")
        
        if len(vectors) != len(metadata) != len(ids):
            raise ValueError("Vectors, metadata, and ids must have the same length")
        
        try:
            # Prepare data for Pinecone
            vectors_to_upsert = []
            for i, (vector, meta, id_) in enumerate(zip(vectors, metadata, ids)):
                vectors_to_upsert.append({
                    'id': id_,
                    'values': vector,
                    'metadata': meta
                })
            
            # Upsert in batches
            batch_size = 100
            for i in range(0, len(vectors_to_upsert), batch_size):
                batch = vectors_to_upsert[i:i + batch_size]
                self.index.upsert(vectors=batch)
            
            self.logger.info(f"Inserted {len(ids)} vectors into Pinecone")
            
        except Exception as e:
            self.logger.error(f"Failed to insert vectors: {e}")
            raise

    def search(self, query_vector: List[float], k: int = 10, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search for similar vectors"""
        if not query_vector:
            raise ValueError("Query vector cannot be empty")
        
        try:
            # Convert filters to Pinecone format
            filter_dict = None
            if filters:
                filter_dict = {}
                for key, value in filters.items():
                    if isinstance(value, list):
                        filter_dict[key] = {"$in": value}
                    else:
                        filter_dict[key] = value
            
            results = self.index.query(
                vector=query_vector,
                top_k=k,
                filter=filter_dict,
                include_metadata=True,
                include_values=True
            )
            
            # Format results
            formatted_results = []
            for match in results['matches']:
                formatted_results.append({
                    'id': match['id'],
                    'metadata': match['metadata'],
                    'distance': match['score'],
                    'embedding': match['values'],
                    'score': match['score']
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
            self.index.delete(ids=ids)
            self.logger.info(f"Deleted {len(ids)} vectors from Pinecone")
            return True
        except Exception as e:
            self.logger.error(f"Delete failed: {e}")
            return False

    def update(self, ids: List[str], vectors: List[List[float]], metadata: List[Dict[str, Any]]):
        """Update existing vectors - same as insert for Pinecone"""
        self.insert(vectors, metadata, ids)

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            stats = self.index.describe_index_stats()
            return {
                'vector_count': stats['total_vector_count'],
                'index_name': self.config.index_name,
                'database_type': 'pinecone',
                'dimension': stats['dimension'],
                'index_fullness': stats['index_fullness']
            }
        except Exception as e:
            self.logger.error(f"Failed to get stats: {e}")
            return {'error': str(e)}