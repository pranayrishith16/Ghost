from os import pipe
from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from pathlib import Path

from src.core.pipeline import RAGPipeline

app = FastAPI(
    title='Veritly AI Law RAG API',
    version='1.0.0',
    description='API system for RAG pipeline'
)

# Singleton pattern to load pipeline once
def get_pipeline():
    if not hasattr(app.state, "pipeline"):
        app.state.pipeline = RAGPipeline()
    return app.state.pipeline

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2048, description="The question to query.")
    retrieval_strategy: Optional[str] = Field("basic", description="Retrieval strategy to use ('basic', 'hybrid', 'rerank').")
    query_type: Optional[str] = Field("legal_analysis", description="Type of query for LLM context.")
    max_results: Optional[int] = Field(10, ge=1, le=50, description="Maximum number of results to return.")
    filters: Optional[Dict[str, Any]] = Field(None, description="Optional filters for retrieval.")

@app.post('/query', summary='Query the pipeline', response_model=Dict[str,Any])
async def query_pipeline(request: QueryRequest, pipeline: RAGPipeline = Depends(get_pipeline)):
    try:
        response = pipeline.query(
            question=request.question,
            retrieval_strategy=request.retrieval_strategy,
            query_type=request.query_type,
            max_results=request.max_results,
            filters=request.filters,
        )
        return {"status": "success", "response": response}
    
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error - try again later")