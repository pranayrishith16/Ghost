## Overview

This module implements the Factory Pattern for creating instances of various RAG system components. It provides centralized, type-based instantiation of document processors, chunkers, embedders, vector stores, retrievers, and generators, enabling flexible configuration and loose coupling between components.

## 📦 Dependencies & Imports

## Interface Dependencies

- [**`src.generation.rag_generator.RAGGenerator`**](rag_generator.py.md) - Main RAG generation component
    
- [**`src.interfaces.llm_provider_interface`**](llm_provider_interface.py.md) - LLM provider abstraction
    
- [**`src.interfaces.document_processing_interface.DocumentProcessorInterface`**](Document_Processor_Interface.py.md) - Document processing contract
    
- [**`src.interfaces.chunking_interface.ChunkingInterface`** ](chunking_interface.py.md)- Text chunking contract
    
- [**`src.interfaces.monitor.MonitorInterface`**](monitor_interface.py.md) - Monitoring and logging contract
    
- [**`src.interfaces.embedder.EmbedderInterface`**](embedder_interface.py.md) - Embedding generation contract
    
- [**`src.interfaces.vector_store_interface.VectorStoreInterface`**](vector_store_interface.py.md) - Vector storage contract
    
- [**`src.interfaces.retriever_interface.RetrieverInterface`**](source/interface/retriever_interface.py.md) - Document retrieval contract
    

## Concrete Implementation Dependencies

- [**`src.document_processor.pdf_extractor.PDFExtractor`**](PDF_Extractor.py.md) - PDF document processor
    
- [**`src.chunking.legal_chunker.LegalChunker`**](legal_chunker.py.md) - Legal document chunking strategy
    
- [**`src.embedder.sentence_transformer_embedder.SentenceTransformersEmbedder`**](sentence_transformer_embedder.py.md) - /Sentence embedding provider
    
- [**`src.vector_store.weaviate.WeaviateStore`**](weaviate.py.md) - Weaviate vector database implementation
    
- [**`src.retrieval.basic_retrieval.BasicRetriever`**](basic_retrieval.py.md) - Basic similarity retrieval
    
- [**`src.retrieval.hybrid_retrieval.HybridRetriever`**](hybrid_retrieval.py.md) - Hybrid semantic/keyword retrieval
    
- [**`src.retrieval.rerank_retrieval.RerankRetriever`**](rerank_retrieval.py.md) - Re-ranking retrieval strategy

## 🏗️ Classes

## `NoOpMonitor`

**Purpose:** No-operation monitoring implementation for development/testing

**Inherits from:** `MonitorInterface`

This class provides a placeholder monitoring implementation that performs no actual logging operations, useful for development environments or when monitoring is disabled.

## 🟢 Public Methods

## `log_metrics(self, metrics, step=None)`

**Purpose:** No-operation metrics logging

**Parameters:**

- `metrics`: Metrics data (ignored)
    
- `step` (optional): Step number (ignored)
    

**Implementation:** `pass` - Does nothing

## `log_artifact(self, path, artifact_path=None)`

**Purpose:** No-operation artifact logging

**Parameters:**

- `path`: Artifact file path (ignored)
    
- `artifact_path` (optional): Destination path (ignored)
    

**Implementation:** `pass` - Does nothing

## `DocumentProcessorFactory`

**Purpose:** Factory for creating document processor instances

## 🟢 Static Methods

## `create(processor_type=None) -> DocumentProcessorInterface`

**Purpose:** Create document processor based on type specification

**Parameters:**

- `processor_type` (str, optional): Type of processor to create
    

**Supported Types:**

- `'pdf'`: Returns `PDFExtractor()` instance for PDF document processing
    

**Returns:**

- `DocumentProcessorInterface`: Configured document processor instance
    

**Error Handling:**

- Raises `Exception` with message `'The document is not pdf'` for unsupported types
    

**Usage:**

python

`processor = DocumentProcessorFactory.create('pdf') result = processor.process_document(Path("document.pdf"))`

## `ChunkingFactory`

**Purpose:** Factory for creating text chunking strategy instances

## 🟢 Static Methods

## `create(chunker_type=None) -> ChunkingInterface`

**Purpose:** Create text chunker based on strategy type

**Parameters:**

- `chunker_type` (str, optional): Type of chunker to create
    

**Supported Types:**

- `'legal'`: Returns `LegalChunker()` instance for legal document chunking
    

