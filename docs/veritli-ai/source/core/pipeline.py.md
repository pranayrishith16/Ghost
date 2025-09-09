## Overview

This module implements the main Retrieval-Augmented Generation (RAG) pipeline that coordinates document processing, text chunking, embedding generation, and vector storage. It serves as the central orchestrator for transforming raw documents into searchable vector embeddings through a multi-stage processing workflow.

## 📦 Dependencies & Imports

## Standard Library

- **`json`** - JSON serialization for output file formatting
    
- **`logging`** - Comprehensive pipeline event and error logging
    
- **`datetime`** - Timestamping for processing operations and metadata
    
- **`pathlib.Path`** - Modern file system path handling and validation
    
- **`typing.Dict, Any, List`** - Type annotations for better code clarity

## Project Configuration

- [**`config.settings.get_config`**](settings.py.md) - Centralized configuration management
    
    - Loads chunking strategies, embedding providers, and pipeline settings
        

## Factory Dependencies

- [**`src.core.factory.DocumentProcessorFactory`**](factory.py.md) - Creates document processor instances
    
- [**`src.core.factory.ChunkingFactory`**](factory.py.md) - Instantiates text chunking strategies
    
- [**`src.core.factory.EmbedderFactory`**](factory.py.md) - Provides embedding generation services
    
- [**`src.core.factory.VectorStoreFactory`**](factory.py.md) - Creates vector storage backend connections

## 🏗️ Classes

## `RAGPipeline`

**Purpose:** Central orchestrator for the complete RAG document processing workflow

**Class Documentation:** "Main RAG pipeline that coordinates all components."

This class manages the entire pipeline from raw document ingestion through vector storage, coordinating multiple specialized components while providing comprehensive logging and error handling.

## Initialization: `__init__(self) -> None`

**Components Initialized:**

- **Configuration:** Loads settings via `get_config()`
    
- **Logger:** Sets up module-level logging with `__name__`
    
- **Document Processor:** Creates PDF processor using factory pattern
    
- **Text Chunker:** Instantiates chunking strategy from configuration
    
- **Embedder:** Initializes embedding provider from configuration
    
- **Vector Store:** Establishes Weaviate connection for chunk storage
    

**Factory Pattern Benefits:**

- Dynamic component creation based on configuration
    
- Easy testing with mock components
    
- Flexible provider switching without code changes

## 🟢 Public Methods

## `ingest_document(self, file_path: Path, run_id: str | None = None) -> Dict[str, Any]`

**Purpose:** Process a single document through the complete RAG pipeline

**Documentation:** "Process a single document through ingestion, chunking, and embedding."

**Parameters:**

- `file_path` (Path): Path to the document file to process
    
- `run_id` (str, optional): Optional tracking identifier for processing runs
    

**Three-Phase Processing:**

**Phase 1: Document Processing**

- Logs: `"Phase 1: Document processing"`
    
- Calls: `self.document_processor.process_document(file_path)`
    
- Extracts: Raw text content and document metadata
    

**Phase 2: Text Chunking**

- Logs: `"Phase 2: Text chunking"`
    
- Calls: `self.chunker.chunk_text(document_data["text"], metadata)`
    
- Validates: Chunks using `self.chunker.validate_chunks(chunks)`
    
- Raises: `ValueError` if chunk validation fails
    

**Phase 3: Embedding Generation**

- Extracts: Text from chunks into list format
    
- Generates: Batch embeddings via `self.embedder.embed_batch(texts)`
    
- Enriches: Chunks with embedding vectors and dimensions
    

**Returns Dictionary:**

- `file_path`: Original file path as string
    
- `chunks`: List of processed chunks with embeddings
    
- `processing_stats`: Statistics including total chunks and success status
    
- `document_metadata`: Extracted document metadata
    
- `timestamp`: Processing completion timestamp in ISO format
    
- `run_id`: Optional tracking identifier
    

**Error Handling:**

- Comprehensive try/catch with context logging
    
- Success logging: `"Successfully processed {file_path}: {len(chunks)} chunks"`
    
- Error logging: `"Failed to process document {file_path}: {e}"`
    
- Re-raises exceptions for caller handling
    

**Usage:**

python

```
pipeline = RAGPipeline() result = pipeline.ingest_document(Path("research_paper.pdf")) print(f"Generated {result['processing_stats']['total_chunks']} chunks")
```

## `batch_ingest(self, directory_path: Path, output_file: str = "chunks.jsonl") -> Dict[str, Any]`

**Purpose:** Process multiple PDF files in batch with comprehensive reporting

**Documentation:** "Process all PDFs in a directory and write chunks with embeddings to JSONL."

**Parameters:**

- `directory_path` (Path): Directory containing PDF files to process
    
- `output_file` (str): Output JSONL filename (default: "chunks.jsonl")
    

**Pre-Processing Validation:**

- Validates directory existence (raises `FileNotFoundError` if missing)
    
- Discovers PDFs using recursive search: `directory_path.rglob("*.pdf")`
    
- Validates file count (raises `FileNotFoundError` if no PDFs found)
    

**Batch Processing Workflow:**

**1. Initialization Phase:**

