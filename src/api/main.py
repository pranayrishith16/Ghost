from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from src.api.auth_api import router as auth_router
from src.api.query_api import router as query_router
from config.api_settings import settings

app = FastAPI(title='Veritly AI RAG SYSTEM')

#session middleware required for OAuth
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    https_only=True,
    max_age=14*14*3600,
    same_site='lax'
)

# app.include_router(auth_router, prefix='/auth',tags=['auth'])
app.include_router(query_router, prefix='/rag',tags=['rag'])