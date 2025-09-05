import mlflow
from pathlib import Path
import json
from archive_src.utils.config_loader import config_load
from archive_src.data_processing.base_json_extractor import USJSONProcessor

def process_pillar2():
    """Main processing pipeline for Pillar 2 - Statutes"""
    mlflow.set_experiment('Pillar 2 Processing for RAG')

    config = config_load()

    JSON_FOLDER = Path(__file__).resolve().parent.parent.parent / config['data_paths']['pillar2_raw']
    OUTPUT_LOCATION = Path(__file__).resolve().parent.parent.parent / config['data_paths']['pillar2_processed']
    CHUNK_SIZE = config['processing']['chunk_size']
    CHUNK_OVERLAP = config['processing']['chunk_overlap']
    BATCH_SIZE = config['processing']['batch_size']

    OUTPUT_LOCATION.parent.mkdir(parents=True,exist_ok=True)

    with mlflow.start_run(run_name='Data_process_Pillar_2_JSON'):
        mlflow.log_params({
            "chunk_size": CHUNK_SIZE,
            "chunk_overlap": CHUNK_OVERLAP,
            "input_folder": str(JSON_FOLDER),
            "output_file": str(OUTPUT_LOCATION),
            'pillar':'Statutes',
        })

    good_files = 0
    bad_files = 0

    all_files = list(JSON_FOLDER.glob('*.json'))
    total_files = len(all_files)
    mlflow.log_metric('Total Files', total_files)
    print('There are {} number of statutes'.format(total_files))

    jsonprocessor = USJSONProcessor()

    with open(OUTPUT_LOCATION, 'w', encoding='utf-8') as outfile:
        for i,json_path in enumerate(all_files):
            result = jsonprocessor.process_json_file(json_path)
            if result['success']:
                good_files+=1
            else:
                bad_files+=1
    
    print(good_files,bad_files)
    


if __name__ == '__main__':
    process_pillar2() 