# """
# Custom exception classes for the Law RAG system.
# Provides detailed error information for different components.
# """

# class DocumentProcessingError(Exception):
#     """Raised when document processing fails"""
#     def __init__(self, message: str, file_path: str = None):
#         self.file_path = file_path
#         super().__init__(f"Document processing error: {message}" + (f" (File: {file_path})" if file_path else ""))

# class ChunkingError(Exception):
#     """Raised when text chunking fails"""
#     def __init__(self, message: str, text_sample: str = None):
#         self.text_sample = text_sample
#         super().__init__(f"Chunking error: {message}" + (f" (Sample: {text_sample[:100]}...)" if text_sample else ""))

# class EmbeddingError(Exception):
#     """Raised when embedding generation fails"""
#     def __init__(self, message: str, model_name: str = None):
#         self.model_name = model_name
#         super().__init__(f"Embedding error: {message}" + (f" (Model: {model_name})" if model_name else ""))

# class VectorStoreError(Exception):
#     """Raised when vector database operations fail"""
#     def __init__(self, message: str, operation: str = None):
#         self.operation = operation
#         super().__init__(f"Vector store error: {message}" + (f" (Operation: {operation})" if operation else ""))

# class LLMGenerationError(Exception):
#     """Raised when LLM text generation fails"""
#     def __init__(self, message: str, provider: str = None, prompt: str = None):
#         self.provider = provider
#         self.prompt = prompt
#         super().__init__(f"LLM generation error: {message}" + 
#                         (f" (Provider: {provider})" if provider else "") +
#                         (f" (Prompt: {prompt[:100]}...)" if prompt else ""))

# class PipelineError(Exception):
#     """Raised when the main RAG pipeline fails"""
#     def __init__(self, message: str, stage: str = None):
#         self.stage = stage
#         super().__init__(f"Pipeline error: {message}" + (f" (Stage: {stage})" if stage else ""))

# class ConfigurationError(Exception):
#     """Raised when configuration is invalid or missing"""
#     def __init__(self, message: str, config_key: str = None):
#         self.config_key = config_key
#         super().__init__(f"Configuration error: {message}" + (f" (Key: {config_key})" if config_key else ""))

# class LLMConnectionError(Exception):
#     """Raised when connection to LLM service fails"""
#     def __init__(self, message: str, provider: str = None):
#         self.provider = provider
#         super().__init__(f"LLM connection error: {message}" + (f" (Provider: {provider})" if provider else ""))