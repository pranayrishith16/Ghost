# import logging
# import time
# from typing import Dict, Any, List, Optional
# from pathlib import Path
# from datetime import datetime

# from src.interfaces.document_processor import DocumentProcessorInterface
# from src.interfaces.chunker import ChunkerInterface
# from src.interfaces.embedder import EmbedderInterface
# from src.interfaces.vector_store import VectorStoreInterface
# from src.interfaces.llm_provider import LLMProviderInterface
# from src.interfaces.monitor import MonitorInterface
# from src.core.factory import (
#     DocumentProcessorFactory,
#     ChunkerFactory,
#     EmbedderFactory,
#     VectorStoreFactory,
#     LLMProviderFactory,
#     MonitorFactory
# )
# from src.config.settings import get_config
# from src.core.exceptions import PipelineError

# class RAGPipeline:
#     """
#     Main RAG pipeline orchestrator that coordinates all components.
#     This is the central nervous system of the Law RAG application.
#     """
    
#     def __init__(self):
#         self.config = get_config()
#         self.logger = logging.getLogger(__name__)
        
#         # Initialize components using factory pattern
#         self.document_processor = DocumentProcessorFactory.create()
#         self.chunker = ChunkerFactory.create()
#         self.embedder = EmbedderFactory.create()
#         self.vector_store = VectorStoreFactory.create()
#         self.llm_provider = LLMProviderFactory.create()
#         self.monitor = MonitorFactory.create()
        
#         self.logger.info("RAGPipeline initialized with all components")
    
#     def ingest_document(self, file_path: Path) -> Dict[str, Any]:
#         """
#         Process a single document through the entire ingestion pipeline.
#         Returns metadata about the processed document.
#         """
#         try:
#             start_time = time.time()
#             self.monitor.start_run(run_name=f"ingest_{file_path.stem}")
            
#             # 1. Document Processing
#             self.logger.info(f"Processing document: {file_path}")
#             document_data = self.document_processor.process_document(file_path)
            
#             # 2. Chunking
#             self.logger.info(f"Chunking document: {file_path}")
#             chunks = self.chunker.chunk_text(document_data['text'], document_data['metadata'])
            
#             # 3. Embedding
#             self.logger.info(f"Generating embeddings for {len(chunks)} chunks")
#             texts = [chunk['text'] for chunk in chunks]
#             embeddings = self.embedder.embed_batch(texts)
            
#             # 4. Vector Storage
#             self.logger.info(f"Storing {len(chunks)} chunks in vector database")
#             chunk_ids = [f"{file_path.stem}_{i}" for i in range(len(chunks))]
            
#             # Add document metadata to each chunk
#             for i, chunk in enumerate(chunks):
#                 chunk['metadata'].update({
#                     'document_id': file_path.stem,
#                     'document_path': str(file_path),
#                     'chunk_id': chunk_ids[i],
#                     'ingestion_timestamp': datetime.now().isoformat()
#                 })
            
#             self.vector_store.insert(
#                 vectors=embeddings,
#                 metadata=[chunk['metadata'] for chunk in chunks],
#                 ids=chunk_ids
#             )
            
#             # Log metrics
#             duration = time.time() - start_time
#             metrics = {
#                 'document_size_bytes': file_path.stat().st_size,
#                 'total_chunks': len(chunks),
#                 'processing_time_seconds': duration,
#                 'chunks_per_second': len(chunks) / duration if duration > 0 else 0,
#                 'avg_chunk_size_chars': sum(len(chunk['text']) for chunk in chunks) / len(chunks) if chunks else 0,
#                 'avg_chunk_size_words': sum(chunk['word_count'] for chunk in chunks) / len(chunks) if chunks else 0
#             }
            
#             self.monitor.log_metrics(metrics)
#             self.monitor.log_artifact(str(file_path), f"document_{file_path.stem}")
#             self.monitor.end_run()
            
#             result = {
#                 'success': True,
#                 'document_id': file_path.stem,
#                 'total_chunks': len(chunks),
#                 'processing_time': duration,
#                 'metrics': metrics,
#                 'metadata': document_data['metadata']
#             }
            
#             self.logger.info(f"Successfully ingested document: {file_path.stem}")
#             return result
            
#         except Exception as e:
#             self.logger.error(f"Failed to ingest document {file_path}: {e}")
#             self.monitor.log_metrics({'ingestion_failed': 1})
#             self.monitor.end_run()
#             raise PipelineError(f"Document ingestion failed: {e}")
    
