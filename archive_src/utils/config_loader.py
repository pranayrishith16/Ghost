import yaml
from pathlib import Path

def config_load(environment='development'):
    config_path = Path(__file__).resolve().parent.parent.parent / 'config' / f'{environment}.yaml'
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)