import time
from pathlib import Path
from datetime import datetime

from confection import try_load_json

#interfaces
from src.interfaces.document_processing_interface import DocumentProcessorInterface
from src.interfaces.chunking_interface import ChunkingInterface

#factory
from src.core.factory import DocumentProcessorFactory
from src.core.factory import ChunkingFactory

#settings
from config.settings import get_config


class RAGPipeline:
    """Main RAG pipeline that coordinates all the components
       This is central nervous system
    """

    def __init__(self):
        self.config = get_config()
        #initialize components using factory pattern
        self.document_processor = DocumentProcessorFactory.create("pdf")
        self.chunker = ChunkingFactory.create(self.config.chunking.strategy)

    def injest_document(self,file_path):
        """
        Process a single document through the entire ingestion pipeline.
#         Returns metadata about the processed document.
        """
        try:
            start_time = time.time()
            
            # 1. Document processing
            document_data = self.document_processor.process_document(file_path)

            # 2. Chunking processing
            chunks = self.chunker.chunk_text(document_data['text'],document_data['metadata'])


            return chunks
        except:
            raise Exception('The document cannot be injested')
        
    def batch_injest(self,directory_path):
        """
        Process all the documents through injestion pipeline
        """

        try:
            if not directory_path.exists():
                raise Exception('The directory does not exist')
            
            results = []
            total_files = 0
            successful_files = 0

            # find all pdf files in directory
            pdf_files = list(directory_path.rglob('*.pdf'))
            total_files = len(pdf_files)

            for i, pdf_file in enumerate(pdf_files):
                try:
                    print(successful_files)
                    result = self.injest_document(pdf_file)
                    if result['text']:
                        successful_files += 1
                except Exception as e:
                    # Log or print which file failed and continue
                    print(f"Skipping invalid PDF {pdf_file}: {e}")
                    continue  # Skip to next file

        except Exception as e:
            raise Exception(e)