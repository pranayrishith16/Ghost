# src/vector_store/weaviate.py
import logging
from typing import List, Dict, Any, Optional

import numpy as np
import weaviate
import weaviate.classes as wvc
from weaviate.classes.config import Property, DataType, Configure

from contextlib import contextmanager

class WeaviateStore:
    """Weaviate implementation of vector storage for legal docs"""

    def __init__(
        self,
        collection_name: str = "LegalDocument",
        embedder=None,
        client: Optional[weaviate.WeaviateClient] = None,
    ):
        self.logger = logging.getLogger(__name__)
        self.collection_name = collection_name
        self.embedder = embedder
        self.client = client or weaviate.connect_to_local()
        self._ensure_collection()

    def __exit__(self,exc_type,exc_val, exc_tb):
        self.close()

    @contextmanager
    def _ensure_collection(self) -> None:
        """Create the collection if it doesn't exist, using self-provided vectors."""
        try:
            if not self.client.collections.exists(self.collection_name):
                self.client.collections.create(
                    name=self.collection_name,
                    # Bring-your-own vectors (single unnamed vector)
                    vector_config=Configure.Vectors.self_provided(),
                    properties=[
                        Property(
                            name="text",
                            data_type=DataType.TEXT,
                            description="The chunk text content",
                        ),
                        Property(
                            name="source_file",
                            data_type=DataType.TEXT,
                            description="Source PDF file path",
                        ),
                        Property(
                            name="chunk_index",
                            data_type=DataType.INT,
                            description="Chunk index within the document",
                        ),
                        Property(
                            name="word_count",
                            data_type=DataType.INT,
                            description="Number of words in chunk",
                        ),
                        Property(
                            name="char_count",
                            data_type=DataType.INT,
                            description="Number of characters in chunk",
                        ),
                        Property(
                            name="processed_at",
                            data_type=DataType.TEXT,
                            description="Processing timestamp",
                        ),
                        Property(
                            name="file_size",
                            data_type=DataType.INT,
                            description="Size of the file",
                        ),
                        Property(
                            name="file_pages",
                            data_type=DataType.INT,
                            description="Number of pages",
                        ),
                    ],
                )
                self.logger.info(f"Created collection '{self.collection_name}'")
            else:
                self.logger.info(f"Collection '{self.collection_name}' already exists")
        except Exception as e:
            self.logger.error(f"Failed to create collection: {e}")
            raise

    def _validate_embedding(self, chunk: Dict[str, Any]) -> Optional[List[float]]:
        """Validate and normalize embedding vector from chunk['embedding']."""
        vector = chunk.get("embedding")
        if vector is None:
            self.logger.warning(
                "Chunk missing embedding, skipping: %s",
                str(chunk.get("text", ""))[:50] + "..."
            )
            return None

        # Convert numpy arrays to lists if needed
        if isinstance(vector, np.ndarray):
            vector = vector.tolist()

        # Ensure list of numbers
        if not isinstance(vector, list) or not all(isinstance(x, (int, float)) for x in vector):
            self.logger.warning("Invalid embedding format, skipping chunk")
            return None

        return vector

    def add_documents(self, chunks: List[Dict[str, Any]]) -> None:
        """Add document chunks with embeddings to Weaviate."""
        try:
            collection = self.client.collections.get(self.collection_name)
            batch_size = 100
            successful = 0

            for i in range(0, len(chunks), batch_size):
                batch_chunks = chunks[i : i + batch_size]
                with collection.batch.dynamic() as batch:
                    for chunk in batch_chunks:
                        vector = self._validate_embedding(chunk)
                        if vector is None:
                            continue

                        props = {
                            "text": str(chunk.get("text", "")),
                            "source_file": str(
                                chunk.get("filename", chunk.get("source_file", ""))
                            ),
                            "chunk_index": int(chunk.get("chunk_index", 0)),
                            "word_count": int(chunk.get("word_count", 0)),
                            "char_count": int(chunk.get("char_count", 0)),
                            "processed_at": str(chunk.get("processed_at", "")),
                            "file_size": int(chunk.get("file_size", 0)),
                            "file_pages": int(chunk.get("pages", chunk.get("file_pages", 0))),
                        }

                        # Optional: pass a stable uuid if present
                        uuid = chunk.get("id")

                        batch.add_object(
                            properties=props,
                            vector=vector,
                            uuid=uuid,
                        )
                        successful += 1

                self.logger.info("Processed batch %d (%d items)", (i // batch_size) + 1, len(batch_chunks))

            self.logger.info("Successfully added %d chunks to Weaviate", successful)
        except Exception as e:
            self.logger.error(f"Failed to add documents to Weaviate: {e}")
            raise

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents using a text query by embedding it first."""
        if not self.embedder:
            raise ValueError("Embedder not provided. Cannot embed query.")
        try:
            qv = self.embedder.embed_text(query)
            return self.search_by_vector(qv, limit=limit)
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            raise

    def search_by_vector(self, query_vector: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        """Search using a pre-computed vector."""
        try:
            collection = self.client.collections.get(self.collection_name)
            response = collection.query.near_vector(
                near_vector=query_vector,
                limit=limit,
                return_metadata=wvc.query.MetadataQuery(distance=True),
            )

            results: List[Dict[str, Any]] = []
            for obj in response.objects:
                props = obj.properties or {}
                results.append(
                    {
                        "text": props.get("text", ""),
                        "source_file": props.get("source_file", ""),
                        "chunk_index": props.get("chunk_index", 0),
                        "word_count": props.get("word_count", 0),
                        "char_count": props.get("char_count", 0),
                        "processed_at": props.get("processed_at", ""),
                        "distance": getattr(obj.metadata, "distance", None),
                    }
                )
            return results
        except Exception as e:
            self.logger.error(f"Vector search failed: {e}")
            raise

    def search_with_filter(
        self,
        query: str,
        filters: Dict[str, Any],
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Search with metadata filters (e.g., by source_file)."""
        if not self.embedder:
            raise ValueError("Embedder not provided. Cannot embed query.")
        try:
            qv = self.embedder.embed_text(query)
            collection = self.client.collections.get(self.collection_name)

            where_filter = None
            if "source_file" in filters:
                where_filter = wvc.query.Filter.by_property("source_file").equal(filters["source_file"])

            response = collection.query.near_vector(
                near_vector=qv,
                limit=limit,
                where=where_filter,
                return_metadata=wvc.query.MetadataQuery(distance=True),
            )

            results: List[Dict[str, Any]] = []
            for obj in response.objects:
                props = obj.properties or {}
                results.append(
                    {
                        "text": props.get("text", ""),
                        "source_file": props.get("source_file", ""),
                        "chunk_index": props.get("chunk_index", 0),
                        "word_count": props.get("word_count", 0),
                        "char_count": props.get("char_count", 0),
                        "processed_at": props.get("processed_at", ""),
                        "distance": getattr(obj.metadata, "distance", None),
                    }
                )
            return results
        except Exception as e:
            self.logger.error(f"Filtered search failed: {e}")
            raise

    def delete_by_source(self, source_file: str) -> None:
        """Delete all chunks from a specific source file."""
        try:
            collection = self.client.collections.get(self.collection_name)
            collection.data.delete_many(
                where=wvc.query.Filter.by_property("source_file").equal(source_file)
            )
            self.logger.info("Deleted all chunks from source: %s", source_file)
        except Exception as e:
            self.logger.error(f"Failed to delete chunks from {source_file}: {e}")
            raise

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get basic statistics about the collection."""
        try:
            collection = self.client.collections.get(self.collection_name)
            total = collection.aggregate.over_all(total_count=True)
            grouped = collection.aggregate.over_all(group_by="source_file")
            return {
                "total_chunks": total.total_count,
                "unique_files": len(grouped.groups) if getattr(grouped, "groups", None) else 0,
                "collection_name": self.collection_name,
            }
        except Exception as e:
            self.logger.error(f"Failed to get collection stats: {e}")
            return {"total_chunks": 0, "unique_files": 0, "collection_name": self.collection_name}

    def close(self):
        """Close the Weaviate client connection."""
        if hasattr(self, "client") and self.client:
            self.client.close()
