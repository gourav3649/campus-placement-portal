from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from app.core.rbac import Role

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str
    role: Role

class UserResponse(UserBase):
    id: int
    role: Role
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class UserIdentity(BaseModel):
    id: int
    role: Role

class UserToken(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserIdentity

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[Role] = None