**Returns:**

- `ChunkingInterface`: Configured chunking strategy instance
    

**Error Handling:**

- Raises `Exception` with message `'Chunker not working'` for unsupported types
    

**Usage:**

python

`chunker = ChunkingFactory.create('legal') chunks = chunker.chunk_text(text_content, metadata)`

## `MonitoringFactory`

**Purpose:** Factory for creating monitoring component instances

## 🟢 Static Methods

## `create(monitor_type=None) -> MonitorInterface`

**Purpose:** Create monitoring interface instance

**Parameters:**

- `monitor_type` (str, optional): Type of monitor (currently ignored)
    

**Returns:**

- `MonitorInterface`: Always returns `NoOpMonitor()` instance
    

**Implementation Note:** Currently hardcoded to return no-operation monitor, replacing MLflow functionality

**Usage:**

python

`monitor = MonitoringFactory.create() monitor.log_metrics({"accuracy": 0.95})  # No-op`

## `EmbedderFactory`

**Purpose:** Factory for creating embedding generation instances

## 🟢 Static Methods

## `create(embedder_type=None) -> EmbedderInterface`

**Purpose:** Create embedder based on provider type

**Parameters:**

- `embedder_type` (str, optional): Type of embedder to create
    

**Supported Types:**

- `'sentence_transformers'`: Returns `SentenceTransformersEmbedder()` instance
    

**Returns:**

- `EmbedderInterface`: Configured embedding provider instance
    

**Error Handling:**

- Raises `Exception` with message `'Sentence transformers not working'` for unsupported types
    

**Usage:**

python

`embedder = EmbedderFactory.create('sentence_transformers') embeddings = embedder.embed_batch(text_chunks)`

## `VectorStoreFactory`

**Purpose:** Factory for creating vector storage backend instances

**Documentation:** "Factory for creating vector stores"

## 🟢 Static Methods

## `create(store_type: str = "weaviate") -> VectorStoreInterface`

**Purpose:** Create vector store instance based on backend type

**Parameters:**

- `store_type` (str): Type of vector store (default: "weaviate")
    

**Supported Types:**

- `"weaviate"`: Returns `WeaviateStore()` instance for Weaviate database
    

**Returns:**

- `VectorStoreInterface`: Configured vector storage backend
    

**Error Handling:**

- Raises `ValueError` with message `"Unsupported vector store type: {store_type}"` for unsupported backends
    

**Usage:**

python

`vector_store = VectorStoreFactory.create("weaviate") vector_store.add_documents(chunks_with_embeddings)`

## `RetrieverFactory`

**Purpose:** Factory for creating document retrieval strategy instances

**Documentation:** "Factory for creating retriever instances"

## 🟢 Static Methods

## `create(retriever_type: str, vector_store: VectorStoreInterface, embedder: EmbedderInterface, **kwargs) -> RetrieverInterface`

**Purpose:** Create retriever instance with specified strategy and dependencies

**Documentation:** "Create retriever based on type"

**Parameters:**

- `retriever_type` (str): Type of retriever strategy to create
    
- `vector_store` (VectorStoreInterface): Vector storage backend instance
    
- `embedder` (EmbedderInterface): Embedding provider instance
    
- `**kwargs`: Additional configuration parameters
    

**Supported Types:**

**`"basic"`:**

- Returns: `BasicRetriever(vector_store, embedder)`
    
- Purpose: Simple similarity-based retrieval
    

**`"hybrid"`:**

- Returns: `HybridRetriever(vector_store, embedder, semantic_weight, keyword_weight)`
    
- Additional Parameters:
    
    - `semantic_weight` (float, default: 0.7): Weight for semantic similarity
        
    - `keyword_weight` (float, default: 0.3): Weight for keyword matching
        

**`"rerank"`:**

- Returns: `RerankRetriever(vector_store, embedder, semantic_weight, keyword_weight, rerank_model, rerank_top_k)`
    
- Additional Parameters:
    
    - `semantic_weight` (float, default: 0.7): Weight for semantic similarity
        
    - `keyword_weight` (float, default: 0.3): Weight for keyword matching
        
    - `rerank_model` (str, default: "cross-encoder/ms-marco-MiniLM-L-6-v2"): Re-ranking model
        
    - `rerank_top_k` (int, default: 50): Number of candidates for re-ranking
        

**Error Handling:**

- Raises `ValueError` with message `"Unknown retriever type: {retriever_type}"` for unsupported types
    

