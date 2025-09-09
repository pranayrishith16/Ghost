
# 📄 pdf_extractor.py

## Overview
This module provides PDF document processing functionality, implementing text extraction and metadata retrieval from PDF files using PyMuPDF.

## 📦 Dependencies & Imports

### Standard Library
- **`pathlib.Path`** - Modern file system path handling
- **`typing.Dict`** - Type hint for dictionary return types  
- **`typing.Any`** - Type hint for flexible value types
- **`os`** - Operating system interface functions

### External Libraries
- **`fitz`** (PyMuPDF) - Core PDF processing library for text extraction and metadata
  - Install: `pip install PyMuPDF`
  - Used for: Opening PDFs, extracting text, reading metadata

### Project Dependencies
- [**`src.interfaces.document_processing_interface.DocumentProcessorInterface`](Document_Processor_Interface.py.md)**
  - Base interface that defines the contract for document processors
  - Ensures consistent API across different document types

## 🏗️ Classes

### `PDFExtractor`
**Inherits from:** `DocumentProcessorInterface`  
**Purpose:** Specialized document processor for PDF files

This class implements the document processing interface specifically for PDF files, providing methods to extract text content, retrieve metadata, and validate PDF documents.

#### 🟢 Public Methods

##### `extract_text(self, file_path: Path) -> str`
**Purpose:** Extracts all text content from a PDF document

**Parameters:**
- `file_path` (Path): Path to the PDF file

**Returns:** 
- `str`: Combined text from all pages

**Implementation Details:**
- Opens PDF using PyMuPDF's `fitz.open()`
- Iterates through each page using `page.get_text()`
- Concatenates all page text into single string
- Ensures proper resource cleanup with try/finally block

**Usage:**
```
extractor = PDFExtractor()  
text = extractor.extract_text(Path("document.pdf"))
```


##### `extract_metadata(self, file_path: Path) -> Dict[str, Any]`
**Purpose:** Retrieves comprehensive metadata from PDF and file system

**Parameters:**
- `file_path` (Path): Path to the PDF file

**Returns Dictionary Contains:**
- `filename`: Original filename
- `file_size`: File size in bytes  
- `pages`: Number of pages in PDF
- `creation_date`: PDF creation date or file creation timestamp
- `mod_date`: PDF modification date or file modification timestamp
- Additional PDF intrinsic metadata fields

**Implementation Notes:**
- Merges PDF metadata with file system metadata
- File metadata takes precedence over PDF metadata for conflicts
- Uses `file_path.stat()` for file system information

##### `process_document(self, file_path: Path) -> Dict[str, Any]`
**Purpose:** Main processing method combining text extraction and metadata retrieval

**Parameters:**
- `file_path` (Path): Path to the PDF file to process

**Returns Dictionary Contains:**
- `text`: Full extracted text content
- `metadata`: Complete metadata dictionary
- `word_count`: Number of words in extracted text
- `char_count`: Total character count

**Error Handling:**
- Validates document before processing using `validate_document()`
- Raises `ValueError` for invalid or non-existent PDF files

**Usage:**
```
result = extractor.process_document(Path("report.pdf"))  
print(f"Processed {result['word_count']} words from {result['metadata']['pages']} pages")
```


##### `validate_document(self, file_path: Path) -> bool`
**Purpose:** Validates that the file exists and is a PDF

**Parameters:**
- `file_path` (Path): Path to validate

**Returns:**
- `bool`: True if valid PDF file, False otherwise

**Validation Checks:**
- File exists at the specified path
- File extension is `.pdf` (case-insensitive)

## 🔗 Cross-References & Dependencies

### Required Interface Implementation
This class implements all methods from:
- **[DocumentProcessorInterface](Document_Processor_Interface.py.md)**
  - Ensures consistent API across document processors
  - See interface documentation for method contracts

### Related Components
- **Text Processing Pipeline** - Uses extracted text for further processing
- **Metadata Indexing** - Utilizes extracted metadata for document cataloging
- **Document Validation** - Part of broader document validation system

### External Dependencies
- **PyMuPDF Documentation:** [https://pymupdf.readthedocs.io/](https://pymupdf.readthedocs.io/)
- **pathlib Documentation:** [https://docs.python.org/3/library/pathlib.html](https://docs.python.org/3/library/pathlib.html)
