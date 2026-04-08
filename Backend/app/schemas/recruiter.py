from pydantic import BaseModel, EmailStr
from typing import Optional
from .user import UserResponse

class RecruiterBase(BaseModel):
    company_name: str
    email: EmailStr
    website: Optional[str] = None

class RecruiterCreate(RecruiterBase):
    user_id: int

class RecruiterUpdate(BaseModel):
    company_name: Optional[str] = None
    website: Optional[str] = None

class RecruiterResponse(RecruiterBase):
    id: int
    user_id: int
    is_verified: bool
    
    class Config:
        from_attributes = True
        
class RecruiterProfileResponse(RecruiterResponse):
    user: UserResponse
