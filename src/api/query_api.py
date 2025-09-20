from datetime import datetime, timezone, timedelta, time, tzinfo
from fastapi import HTTPException, Depends, Security, APIRouter, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional


from src.api.auth_api import FREE_USER_QUERY_LIMIT, get_user_from_token
from src.core.pipeline import RAGPipeline
from src.api.db import free_user_usage_collection

router = APIRouter()

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2048, description="The question to query.")
    retrieval_strategy: Optional[str] = Field("hybrid", description="Retrieval strategy to use ('basic', 'hybrid', 'rerank').")
    query_type: Optional[str] = Field("legal_analysis", description="Type of query for LLM context.")
    max_results: Optional[int] = Field(10, ge=1, le=50, description="Maximum number of results to return.")
    filters: Optional[Dict[str, Any]] = Field(None, description="Optional filters for retrieval.")

# Singleton pattern to load pipeline once
def get_pipeline(request:Request):
    if not hasattr(request.app.state, "pipeline"):
        request.app.state.pipeline = RAGPipeline()
    return request.app.state.pipeline

@router.post('/query', summary='Query the pipeline', response_model=None)
async def query_pipeline(
    request_data: QueryRequest,
    request: Request,
    pipeline: RAGPipeline = Depends(get_pipeline),
    credentials: Optional[HTTPAuthorizationCredentials] = Security(HTTPBearer(auto_error=False)),
):
    if not credentials:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    token = credentials.credentials
    user = await get_user_from_token(token)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if isinstance(user,dict) and user.get('is_free_user'):
        anon_id = user['anon_id']
        now_utc = datetime.now(timezone.utc)
        midnight_utc = datetime.combine(now_utc.date() + timedelta(days=1), time.min, tzinfo=timezone.utc)

        usage_record = free_user_usage_collection.find_one({"anon_id":anon_id})

        if usage_record:
            expires_at = usage_record.get('expires_at')
            if expires_at is not None and expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at < now_utc:
                # Reset count and expiry
                free_user_usage_collection.update_one(
                                                        {"anon_id": anon_id},
                                                        {"$set": {"count": 1, "expires_at": midnight_utc}}
                )
                count = 1
            else:
                if usage_record.get("count", 0) >= FREE_USER_QUERY_LIMIT:
                    raise HTTPException(status_code=429, detail=f"Free user query limit exceeded ({FREE_USER_QUERY_LIMIT} per day)")
                free_user_usage_collection.update_one(
                    {"anon_id": anon_id},
                    {"$inc": {"count": 1}}
                )
                count = usage_record["count"] + 1
        else:
            free_user_usage_collection.insert_one({
                "anon_id":anon_id,
                "count":1,
                "expires_at":midnight_utc,
            })
            count = 1

    response = pipeline.query(
        question=request_data.question,
        retrieval_strategy=request_data.retrieval_strategy,
        query_type=request_data.query_type,
        max_results=request_data.max_results,
        filters=request_data.filters,
    )
    return {"status": "success", "response": response}