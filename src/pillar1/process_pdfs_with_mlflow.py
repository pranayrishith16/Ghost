import fitz
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pathlib import Path
import json
import mlflow
import re
import pandas as pd
import easyocr
from PIL import Image
import io
import numpy as np

# --configuration--
PDF_FOLDER = Path(__file__).resolve().parent / '..' / '..' / 'data' / 'raw' / 'pillar1-cases'
OUTPUT_LOCATION = Path(__file__).resolve().parent / '..' / '..' / 'data' / 'processed' / 'case_chunks.jsonl'
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 175
BATCH_SIZE = 50      # will update MLFLOW every 50 files
# -----

#initialize OCR engine
print('Initializing OCR engine...')
reader = easyocr.Reader(['en'])

def extract_text_using_OCR(pdf_path):
    doc = fitz.open(pdf_path)
    full_txt = ""

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        # render page with high res image
        mat = fitz.Matrix(2.0,2.0) # scale factor for better OCR
        pix = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes('png')

        #Convert to numpy array (which EasyOCR accepts)
        img_bytes = pix.tobytes("ppm")  # Use PPM format for easier conversion
        pil_image = Image.open(io.BytesIO(img_bytes))
        img_array = np.array(pil_image)  # Convert to numpy array

        #Perform OCR on the image
        results = reader.readtext(img_array, detail=0)  # detail=0 returns only text
        page_text = " ".join(results)
        full_txt += page_text + "\n"
    
    doc.close()
    return full_txt

def extract_normal_pdf(pdf_path):
    """
    Extracts text from NORMAL text-based PDFs.
    Returns: Extracted text as string, or None if no text found
    """
    doc = fitz.open(pdf_path)
    full_text = ""
    
    for page in doc:
        text = page.get_text()
        if text.strip():  # If page has text
            full_text += text + "\n"
    
    doc.close()
    return full_text if full_text.strip() else None

def single_pdf(pdf_path):
    """
    Processes one PDF file - tries normal extraction first, then OCR if needed.
    """
    result = {
        "file_name": pdf_path.name,
        "success": False,
        "chunks": [],
        "error": None,
        "used_ocr": False  # Track if we had to use OCR
    }
    
    try:
        # FIRST: Try normal text extraction
        full_text = extract_normal_pdf(pdf_path)
        
        # SECOND: If normal extraction failed, use OCR
        if full_text is None:
            result["used_ocr"] = True
            print(f"Using OCR for: {pdf_path.name}")
            full_text = extract_text_using_OCR(pdf_path)
        
        if not full_text.strip():
            result["error"] = "No text extracted (even with OCR)"
            return result
            
        # Clean text
        full_text = ' '.join(full_text.split())  # Remove extra whitespace
        
        # Split into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP
        )
        chunks = text_splitter.split_text(full_text)
        
        # Return successful result
        result["success"] = True
        result["chunks"] = chunks
        
    except Exception as e:
        result["error"] = str(e)
        
    return result


def main():
    print('Starting MLFlow tracking!.. Open localhost 5000 to montior')
    mlflow.set_experiment('Legal-RAG-PDF-Processing')

    with mlflow.start_run(run_name='Process_large_number_PDFS'):
        # adding configuration parameters
        mlflow.log_params({
            "chunk_size":CHUNK_SIZE,
            "chunk_overlap":CHUNK_OVERLAP,
            "input_folder":str(PDF_FOLDER),
            "output_file":str(OUTPUT_LOCATION)
        })

    all_files = list(PDF_FOLDER.glob("*.pdf"))
    total_files = len(all_files)
    mlflow.log_metric("total_files",total_files)
    print("There are {} number of files".format(total_files))

    # counters
    good_files = 0
    bad_files = 0
    total_chunks = 0
    error_list = []

    with open(OUTPUT_LOCATION, 'w', encoding='utf-8') as outfile:
        for i,pdf_path in enumerate(all_files):
            result = single_pdf(pdf_path)
            if result['success']:
                good_files += 1
                for chunk_id,text in enumerate(result['chunks']):
                    record = {
                        "text":text,
                        "metadata":{
                            "source_file":result['file_name'],
                            "chunk_id":chunk_id
                        }
                    }
                    outfile.write(json.dumps(record) + '\n')
                    total_chunks += 1
            else:
                bad_files += 1
                error_list.append([result['file_name'],result['error']])

            if (i+1) % BATCH_SIZE == 0:
                mlflow.log_metrics({
                    "processed_files": i+1,
                    "good_files":good_files,
                    'bad_files':bad_files,
                    'total_chunks':total_chunks,
                }, step=i+1)
    mlflow.log_metrics({
        "total_good_files":good_files,
        "total_bad_files":bad_files,
        "final_total_chunks":total_chunks,
    })

    if error_list:
            error_df = pd.DataFrame(error_list, columns=["file_name", "error"])
    
            mlflow.log_table(
                data=error_df,
                artifact_file="processing_errors.json"
            )
        
        # Save the output file as an artifact in MLflow
    mlflow.log_artifact(OUTPUT_LOCATION)
    
    print("="*50)
    print("PROCESSING COMPLETE!")
    print(f"Successfully processed: {good_files} files")
    print(f"Failed: {bad_files} files")
    print(f"Total chunks created: {total_chunks}")
    print(f"Output saved to: {OUTPUT_LOCATION}")
    print("View detailed results at: http://localhost:5000")

if __name__ == "__main__":
    main()