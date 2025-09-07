import re
from langchain_text_splitters import RecursiveCharacterTextSplitter
import sys
from pathlib import Path

from config.settings import get_config

from src.interfaces.chunking_interface import ChunkingInterface

class LegalChunker(ChunkingInterface):
    """Legal document specific with RecursiveCharacterTextSplitter"""

    def __init__(self):
        self.config = get_config().chunking

        # initialize text splitter for legal documents
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.overlap,
            length_function=len,
            separators=["\n\n\n", "\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )

    def chunk_text(self, text, metadata=None):
        """Split legal documents using section aware chunking"""
        if not text:
            return []
        
        return self._standard_chunking(text,metadata)
    
    def _standard_chunking(self,text,metadata):
        """Standard recursive chunking for less structured documents"""
        chunks = self.text_splitter.split_text(text)
        
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
    
    def get_chunk_size(self, text, metadata):
        return self.config.chunk_size
    
    def get_overlap(self):
        return self.config.overlap
    
    def validate_chunks(self, chunks):
        """Validate chunk quality for legal documents"""
        if not chunks:
            return False

        for chunk in chunks:
            # Legal documents may have shorter chunks (citations, headings)
            if len(chunk['text']) < 20:
                return False

            # Check for required fields
            required_fields = ['text', 'word_count', 'char_count', 'chunk_index']
            if not all(field in chunk for field in required_fields):
                return False

        return True