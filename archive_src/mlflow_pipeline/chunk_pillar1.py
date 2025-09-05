from pathlib import Path
import json
import mlflow
import pandas as pd
from archive_src.data_processing.case_pdf_extractor import process_case_pdf
from archive_src.utils.config_loader import config_load

def process_pillar1():
    """Main processing pipeline for Pillar1 (Cases)"""
    mlflow.set_experiment('Pillar 1 processing for RAG')

    config = config_load()

    PDF_FOLDER = Path(__file__).resolve().parent.parent.parent / config['data_paths']['pillar1_raw']
    OUTPUT_LOCATION = Path(__file__).parent.parent.parent / config['data_paths']['pillar1_processed']
    CHUNK_SIZE = config['processing']['chunk_size']
    CHUNK_OVERLAP = config['processing']['chunk_overlap']
    BATCH_SIZE = config['processing']['batch_size']

    OUTPUT_LOCATION.parent.mkdir(parents=True, exist_ok=True)

    with mlflow.start_run(run_name='Data_Process_Pillar_1_PDFS'):
        mlflow.log_params({
            "chunk_size": CHUNK_SIZE,
            "chunk_overlap": CHUNK_OVERLAP,
            "input_folder": str(PDF_FOLDER),
            "output_file": str(OUTPUT_LOCATION),
            "pillar": "cases"
        })

    all_files = list(PDF_FOLDER.glob("*.pdf"))
    total_files = len(all_files)
    mlflow.log_metric("total_files", total_files)
    print(f"There are {total_files} number of case files")

    # counters
    good_files = 0
    bad_files = 0
    total_chunks = 0
    error_list = []

    with open(OUTPUT_LOCATION, 'w', encoding='utf-8') as outfile:
        for i, pdf_path in enumerate(all_files):
            result = process_case_pdf(pdf_path, CHUNK_SIZE, CHUNK_OVERLAP)
            
            if result['success']:
                good_files += 1
                for chunk_id, text in enumerate(result['chunks']):
                    record = {
                        "text": text,
                        "metadata": {
                            "source_file": result['file_name'],
                            "chunk_id": chunk_id,
                            "pillar": "cases",
                            "used_ocr": result['used_ocr']
                        }
                    }
                    outfile.write(json.dumps(record) + '\n')
                    total_chunks += 1
            else:
                bad_files += 1
                error_list.append([result['file_name'], result['error']])

            if (i + 1) % BATCH_SIZE == 0:
                mlflow.log_metrics({
                    "processed_files": i + 1,
                    "good_files": good_files,
                    'bad_files': bad_files,
                    'total_chunks': total_chunks,
                }, step=i + 1)
    
    mlflow.log_metrics({
        "total_good_files": good_files,
        "total_bad_files": bad_files,
        "final_total_chunks": total_chunks,
    })

    if error_list:
        error_df = pd.DataFrame(error_list, columns=["file_name", "error"])
        mlflow.log_table(data=error_df, artifact_file="processing_errors.json")
    
    mlflow.log_artifact(OUTPUT_LOCATION)
    
    print("=" * 50)
    print("PILLAR1 PROCESSING COMPLETE!")
    print(f"Successfully processed: {good_files} case files")
    print(f"Failed: {bad_files} case files")
    print(f"Total chunks created: {total_chunks}")
    print(f"Output saved to: {OUTPUT_LOCATION}")

if __name__ == "__main__":
    process_pillar1()