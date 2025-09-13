from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone, time
import jwt
from typing import Optional
import uuid

from src.api.models import UserInDB

FREE_USER_QUERY_LIMIT = 3
FREE_USER_TOKEN_EXP_HOUR_UTC = 0  # Midnight UTC

# In-memory usage tracking for demo (replace with persistent store)
free_user_usage = {}

#api-settings
from config.api_settings import settings

pwd_context = CryptContext(schemes=['bcrypt'],deprecated='auto')

def get_password_hash(password:str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password:str, hashed_password:str) -> bool:
    return pwd_context.verify(plain_password,hashed_password)





def create_access_token(data:dict, expires_delta:Optional[timedelta]=None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode,settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return encoded_jwt