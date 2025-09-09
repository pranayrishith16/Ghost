import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from unittest import result

from blinker import ANY
from cycler import L

from config.settings import get_config
from src.core.factory import (
    DocumentProcessorFactory,
    ChunkingFactory,
    EmbedderFactory,
    VectorStoreFactory,
    LLMProviderFactory
)

# Import your custom components
from src.retrieval.basic_retrieval import BasicRetriever
from src.retrieval.hybrid_retrieval import HybridRetriever
from src.retrieval.rerank_retrieval import RerankRetriever

class RAGPipeline:
    """Main RAG pipeline that coordinates all components."""

    def __init__(self) -> None:
        self.config = get_config()
        self.logger = logging.getLogger(__name__)

        # Initialize components via factories
        self.document_processor = DocumentProcessorFactory.create("pdf")
        self.chunker = ChunkingFactory.create(self.config.chunking.strategy)
        self.embedder = EmbedderFactory.create(self.config.embedding.provider)
        self.vector_store = VectorStoreFactory.create(
            self.config.vector_store.provider or 'weaviate'
        )
        self.llm_provider = LLMProviderFactory.create(
            self.config.llm.provider or 'openrouter'
        )

    def ingest_document(self, file_path: Path, run_id: str | None = None) -> Dict[str, Any]:
        """Process a single document through ingestion, chunking, and embedding."""
        try:
            # 1. Document processing
            self.logger.info("Phase 1: Document processing")
            document_data = self.document_processor.process_document(file_path)

            # 2. Chunking
            self.logger.info("Phase 2: Text chunking")
            chunks = self.chunker.chunk_text(
                document_data["text"], document_data.get("metadata", {})
            )

            if not self.chunker.validate_chunks(chunks):
                raise ValueError("Chunk validation failed")

            # 3. Embedding
            texts = [ch["text"] for ch in chunks]
            embeddings = self.embedder.embed_batch(texts)
            
            # enhance chunks with embedding and document metadata
            chunks_ids = [f"{file_path.stem}_{i}" for i in range(len(chunks))]
            enhanced_chunks = []

            for i,chunk in enumerate(chunks):
                enhanced_chunk = {
                    **chunk,
                    "embedding":embeddings[i],
                    "embedding_dim":len(embeddings[i]),
                    "chunk_id": chunks_ids[i],
                    "document_id": file_path.stem,
                    "document_path": str(file_path),
                    "ingestion_timestamp": datetime.now().isoformat(),
                }
                enhanced_chunks.append(enhanced_chunk)

            #4. store in vector database
            self.vector_store.add_documents(enhanced_chunks)

            result = {
                "file_path": str(file_path),
                "document_id": file_path.stem,
                "chunks": enhanced_chunks,
                "processing_stats": {
                    "total_chunks": len(chunks),
                    "success": True,
                },
                "document_metadata": document_data.get("metadata", {}),
                "timestamp": datetime.now().isoformat(),
                "run_id": run_id,
            }
        
            return result

        except Exception as e:
            self.logger.error(f"Failed to process document {file_path}: {e}")
            raise

    def batch_ingest(self, directory_path: Path, output_file: str = "chunks.jsonl") -> Dict[str, Any]:
        """Process all PDFs in a directory and write chunks with embeddings to JSONL."""
        if not directory_path.exists():
            raise FileNotFoundError(f"The directory {directory_path} does not exist")

        self.logger.info(f"Starting batch ingestion from: {directory_path}")
        pdf_files = list(directory_path.rglob("*.pdf"))
        total_files = len(pdf_files)
        if total_files == 0:
            raise FileNotFoundError(f"No PDF files found in {directory_path}")

        all_chunks_for_vector_store = []

        results: List[Dict[str, Any]] = []
        successful_files = 0
        failed_files = 0
        total_chunks = 0

        with open(output_file, "w", encoding="utf-8") as f_out:
            for i, pdf_file in enumerate(pdf_files):
                try:
                    result = self.ingest_document(pdf_file)
                    chunks = result["chunks"]
                    successful_files += 1
                    total_chunks += len(chunks)

                    for chunk in chunks:
                        chunk_with_metadata = {
                            **chunk,
                            "source_file": str(pdf_file),
                            "processed_at": datetime.now().isoformat(),
                        }
                        f_out.write(json.dumps(chunk_with_metadata, ensure_ascii=False) + "\n")

                        all_chunks_for_vector_store.append(chunk_with_metadata)

                    results.append(
                        {
                            "file": str(pdf_file),
                            "status": "success",
                            "chunks": len(chunks),
                        }
                    )
                    self.logger.info(
                        f"Progress: {i + 1}/{total_files} - {pdf_file.name} -> {len(chunks)} chunks with embeddings"
                    )
                except Exception as e:
                    failed_files += 1
                    results.append({"file": str(pdf_file), "status": "failed", "error": str(e)})
                    self.logger.warning(f"Skipping invalid PDF {pdf_file}: {e}")
                    continue

        batch_summary = {
            "total_files": total_files,
            "successful_files": successful_files,
            "failed_files": failed_files,
            "total_chunks": total_chunks,
            "success_rate": (successful_files / total_files) * 100 if total_files > 0 else 0.0,
            "output_file": output_file,
            "detailed_results": results,
            "completed_at": datetime.now().isoformat(),
        }


        self.logger.info(
            f"Batch ingestion completed: {successful_files}/{total_files} files successful, {total_chunks} chunks created"
        )
        return batch_summary
    
    def query(self, question:str, max_results:int = 10, filters:Dict[str,Any] = None) -> Dict[str,Any]:
        """
        process a query through the RAG pipeline
        returns the answer and relevant context
        """

        #1. generate embedding
        query_embedding = self.embedder.embed_text(question)

        #2. retrieve relevant chunks
        search_results = self.vector_store.search_by_vector(
            query_vector=query_embedding,
            limit=max_results,
        )

        if not search_results:
            return {
                "question": question,
                    "answer": "I couldn't find any relevant information to answer your question.",
                    "context_chunks": [],
                    "total_chunks_retrieved": 0,
            }
        
        #3. Generate answer using LLM
        context_text = [result['text'] for result in search_results]
        answer = self.llm_provider.generate_with_context(question,context_text)

        response = {
                "question": question,
                "answer": answer,
                "context_chunks": [
                    {
                        "text": result["text"],
                        "score": result.get("score", 0.0),
                        "document_id": result.get("document_id"),
                        "chunk_id": result.get("chunk_id"),
                        "source_file": result.get("source_file")
                    }
                    for result in search_results
                ],
                "total_chunks_retrieved": len(search_results),
                "filters_applied": filters or {}
            }
        
        return response
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the pipeline and all components."""
        try:
            return {
                "vector_store": self.vector_store.get_stats(),
                "embedder": {
                    "model_info": self.embedder.get_model_info(),
                    "embedding_dim": getattr(self.embedder, 'embedding_dim', None)
                },
                "llm_provider": self.llm_provider.get_model_info(),
                "components": {
                    "chunker_type": self.chunker.__class__.__name__,
                    "document_processor_type": self.document_processor.__class__.__name__,
                    "chunking_strategy": getattr(self.config.chunking, 'strategy', None),
                    "embedding_provider": getattr(self.config.embedding, 'provider', None),
                    "llm_provider": getattr(self.config.llm, 'provider', None)
                },
                "pipeline_info": {
                    "version": "1.0.0",
                    "initialized_at": datetime.now().isoformat(),
                    "supports_batch_ingestion": True,
                    "supports_query": True,
                    "supports_monitoring": True
                }
            }
        except Exception as e:
            self.logger.error(f"Failed to get pipeline stats: {e}")
            raise Exception(f"Failed to get pipeline stats: {e}")

    def health_check(self) -> Dict[str, Any]:
        """Perform a health check on all pipeline components."""
        health_status = {"overall": "healthy", "components": {}}
        
        components = {
            "document_processor": self.document_processor,
            "chunker": self.chunker,
            "embedder": self.embedder,
            "vector_store": self.vector_store,
            "llm_provider": self.llm_provider,
            "monitor": self.monitor
        }
        
        for name, component in components.items():
            try:
                if hasattr(component, 'health_check'):
                    status = component.health_check()
                else:
                    # Basic connectivity check
                    status = {"status": "healthy", "message": "Component accessible"}
                
                health_status["components"][name] = status
                
                if status.get("status") != "healthy":
                    health_status["overall"] = "degraded"
                    
            except Exception as e:
                health_status["components"][name] = {
                    "status": "unhealthy", 
                    "error": str(e)
                }
                health_status["overall"] = "unhealthy"
        
        health_status["timestamp"] = datetime.now().isoformat()
        return health_status

    def reset_pipeline(self) -> Dict[str, Any]:
        """Reset the pipeline state (clear vector store, reset monitoring)."""
        try:
            self.logger.info("Resetting pipeline state...")
            
            # Clear vector store
            if hasattr(self.vector_store, 'clear'):
                self.vector_store.clear()
            
            # Reset monitoring
            if hasattr(self.monitor, 'reset'):
                self.monitor.reset()
            
            return {
                "status": "success",
                "message": "Pipeline reset completed",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Pipeline reset failed: {e}")
            raise Exception(f"Pipeline reset failed: {e}")