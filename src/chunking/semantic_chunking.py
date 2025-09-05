from langchain_text_splitters import RecursiveCharacterTextSplitter
import sys
from pathlib import Path

# Fix import path
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.settings import get_config

from src.interfaces.chunker import ChunkerInterface

class SemanticChunker(ChunkerInterface):
    """Chunks text using RecursiveCharacterTextSplitter for semantic boundaries"""

    def __init__(self):
        self.config = get_config().chunking

        # Initialize the text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.overlap,
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )

    def chunk_text(self, text, metadata = None):
        if not text:
            return []
        
        try:
            # Use RecursiveCharacterTextSplitter to create chunks
            chunks = self.text_splitter.split_text(text)
            
            # Format chunks with metadata
            formatted_chunks = []
            for i, chunk_text in enumerate(chunks):
                formatted_chunks.append({
                    'text': chunk_text.strip(),
                    'word_count': len(chunk_text.split()),
                    'char_count': len(chunk_text),
                    'chunk_index': i,
                    'metadata': metadata or {}
                })
            
            return formatted_chunks
            
        except Exception as e:
            print(e)
            return None
            # # Fallback to fixed size chunking
            # from .fixed_size_chunker import FixedSizeChunker
            # fallback_chunker = FixedSizeChunker()
            # return fallback_chunker.chunk_text(text, metadata)

    def get_chunk_size(self):
        return self.config.chunk_size
    
    def get_overlap(self):
        return self.config.overlap
    
    def validate_chunks(self, chunks):
        """Validate chunk quality"""
        if not chunks:
            return False

        for chunk in chunks:
            # Check minimum content
            if len(chunk['text']) < self.config.min_chunk_size:
                return False

            # Check for required fields
            required_fields = ['text', 'word_count', 'char_count', 'chunk_index']
            if not all(field in chunk for field in required_fields):
                return False

        return True