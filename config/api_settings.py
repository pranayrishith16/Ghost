from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    GOOGLE_CLIENT_ID: str 
    GOOGLE_CLIENT_SECRET: str 

    # MongoDB connection settings
    MONGODB_URI: str
    MONGODB_DB_NAME: str   # default DB name if not set in env

    class Config:
        extra = "ignore"   # Ignore unexpected fields instead of raising error
        env_file = '.env'
        env_file_encoding = 'utf-8'

settings = Settings()