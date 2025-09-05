import re
from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
import sys
from pathlib import Path

# Fix import path
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.settings import get_config

from src.interfaces.chunker import ChunkerInterface

class LegalChunker(ChunkerInterface):
    """Legal document specific chunking using RecursiveCharacterTextSplitter"""

    def __init__(self):
        self.config = get_config().chunking
        
        # Initialize text splitter for legal documents
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.overlap,
            length_function=len,
            separators=["\n\n\n", "\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )

        # Legal document section patterns
        self.section_patterns = [
            re.compile(r'^(?:\d+\.\s+)?([A-Z][A-Z\s]{5,}):?$', re.MULTILINE),
            re.compile(r'^([IVX]+\.\s+[A-Z][A-Z\s]{5,})$', re.MULTILINE),
            re.compile(r'^([A-Z][A-Za-z\s]{5,}):$', re.MULTILINE),
        ]

    def chunk_text(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Split legal documents using section-aware chunking"""
        if not text:
            return []

        # Try to extract sections first for structured legal documents
        sections = self._extract_sections(text)
        
        if sections and len(sections) > 1:
            return self._chunk_by_sections(text, sections, metadata)
        else:
            # Use standard recursive chunking for less structured documents
            return self._standard_chunking(text, metadata)

    def _extract_sections(self, text: str) -> List[Dict[str, Any]]:
        """Extract legal document sections"""
        sections = []
        
        for pattern in self.section_patterns:
            matches = list(pattern.finditer(text))
            
            for i, match in enumerate(matches):
                section_title = match.group(1).strip()
                start_pos = match.start()
                end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(text)
                
                sections.append({
                    'title': section_title,
                    'start_pos': start_pos,
                    'end_pos': end_pos
                })
        
        return sections

    def _chunk_by_sections(self, text: str, sections: List[Dict[str, Any]], metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Chunk text while preserving section structure"""
        chunks = []
        
        for i, section in enumerate(sections):
            section_text = text[section['start_pos']:section['end_pos']].strip()
            
            if section_text:
                # Chunk each section individually
                section_chunks = self.text_splitter.split_text(section_text)
                
                for j, chunk_text in enumerate(section_chunks):
                    chunks.append({
                        'text': chunk_text.strip(),
                        'section_title': section['title'],
                        'section_index': i,
                        'word_count': len(chunk_text.split()),
                        'char_count': len(chunk_text),
                        'chunk_index': len(chunks),
                        'is_section': True,
                        'metadata': metadata or {}
                    })
        
        return chunks

    def _standard_chunking(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
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

    def get_chunk_size(self) -> int:
        return self.config.chunk_size

    def get_overlap(self) -> int:
        return self.config.overlap

    def validate_chunks(self, chunks: List[Dict[str, Any]]) -> bool:
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