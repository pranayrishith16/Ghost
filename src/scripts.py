# test_simple.py
from pathlib import Path
from src.core.pipeline import RAGPipeline
from config.settings import get_config

# Initialize
config = get_config()
pipeline = RAGPipeline()

# Quick ingest test (optional - only if you have no data yet)
# data_dir = Path(config.data_dir)
# pipeline.batch_ingest(data_dir)

# Test a simple query
try:
    response = pipeline.query(
        question="illegal lane usage",
        retrieval_strategy="basic",
        query_type="legal_analysis"
    )
    
    print("✅ Pipeline working!")
    print(f"Answer: {response['answer']}")
    print(f"Confidence: {response['confidence_score']}")
    print(f"Sources found: {len(response['sources'])}")
    
except Exception as e:
    print(f"❌ Pipeline failed: {e}")
