import logging
from typing import List, Dict, Any, Optional
import weaviate
from weaviate import AuthApiKey
import sys
from pathlib import Path

# Fix import path
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.settings import get_config

from archive_src.interfaces.vector_store import VectorStoreInterface

class WeaviateStore(VectorStoreInterface):
    """Weaviate vector store implementation"""

    def __init__(self):
        self.config = get_config().database
        self.logger = logging.getLogger(__name__)
        
        if self.config.type != "weaviate":
            raise ValueError(f"Invalid database type: {self.config.type}. Expected 'weaviate'")
        
        # Initialize Weaviate client
        auth_config = AuthApiKey(api_key=self.config.api_key) if self.config.api_key else None
        
        self.client = weaviate.Client(
            url=f"http://{self.config.host}:{self.config.port}",
            auth_client_secret=auth_config,
            additional_headers={
                "X-OpenAI-Api-Key": self.config.api_key  # For OpenAI integration
            }
        )
        
        self._ensure_schema()
        
        self.logger.info(f"Initialized WeaviateStore")

    def _ensure_schema(self):
        """Ensure schema exists"""
        class_name = "LawCase"
        class_obj = {
            "class": class_name,
            "vectorizer": "text2vec-openai",
            "moduleConfig": {
                "text2vec-openai": {
                    "model": "ada",
                    "modelVersion": "002",
                    "type": "text"
                }
            },
            "properties": [
                {
                    "name": "text",
                    "dataType": ["text"],
                    "description": "The text content of the case"
                },
                {
                    "name": "case_number",
                    "dataType": ["string"],
                    "description": "Case number or docket number"
                },
                {
                    "name": "court",
                    "dataType": ["string"],
                    "description": "Court name"
                }
            ]
        }
        
        if not self.client.schema.exists(class_name):
            self.client.schema.create_class(class_obj)
            self.logger.info(f"Created schema class: {class_name}")

    def create_collection(self, name: str, dimension: int, metadata_schema: Dict[str, Any] = None):
        """Create a new class (Weaviate equivalent of collection)"""
        try:
            class_obj = {
                "class": name,
                "vectorizer": "none",  # We provide our own vectors
                "properties": metadata_schema or []
            }
            self.client.schema.create_class(class_obj)
            self.logger.info(f"Created class: {name}")
        except Exception as e:
            self.logger.error(f"Failed to create class {name}: {e}")
            raise

    def insert(self, vectors: List[List[float]], metadata: List[Dict[str, Any]], ids: List[str]):
        """Insert vectors with metadata"""
        if not all([vectors, metadata, ids]):
            raise ValueError("Vectors, metadata, and ids must be provided")
        
        if len(vectors) != len(metadata) != len(ids):
            raise ValueError("Vectors, metadata, and ids must have the same length")
        
        try:
            with self.client.batch as batch:
                for i, (vector, meta, id_) in enumerate(zip(vectors, metadata, ids)):
                    batch.add_data_object(
                        data_object=meta,
                        class_name="LawCase",
                        vector=vector,
                        uuid=id_
                    )
            
            self.logger.info(f"Inserted {len(ids)} vectors into Weaviate")
            
        except Exception as e:
            self.logger.error(f"Failed to insert vectors: {e}")
            raise

    def search(self, query_vector: List[float], k: int = 10, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search for similar vectors"""
        if not query_vector:
            raise ValueError("Query vector cannot be empty")
        
        try:
            # Build GraphQL query
            where_clause = ""
            if filters:
                where_conditions = []
                for key, value in filters.items():
                    if isinstance(value, list):
                        where_conditions.append(f'{key}: {{in: {value}}}')
                    else:
                        where_conditions.append(f'{key}: {{equal: "{value}"}}')
                where_clause = f'(where: {{operator: And, operands: [{", ".join(where_conditions)}]}})'
            
            query = f'''
            {{
                Get {{
                    LawCase(
                        nearVector: {{vector: {query_vector}}}
                        limit: {k}
                        {where_clause}
                    ) {{
                        _additional {{
                            id
                            distance
                            vector
                        }}
                        text
                        case_number
                        court
                    }}
                }}
            }}
            '''
            
            results = self.client.query.raw(query)
            
            # Format results
            formatted_results = []
            for case in results['data']['Get']['LawCase']:
                formatted_results.append({
                    'id': case['_additional']['id'],
                    'metadata': {k: v for k, v in case.items() if k != '_additional'},
                    'distance': case['_additional']['distance'],
                    'embedding': case['_additional']['vector'],
                    'score': 1 - case['_additional']['distance']
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
            for id_ in ids:
                self.client.data_object.delete(id_, class_name="LawCase")
            self.logger.info(f"Deleted {len(ids)} vectors from Weaviate")
            return True
        except Exception as e:
            self.logger.error(f"Delete failed: {e}")
            return False

    def update(self, ids: List[str], vectors: List[List[float]], metadata: List[Dict[str, Any]]):
        """Update existing vectors"""
        if len(ids) != len(vectors) != len(metadata):
            raise ValueError("IDs, vectors, and metadata must have the same length")
        
        try:
            for id_, vector, meta in zip(ids, vectors, metadata):
                self.client.data_object.update(
                    uuid=id_,
                    class_name="LawCase",
                    data_object=meta,
                    vector=vector
                )
            self.logger.info(f"Updated {len(ids)} vectors in Weaviate")
        except Exception as e:
            self.logger.error(f"Update failed: {e}")
            raise

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            stats = self.client.query.aggregate.over_all(
                class_name="LawCase",
                fields="meta { count }"
            )
            return {
                'vector_count': stats['data']['Aggregate']['LawCase'][0]['meta']['count'],
                'database_type': 'weaviate'
            }
        except Exception as e:
            self.logger.error(f"Failed to get stats: {e}")
            return {'error': str(e)}