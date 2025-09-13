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
    LLMProviderFactory,
    MonitoringFactory
)

# Import your custom components
from src.retrieval.basic_retrieval import BasicRetriever
from src.retrieval.hybrid_retrieval import HybridRetriever
from src.retrieval.rerank_retrieval import RerankRetriever
from src.generation.rag_generator import RAGGenerator

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

        #initialize your custom retrievers
        self.retrievers = {
            'basic': BasicRetriever(self.vector_store,self.embedder),
            'hybrid':HybridRetriever(self.vector_store,self.embedder),
            'rerank':RerankRetriever(self.vector_store,self.embedder)
        }

        #initializing custom generator
        self.generators = {
            strategy: RAGGenerator(retriever,self.llm_provider)
            for strategy,retriever in self.retrievers.items()
        }

        # Initialize monitor via factory for modular monitoring
        monitor_type = (
            self.config.monitoring.type if self.config.monitoring else None
        )
        if monitor_type:
            self.monitor = MonitoringFactory.create(
                monitor_type=monitor_type,
                experiment_name=self.config.monitoring.experiment_name,
                tracking_uri=self.config.monitoring.tracking_uri,
            )
        else:
            self.monitor = None

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
    
    def query(
            self, 
            question:str, 
            retrieval_strategy:str = 'basic',
            query_type:str='legal_analysis',
            max_results:int = 10, 
            filters:Dict[str,Any] = None) -> Dict[str,Any]:
        """
        process a query through the RAG pipeline
        returns the answer and relevant context
        """
        run_id = None
        try:
            
            # Validate retrieval strategy
            if retrieval_strategy not in self.generators:
                available = list(self.generators.keys())
                raise ValueError(f"Unknown retrieval strategy '{retrieval_strategy}'. Available: {available}")
            
            if self.monitor:
                params = {
                    "question": question,
                    "retrieval_strategy": retrieval_strategy,
                    "query_type": query_type,
                    "max_results": max_results,
                }
                run_id = self.monitor.start_run(
                    run_name=f"Query-{datetime.now().isoformat()}",
                    params=params,
                )
            
            # Use YOUR custom RAGGenerator (not basic LLM call)
            generator = self.generators[retrieval_strategy]
            response = generator.generate_response(
                query=question,
                query_type=query_type,
                k=max_results,
                filters=filters
            )

            if self.monitor:
                metrics = {
                    "confidence_score": response.get("confidence_score", 0.0),
                    "sources_used": len(response.get("sources", [])),
                    "generation_successful": 1.0,
                }
                self.monitor.log_metrics(metrics)
                self.monitor.log_text(text=response.get("generated_text", ""), name="GeneratedAnswer")
                self.monitor.end_run(run_id)
                run_id = None

            # Enhance response with pipeline metadata
            enhanced_response = {
                **response,
                "pipeline_metadata": {
                    "retrieval_strategy": retrieval_strategy,
                    "query_type": query_type,
                    "pipeline_version": "2.0.0",
                    "components_used": {
                        "retriever": self.retrievers[retrieval_strategy].__class__.__name__,
                        "generator": "RAGGenerator",
                        "embedder": self.embedder.__class__.__name__,
                        "llm_provider": self.llm_provider.__class__.__name__
                    }
                }
            }

            # Log comprehensive metrics
            pipeline_metrics = {
                "retrieval_strategy": retrieval_strategy,
                "query_type": query_type,
                "confidence_score": response.get("confidence_score", 0.0),
                "sources_used": len(response.get("sources", [])),
                "generation_successful": True
            }
            
            return enhanced_response

        except Exception as e:
            self.logger.error(f"Pipeline query processing failed: {e}")
            if self.monitor and run_id:
                self.monitor.log_text(text=str(e), name="QueryError")
                self.monitor.end_run(run_id)
            raise
    
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