- Creates tracking counters: `successful_files`, `failed_files`, `total_chunks`
    
- Initializes collections for results and vector store data
    
- Opens output file with UTF-8 encoding
    

**2. Individual File Processing:**

- Iterates through each PDF with progress tracking
    
- Calls `ingest_document()` for each file
    
- Updates success counters and accumulates chunk totals
    
- Enhances chunks with batch metadata:
    
    - `source_file`: Original PDF file path
        
    - `processed_at`: Current timestamp
        

**3. Output Generation:**

- Writes each chunk as JSONL: `json.dumps(chunk_with_metadata, ensure_ascii=False)`
    
- Maintains collection for vector store bulk insertion
    
- Progress logging: `"Progress: {i+1}/{total_files} - {pdf_file.name} -> {len(chunks)} chunks"`
    

**4. Vector Store Integration:**

- Bulk insertion: `self.vector_store.add_documents(all_chunks_for_vector_store)`
    
- Success logging: `"Added {len(all_chunks_for_vector_store)} chunks to vector store"`
    
- Graceful error handling for vector store failures
    

**Error Handling:**

- Individual file failures don't halt batch processing
    
- Failed files logged as warnings: `"Skipping invalid PDF {pdf_file}: {e}"`
    
- Detailed error tracking in results with status and error messages
    
- Continues processing remaining files after failures
    

**Returns Dictionary:**

- `total_files`: Total PDF files discovered
    
- `successful_files`: Successfully processed file count
    
- `failed_files`: Failed processing file count
    
- `total_chunks`: Total chunks generated across all files
    
- `success_rate`: Processing success percentage
    
- `output_file`: Path to generated JSONL file
    
- `detailed_results`: Per-file processing results with status
    
- `completed_at`: Batch completion timestamp
    

**Comprehensive Logging:**

- Start: `"Starting batch ingestion from: {directory_path}"`
    
- Progress: Per-file processing updates with chunk counts
    
- Vector storage: Bulk insertion confirmations
    
- Completion: `"Batch ingestion completed: {successful_files}/{total_files} files successful, {total_chunks} chunks created"`
    

**Usage:**

python

`pipeline = RAGPipeline() summary = pipeline.batch_ingest(     directory_path=Path("./research_documents"),     output_file="research_chunks.jsonl" ) print(f"Success rate: {summary['success_rate']:.1f}%") print(f"Total chunks: {summary['total_chunks']}")`


## 🔄 Processing Architecture

## Pipeline Flow

text

`Raw PDF → Document Processor → Text Chunker → Embedder → Vector Store    ↓            ↓                  ↓            ↓           ↓ PDF File   Text + Metadata   Validated    Vector      Searchable                               Chunks     Embeddings     Index`

## Component Integration

- **Factory Pattern:** Configuration-driven component instantiation
    
- **Error Isolation:** Individual file failures don't halt batch operations
    
- **Bulk Operations:** Optimized vector store insertions for performance
    
- **Comprehensive Logging:** Full audit trail of processing events
    

## 📊 Output Formats

## JSONL Chunk Structure

Each line contains a JSON object with:

- `text`: Chunk text content
    
- `embedding`: Vector embedding array
    
- `embedding_dim`: Embedding vector dimensions
    
- `source_file`: Original PDF file path
    
- `processed_at`: Processing timestamp
    
- Additional document metadata fields
    

## ⚠️ Error Handling & Validation

## Directory-Level Validation

- **Missing Directory:** Raises `FileNotFoundError` with descriptive message
    
- **No PDF Files:** Raises `FileNotFoundError` when directory contains no PDFs
    
- **File Access:** Handles permission and encoding issues gracefully
    

## Processing-Level Error Management

- **Chunk Validation:** Raises `ValueError` for invalid chunk structures
    
- **Embedding Failures:** Logged with file context, processing continues
    
- **Vector Store Errors:** Logged but don't halt batch processing
    
- **Individual File Failures:** Tracked but don't stop batch operations
    

## 🔗 Cross-References & Dependencies

## Required Factory Components

- **[DocumentProcessorFactory](https://www.perplexity.ai/core/factory.md#documentprocessorfactory)** - PDF processor creation
    
- **[ChunkingFactory](https://www.perplexity.ai/core/factory.md#chunkingfactory)** - Text chunking strategies
    
- **[EmbedderFactory](https://www.perplexity.ai/core/factory.md#embedderfactory)** - Embedding generation services
    
- **[VectorStoreFactory](https://www.perplexity.ai/core/factory.md#vectorstorefactory)** - Vector storage backends
    

## Configuration Requirements

- **Chunking Strategy:** Accessed via `config.chunking.strategy`
    
- **Embedding Provider:** Accessed via `config.embedding.provider`
    
- **Vector Store:** Currently hardcoded to 'weaviate'
    

## Related Components

- **[Configuration Settings](https://www.perplexity.ai/config/settings.md)** - Pipeline configuration
    
- **[PDF Extractor](https://www.perplexity.ai/extractors/pdf_extractor.md)** - Document processing implementation
    
- **[Vector Store Interface](https://www.perplexity.ai/storage/vector_store.md)** - Storage backend