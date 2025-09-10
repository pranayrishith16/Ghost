from warnings import deprecated
from passlib.context import CryptContext
from datetime import datetime, timedelta
import jwt
from typing import Optional

#api-settings
from config.api_settings import settings

pwd_context = CryptContext(schemes=['bcrypt'],deprecated='auto')

def get_password_hash(password:str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password:str, hashed_password:str) -> bool:
    return pwd_context.verify(plain_password,hashed_password)

def create_access_token(data:dict, expires_delta:Optional[timedelta]=None) -> str:
    to_encode = data.copy()
    expire = datetime.now(datetime.timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode,settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return encoded_jwt