**Usage Examples:**

python

`# Basic retriever basic_retriever = RetrieverFactory.create("basic", vector_store, embedder) # Hybrid retriever with custom weights hybrid_retriever = RetrieverFactory.create(     "hybrid", vector_store, embedder,     semantic_weight=0.8, keyword_weight=0.2 ) # Re-ranking retriever with custom configuration rerank_retriever = RetrieverFactory.create(     "rerank", vector_store, embedder,     rerank_model="custom-reranker", rerank_top_k=100 )`

## `GenerationFactory`

**Purpose:** Factory for creating RAG generation component instances

**Documentation:** "Factory for creating generation components"

## 🟢 Static Methods

## `create_rag_generator(retriever: RetrieverInterface, llm_provider: llm_provider_interface) -> RAGGenerator`

**Purpose:** Create RAG generator with specified retriever and LLM provider

**Documentation:** "Create RAG generator with specified retriever and LLM provider"

**Parameters:**

- `retriever` (RetrieverInterface): Document retrieval strategy instance
    
- `llm_provider` (llm_provider_interface): Language model provider instance
    

**Returns:**

- `RAGGenerator`: Configured RAG generation component
    

**Usage:**

python

`rag_generator = GenerationFactory.create_rag_generator(retriever, llm_provider) response = rag_generator.generate(query, context)`

## 🔄 Factory Pattern Benefits

## Centralized Component Creation

- Single point of control for component instantiation
    
- Consistent interface for creating similar components
    
- Easy configuration management and dependency injection
    

## Flexible Configuration

- Type-based component selection enables runtime configuration
    
- Support for different implementations without code changes
    
- Simplified testing with mock implementations
    

## Loose Coupling

- Components depend on interfaces, not concrete implementations
    
- Factory pattern decouples creation logic from business logic
    
- Enhanced maintainability and extensibility
    

## 🛠️ Complete Pipeline Assembly

## End-to-End Component Creation

python

`# Create all pipeline components via factories processor = DocumentProcessorFactory.create('pdf') chunker = ChunkingFactory.create('legal') embedder = EmbedderFactory.create('sentence_transformers') vector_store = VectorStoreFactory.create('weaviate') monitor = MonitoringFactory.create() # Create retriever with dependencies retriever = RetrieverFactory.create(     'hybrid', vector_store, embedder,     semantic_weight=0.7, keyword_weight=0.3 ) # Create RAG generator rag_generator = GenerationFactory.create_rag_generator(retriever, llm_provider)`

## ⚠️ Error Handling Patterns

## Exception Types

- **Generic `Exception`**: Used by DocumentProcessorFactory and ChunkingFactory
    
- **`ValueError`**: Used by VectorStoreFactory and RetrieverFactory for type validation
    

## Error Messages

- Descriptive error messages indicating unsupported types
    
- Consistent error handling across factory implementations
    
- Clear indication of supported vs. unsupported options
    

## 🔗 Cross-References & Dependencies

## Interface Contracts

- **[DocumentProcessorInterface](https://www.perplexity.ai/interfaces/document_processing_interface.md)** - Document processing contract
    
- **[ChunkingInterface](https://www.perplexity.ai/interfaces/chunking_interface.md)** - Text chunking contract
    
- **[EmbedderInterface](https://www.perplexity.ai/interfaces/embedder.md)** - Embedding generation contract
    
- **[VectorStoreInterface](https://www.perplexity.ai/interfaces/vector_store_interface.md)** - Vector storage contract
    
- **[RetrieverInterface](https://www.perplexity.ai/interfaces/retriever_interface.md)** - Document retrieval contract
    

## Concrete Implementations

- **[PDFExtractor](https://www.perplexity.ai/document_processor/pdf_extractor.md)** - PDF processing implementation
    
- **[LegalChunker](https://www.perplexity.ai/chunking/legal_chunker.md)** - Legal document chunking strategy
    
- **[WeaviateStore](https://www.perplexity.ai/vector_store/weaviate.md)** - Weaviate vector database
    
- **[Retrieval Strategies](https://www.perplexity.ai/retrieval/)** - Various retrieval implementations
    

## Pipeline Integration

- **[RAG Pipeline](https://www.perplexity.ai/pipeline.md)** - Uses factories for component creation
    
- **[Configuration](https://www.perplexity.ai/config/)** - Provides type specifications for factories