import mlflow
from .process_pillar1 import process_pillar1

def process_everything():
    """Orchestrate processing of all three pillars"""
    mlflow.set_experiment('Legal-RAG-Full-Pipeline')

    with mlflow.start_run(run_name='Process_All_Pillars'):
        print("Starting Pillar1 (Cases) processing...")
        process_pillar1()

if __name__ == "__main__":
    process_everything()