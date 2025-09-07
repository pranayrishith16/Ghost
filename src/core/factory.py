# interfaces
from src.interfaces.document_processing_interface import DocumentProcessorInterface
from src.interfaces.chunking_interface import ChunkingInterface

## concrete implementations
from src.document_processor.pdf_extractor import PDFExtractor
from src.chunking.legal_chunker import LegalChunker

class DocumentProcessorFactory:
    """Factory for creating document processor"""

    @staticmethod
    def create(processor_type=None) -> DocumentProcessorInterface:
        processor_type = processor_type

        if processor_type == 'pdf':
            return PDFExtractor()
        else:
            raise Exception(f'The document is not pdf')
        
class ChunkingFactory:
    """Factory for chunking"""

    @staticmethod
    def create(chunker_type=None):
        chunker_type = chunker_type

        if chunker_type == 'legal':
            return LegalChunker()
        else:
            raise Exception(f'Chunker not working')