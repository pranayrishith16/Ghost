from pydantic import BaseModel, EmailStr
from typing import Optional

class User(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

    class Config:
        orm_mode = True

class UserInDB(User):
    hashed_password: Optional[str] = None
    id: Optional[str] = None
