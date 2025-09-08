import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from config.settings import get_config
from src.core.factory import (
    DocumentProcessorFactory,
    ChunkingFactory,
    EmbedderFactory,
    VectorStoreFactory
)

class RAGPipeline:
    """Main RAG pipeline that coordinates all components."""

    def __init__(self) -> None:
        self.config = get_config()
        self.logger = logging.getLogger(__name__)

        # Initialize components via factories
        self.document_processor = DocumentProcessorFactory.create("pdf")
        self.chunker = ChunkingFactory.create(self.config.chunking.strategy)
        self.embedder = EmbedderFactory.create(self.config.embedding.provider)
        self.vector_store = VectorStoreFactory.create('weaviate')

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
            for i, ch in enumerate(chunks):
                vec = embeddings[i]
                ch["embedding"] = vec
                ch["embedding_dim"] = len(vec)

            result = {
                "file_path": str(file_path),
                "chunks": chunks,
                "processing_stats": {
                    "total_chunks": len(chunks),
                    "success": True,
                },
                "document_metadata": document_data.get("metadata", {}),
                "timestamp": datetime.now().isoformat(),
                "run_id": run_id,
            }
            self.logger.info(f"Successfully processed {file_path}: {len(chunks)} chunks")
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
        
        # Add all chunks to vector store
        if all_chunks_for_vector_store:
            try:
                self.vector_store.add_documents(all_chunks_for_vector_store)
                self.logger.info(f"Added {len(all_chunks_for_vector_store)} chunks to vector store")
            except Exception as e:
                self.logger.error(f"Failed to add chunks to vector store: {e}")

        # Log the output file as an artifact
        # try:
        #     if Path(output_file).exists():
        #         self.monitor.log_artifact(output_file, "processed_chunks")
        # except Exception as e:
        #     self.logger.warning(f"Failed to log artifact {output_file}: {e}")

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

        # Log batch metrics
        # try:
        #     self.monitor.log_metrics(
        #         {
        #             "total_files": total_files,
        #             "successful_files": successful_files,
        #             "failed_files": failed_files,
        #             "total_chunks": total_chunks,
        #             "success_rate": batch_summary["success_rate"],
        #         }
        #     )
        # except Exception as e:
        #     self.logger.warning(f"Failed to log batch metrics: {e}")

        self.logger.info(
            f"Batch ingestion completed: {successful_files}/{total_files} files successful, {total_chunks} chunks created"
        )
        return batch_summary
