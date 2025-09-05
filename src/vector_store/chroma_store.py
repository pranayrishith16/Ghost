import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
import numpy as np
import sys
from pathlib import Path

# Fix import path
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.settings import get_config

from archive_src.interfaces.vector_store import VectorStoreInterface

class ChromaStore(VectorStoreInterface):
    """ChromaDB vector store implementation"""

    def __init__(self):
        self.config = get_config().database
        self.logger = logging.getLogger(__name__)
        
        if self.config.type != "chroma":
            raise ValueError(f"Invalid database type: {self.config.type}. Expected 'chroma'")
        
        # Initialize Chroma client
        self.client = chromadb.HttpClient(
            host=self.config.host,
            port=self.config.port,
            settings=Settings(allow_reset=True, anonymized_telemetry=False)
        )
        
        self.collection = None
        self._ensure_collection()
        
        self.logger.info(f"Initialized ChromaStore with collection: {self.config.collection_name}")

    def _ensure_collection(self):
        """Ensure collection exists with proper configuration"""
        try:
            self.collection = self.client.get_collection(
                name=self.config.collection_name,
                embedding_function=None  # We provide our own embeddings
            )
        except Exception:
            # Collection doesn't exist, create it
            self.collection = self.client.create_collection(
                name=self.config.collection_name,
                metadata={
                    "hnsw:space": self.config.distance_metric,
                    "hnsw:construction_ef": self.config.ef_construction,
                    "hnsw:M": self.config.m
                }
            )
            self.logger.info(f"Created new collection: {self.config.collection_name}")

    def create_collection(self, name: str, dimension: int, metadata_schema: Dict[str, Any] = None):
        """Create a new collection"""
        try:
            collection = self.client.create_collection(
                name=name,
                metadata={
                    "hnsw:space": self.config.distance_metric,
                    "dimension": dimension,
                    **(metadata_schema or {})
                }
            )
            self.logger.info(f"Created collection: {name}")
            return collection
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
            # Convert to lists for Chroma
            vectors_list = [vector for vector in vectors]
            metadatas = [meta for meta in metadata]
            
            self.collection.upsert(
                embeddings=vectors_list,
                metadatas=metadatas,
                ids=ids
            )
            self.logger.info(f"Inserted {len(ids)} vectors into ChromaDB")
            
        except Exception as e:
            self.logger.error(f"Failed to insert vectors: {e}")
            raise

    def search(self, query_vector: List[float], k: int = 10, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search for similar vectors"""
        if not query_vector:
            raise ValueError("Query vector cannot be empty")
        
        try:
            # Convert filters to Chroma format
            where = None
            if filters:
                where = {}
                for key, value in filters.items():
                    if isinstance(value, list):
                        where[key] = {"$in": value}
                    else:
                        where[key] = value
            
            results = self.collection.query(
                query_embeddings=[query_vector],
                n_results=k,
                where=where,
                include=["metadatas", "distances", "embeddings"]
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    'id': results['ids'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i],
                    'embedding': results['embeddings'][0][i] if results['embeddings'] else None,
                    'score': 1 - results['distances'][0][i]  # Convert distance to similarity score
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
            self.collection.delete(ids=ids)
            self.logger.info(f"Deleted {len(ids)} vectors from ChromaDB")
            return True
        except Exception as e:
            self.logger.error(f"Delete failed: {e}")
            return False

    def update(self, ids: List[str], vectors: List[List[float]], metadata: List[Dict[str, Any]]):
        """Update existing vectors"""
        if len(ids) != len(vectors) != len(metadata):
            raise ValueError("IDs, vectors, and metadata must have the same length")
        
        try:
            self.collection.upsert(
                embeddings=vectors,
                metadatas=metadata,
                ids=ids
            )
            self.logger.info(f"Updated {len(ids)} vectors in ChromaDB")
        except Exception as e:
            self.logger.error(f"Update failed: {e}")
            raise

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            count = self.collection.count()
            return {
                'vector_count': count,
                'collection_name': self.config.collection_name,
                'database_type': 'chroma'
            }
        except Exception as e:
            self.logger.error(f"Failed to get stats: {e}")
            return {'error': str(e)}