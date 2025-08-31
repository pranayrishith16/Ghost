from langchain_text_splitters import RecursiveCharacterTextSplitter
from .base_extractor import extract_normal_pdf, extract_text_using_ocr

def process_case_pdf(pdf_path, chunk_size=1000, chunk_overlap=175):
    """
    Pillar1-specific PDF processing for legal cases
    """
    result = {
        "file_name": pdf_path.name,
        "success": False,
        "chunks": [],
        "error": None,
        "used_ocr": False,
        "pillar": "cases"
    }
    
    try:
        # Use shared base functions
        full_text = extract_normal_pdf(pdf_path)
        
        if full_text is None:
            result["used_ocr"] = True
            print(f"Using OCR for: {pdf_path.name}")
            full_text = extract_text_using_ocr(pdf_path)
        
        if not full_text.strip():
            result["error"] = "No text extracted (even with OCR)"
            return result
            
        # Case-specific text cleaning
        full_text = clean_case_text(full_text)
        
        # Split into chunks
        chunks = split_text(full_text, chunk_size, chunk_overlap)
        
        result["success"] = True
        result["chunks"] = chunks
        
    except Exception as e:
        result["error"] = str(e)
        
    return result

def clean_case_text(text):
    """Case-specific text cleaning logic"""
    # Remove extra whitespace (basic cleaning - can be expanded)
    text = ' '.join(text.split())
    # Add case-specific cleaning here (legal citations, judge names, etc.)
    return text

def split_text(text, chunk_size, chunk_overlap):
    """Shared text splitting logic"""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    return text_splitter.split_text(text)