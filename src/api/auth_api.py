from ast import Str
from re import S
from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import timedelta, datetime
import jwt
from jwt import PyJWTError
from authlib.integrations.starlette_client import OAuth, OAuthError
from starlette.middleware.sessions import SessionMiddleware
from fastapi import FastAPI
from src.services.auth_service import verify_password, get_password_hash, create_access_token
from config.api_settings import settings

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/token')

oauth = OAuth()
CONF_URL = 'https://accounts.google.com/.well-known/openid-configuration'
oauth.register(
    name='google',
    server_metadata_url = CONF_URL,
    client_id = settings.GOOGLE_CLIENT_ID,
    client_secret = settings.GOOGLE_CLIENT_SECRET,
    client_kwargs = {'scope':'openid email provider'}
)

fake_users_db = {}

class User(BaseModel):
    email:EmailStr
    full_name:Optional[str] = None

class UserInDB(User):
    hashed_password: Optional[str] = None

class UserCreate(User):
    password:Optional[str] = None

class Token(BaseModel):
    access_token:str
    token_type:str

class TokenData(BaseModel):
    email:Optional[str] = None


def get_user(email:EmailStr) -> Optional[UserInDB]:
    user = fake_users_db.get(email)
    if user:
        return UserInDB(**user)
    return None

def authenticate_user(email:EmailStr,password:str) -> Optional[UserInDB]:
    user = get_user(email)
    if not user or not user.hashed_password:
        return None
    if not verify_password(password,user.hashed_password):
        return None
    return user

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except PyJWTError:
        raise credentials_exception
    user = get_user(email)
    if not user:
        raise credentials_exception
    return user


@router.post('/register',status_code=201)
async def register(user:UserCreate):
    if user.email in fake_users_db:
        raise HTTPException(status_code=400,detail='Email already registered')
    if not user.password:
        raise HTTPException(status_code=404, detail='Password required')
    hashed_password = get_password_hash(user.password)
    fake_users_db[user.email] = {
        "email":user.email,
        'full_name':user.full_name,
        'hashed_password':hashed_password,
    }
    return {'msg':'user registration successful'}

@router.post('/token',response_model=Token)
async def login(form_data:OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.email,form_data.password)
    if not user:
        raise HTTPException(status_code=401,detail='Incorrect email or password')
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={'sub':user.email},
        expires_delta=access_token_expires
    )
    return {'access_token':access_token, 'token_type':'bearer'}

@router.get('/login/google')
async def login_via_google(request:Request):
    redirect_uri = request.url_for('auth_google_callback')
    return await oauth.google.authorize_redirect(request,redirect_uri)

@router.get("/auth/google/callback")
async def auth_google_callback(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError:
        raise HTTPException(status_code=400, detail="Google OAuth failed")
    user_info = await oauth.google.parse_id_token(request, token)
    if not user_info:
        raise HTTPException(status_code=400, detail="Failed to get user info from Google")
    email = user_info['email']
    user = get_user(email)
    if not user:
        fake_users_db[email] = {
            "email": email,
            "email": user_info['email'],
            "full_name": user_info.get('name'),
            "hashed_password": None,
        }
        user = get_user(email)
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me", response_model=User)
async def read_users_me(current_user: UserInDB = Depends(get_current_user)):
    return current_user