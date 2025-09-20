# modules
import token
from fastapi import APIRouter, Body, HTTPException, Depends, status, Request
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import timedelta, datetime, timezone, time
import jwt
from jwt import PyJWTError, ExpiredSignatureError
from authlib.integrations.starlette_client import OAuth, OAuthError
import uuid
from secrets import token_urlsafe

# In-house
from src.services.auth_service import verify_password, get_password_hash, create_access_token
from src.api.models import User, UserInDB
from src.api.db import users_collection, refresh_tokens_collection
from config.api_settings import settings

FREE_USER_QUERY_LIMIT = 50
FREE_USER_TOKEN_EXP_HOUR_UTC = 0  # Midnight UTC


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

# Pydantic models

class UserCreate(User):
    password:str = Field(min_length=8)

class Token(BaseModel):
    access_token:str
    token_type:str

class TokenData(BaseModel):
    email:Optional[str] = None


def create_free_user_token():
    anon_id = str(uuid.uuid4())
    # Calculate UTC midnight expiry
    now = datetime.now(timezone.utc)
    midnight = datetime.combine(now.date() + timedelta(days=1), time(FREE_USER_TOKEN_EXP_HOUR_UTC))
    exp = int(midnight.timestamp())
    payload = {
        "sub": anon_id,
        "free_user": True,
        "exp": exp
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token, anon_id

async def get_user_from_token(token:str) -> Optional[UserInDB]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get('free_user'):
            #its a free user token
            return {"anon_id": payload.get("sub"), "is_free_user": True}
        else:
            # It's a normal authenticated user token
            email = payload.get("sub")
            if not email:
                return None
            user = get_user(email)
            return user
    except (PyJWTError, ExpiredSignatureError):
        return None


# Helper to convert MongoDB user dict to UserInDB model
def user_doc_to_model(user_doc) -> UserInDB:
    if not user_doc:
        return None
    user_doc['id'] = str(user_doc['_id'])
    # Remove MongoDB internal keys if present
    user_doc.pop('_id', None)
    return UserInDB(**user_doc)

# Fetch user from MongoDB by email
def get_user(email: EmailStr) -> Optional[UserInDB]:
    user_doc = users_collection.find_one({'email': email})
    return user_doc_to_model(user_doc)

# Authenticate user with email and password
def authenticate_user(email: EmailStr, password: str) -> Optional[UserInDB]:
    user = get_user(email)
    if not user or not user.hashed_password:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

# Dependency to get current user from JWT token
async def get_current_user(token:str = Depends(oauth2_scheme)) -> UserInDB:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            raise credentials_exception
        # Expiration claim validated by PyJWT decode automatically, add manual if needed
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except PyJWTError:
        raise credentials_exception
    user = get_user(email)
    if not user:
        raise credentials_exception
    return user

# REFRESH TOKENS HELPERS

REFRESH_TOKENS_EXPIRE_DAYS = 28

def create_refresh_token(user_email:str):
    refresh_token = token_urlsafe(32)
    expires_at = datetime.now(time.utc) + timedelta(days=REFRESH_TOKENS_EXPIRE_DAYS)
    refresh_tokens_collection.insert_one({
        "refresh_token": refresh_token,
        "email":user_email,
        "expires_at":expires_at
    })
    return refresh_token



@router.get("/free_token", summary="Get a free user token for anonymous usage")
async def get_free_user_token():
    token, anon_id = create_free_user_token()
    return JSONResponse(content={"access_token": token, "token_type": "bearer"})

@router.post('/register',status_code=201)
async def register(user:UserCreate):
    if get_user(user.email):
        raise HTTPException(status_code=400,detail='Email already registered')
    if not user.password:
        raise HTTPException(status_code=404, detail='Password required')
    hashed_password = get_password_hash(user.password)
    user_dict = user.model_dump()
    user_dict['hashed_password'] = hashed_password
    user_dict.pop('password')  # remove plain password
    users_collection.insert_one(user_dict)
    return {'msg': 'User registration successful'}

@router.post('/token',response_model=Token)
async def login(form_data:OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username,form_data.password)
    if not user:
        raise HTTPException(status_code=401,detail='Incorrect email or password')
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={'sub':user.email},
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(user.email)
    return {
        'access_token':access_token, 
        'token_type':'bearer',
        'refresh_token':refresh_token,
        }

@router.post('/token/refresh')
async def refresh_access_token(refresh_token:str = Body(..., embed=True)):
    token_record = refresh_tokens_collection.find_one({'refresh_token':refresh_token})
    now = datetime.now(timezone.utc)
    if not token_record or token_record.get('expires_at',now) < now:
        raise HTTPException(status_code=401,detail='Invalid or expired refresh token')
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(
        data={
            "sub":token_record["email"]},
            expires_delta=access_token_expires,
    )
    return {
        'access_token':new_access_token,
        'token_type':'bearer'
    }


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
        user_data = {
            "email":email,
            "full_name":user_info.get('name'),
            "hashed_password":None  # Passwordless user created by OAuth
        }
        users_collection.insert_one(user_data)
        user = get_user(email)
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me", response_model=User)
async def read_users_me(current_user: UserInDB = Depends(get_current_user)):
    return User(email=current_user.email, full_name=current_user.full_name)