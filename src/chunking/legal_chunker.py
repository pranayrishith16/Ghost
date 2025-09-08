from typing import Dict, Any, List, Optional
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.interfaces.chunking_interface import ChunkingInterface
from config.settings import get_config

class LegalChunker(ChunkingInterface):
    """Legal document specific chunker using RecursiveCharacterTextSplitter"""

    def __init__(self) -> None:
        cfg = get_config().chunking
        self._chunk_size = cfg.chunk_size
        self._overlap = cfg.overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self._chunk_size,
            chunk_overlap=self._overlap,
            length_function=len,
            separators=["\n\n\n", "\n\n", "\n", ". ", "! ", "? ", ", ", " ", ""],
        )

    def chunk_text(self, text: str, meta = None) -> List[Dict[str, Any]]:
        if not text:
            return []
        chunks = self.text_splitter.split_text(text)
        formatted = []
        md = meta or {}
        for i, chunk_text in enumerate(chunks):
            ct = chunk_text.strip()
            formatted.append(
                {
                    "text": ct,
                    "word_count": len(ct.split()),
                    "char_count": len(ct),
                    "chunk_index": i,
                    "metadata": md,
                }
            )
        return formatted

    def get_chunk_size(self, text: str, meta = None) -> int:
        return self._chunk_size

    def get_overlap(self) -> int:
        return self._overlap

    def validate_chunks(self, chunks: List[Dict[str, Any]]) -> bool:
        if not chunks:
            return False
        for ch in chunks:
            # Keep practical lower bound while allowing short legal headings/citations
            if "text" not in ch or len(ch["text"]) < 5:
                return False
            for req in ("word_count", "char_count", "chunk_index"):
                if req not in ch:
                    return False
        return True
