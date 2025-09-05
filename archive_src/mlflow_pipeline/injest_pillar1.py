from pathlib import Path
import mlflow
from archive_src.utils.config_loader import config_load


def injest_pillar1():
    """main injestion for pillar1"""
    mlflow.set_experiment('Injestion for pillar 1')

    config = config_load()

    reading_jsonl = Path(__file__).resolve().parent.parent.parent / config['data_paths']['pillar1_processed']
    
    with open(reading_jsonl, 'r', encoding='utf-8') as f:
        for line_num,line in enumerate(f,1):
            print(line)
            break


if __name__ == '__main__':
    injest_pillar1()