from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from src.api.auth_api import router as auth_router
from src.api.query_api import router as query_router

from src.api.db import client

app = FastAPI(title='Veritly AI RAG SYSTEM')

origins = [
    "http://localhost:5173",
]

@app.on_event("shutdown")
def shutdown_db_client():
    client.close()

#session middleware required for OAuth
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(auth_router, prefix='/auth',tags=['auth'])
app.include_router(query_router, prefix='/rag',tags=['rag'])