#     def query(self, question: str, max_results: int = 10) -> Dict[str, Any]:
#         """
#         Process a query through the RAG pipeline.
#         Returns the answer and relevant context.
#         """
#         try:
#             start_time = time.time()
#             self.monitor.start_run(run_name=f"query_{int(time.time())}")
            
#             # 1. Generate query embedding
#             self.logger.info(f"Generating embedding for query: {question}")
#             query_embedding = self.embedder.embed_text(question)
            
#             # 2. Retrieve relevant chunks
#             self.logger.info(f"Retrieving relevant chunks for query")
#             results = self.vector_store.search(
#                 query_vector=query_embedding,
#                 k=max_results,
#                 filters=None  # Could add filters for court, date, etc.
#             )
            
#             # 3. Generate answer using LLM
#             self.logger.info(f"Generating answer using LLM")
#             context_chunks = [result['metadata']['text'] for result in results]
#             answer = self.llm_provider.generate_with_context(question, context_chunks)
            
#             # 4. Prepare response
#             duration = time.time() - start_time
#             response = {
#                 'question': question,
#                 'answer': answer,
#                 'context_chunks': [
#                     {
#                         'text': result['metadata']['text'],
#                         'score': result['score'],
#                         'document_id': result['metadata'].get('document_id'),
#                         'chunk_id': result['metadata'].get('chunk_id')
#                     }
#                     for result in results
#                 ],
#                 'processing_time': duration,
#                 'total_chunks_retrieved': len(results)
#             }
            
#             # Log metrics
#             metrics = {
#                 'query_processing_time': duration,
#                 'chunks_retrieved': len(results),
#                 'answer_length_chars': len(answer),
#                 'answer_length_words': len(answer.split())
#             }
            
#             self.monitor.log_metrics(metrics)
#             self.monitor.end_run()
            
#             return response
            
#         except Exception as e:
#             self.logger.error(f"Query processing failed: {e}")
#             self.monitor.log_metrics({'query_failed': 1})
#             self.monitor.end_run()
#             raise PipelineError(f"Query processing failed: {e}")
    
#     def batch_ingest(self, directory_path: Path) -> Dict[str, Any]:
#         """
#         Process all documents in a directory through the ingestion pipeline.
#         """
#         try:
#             if not directory_path.exists() or not directory_path.is_dir():
#                 raise PipelineError(f"Directory not found: {directory_path}")
            
#             results = []
#             total_files = 0
#             successful_files = 0
            
#             # Find all PDF files in directory and subdirectories
#             pdf_files = list(directory_path.rglob("*.pdf"))
#             total_files = len(pdf_files)
            
#             self.logger.info(f"Starting batch ingestion of {total_files} PDF files")
#             self.monitor.start_run(run_name=f"batch_ingest_{directory_path.name}")
            
#             for i, pdf_file in enumerate(pdf_files):
#                 try:
#                     self.logger.info(f"Processing file {i+1}/{total_files}: {pdf_file.name}")
#                     result = self.ingest_document(pdf_file)
#                     results.append(result)
#                     successful_files += 1
                    
#                 except Exception as e:
#                     self.logger.error(f"Failed to process {pdf_file}: {e}")
#                     results.append({
#                         'success': False,
#                         'file_path': str(pdf_file),
#                         'error': str(e)
#                     })
            
#             # Log batch metrics
#             metrics = {
#                 'total_files_processed': total_files,
#                 'successful_files': successful_files,
#                 'failed_files': total_files - successful_files,
#                 'success_rate': successful_files / total_files if total_files > 0 else 0
#             }
            
#             self.monitor.log_metrics(metrics)
#             self.monitor.end_run()
            
#             return {
#                 'batch_summary': metrics,
#                 'file_results': results
#             }
            
#         except Exception as e:
#             self.logger.error(f"Batch ingestion failed: {e}")
#             raise PipelineError(f"Batch ingestion failed: {e}")
    
#     def get_stats(self) -> Dict[str, Any]:
#         """Get statistics about the pipeline and vector store"""
#         try:
#             vector_stats = self.vector_store.get_stats()
#             embedder_info = self.embedder.get_model_info()
#             llm_info = self.llm_provider.get_model_info()
            
#             return {
#                 'vector_store': vector_stats,
#                 'embedder': embedder_info,
#                 'llm_provider': llm_info,
#                 'chunker_type': self.chunker.__class__.__name__,
#                 'document_processor_type': self.document_processor.__class__.__name__
#             }
            
#         except Exception as e:
#             self.logger.error(f"Failed to get pipeline stats: {e}")
#             raise PipelineError(f"Failed to get pipeline stats: {e}")