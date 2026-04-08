from pydantic import BaseModel, EmailStr
from typing import Optional, List
from .user import UserResponse

class StudentBase(BaseModel):
    first_name: str
    last_name: str
    branch: str
    graduation_year: int
    cgpa: float
    skills: Optional[str] = None
    bio: Optional[str] = None
    college_id: int

class StudentCreate(StudentBase):
    user_id: int

class StudentUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    branch: Optional[str] = None
    graduation_year: Optional[int] = None
    cgpa: Optional[float] = None
    skills: Optional[str] = None
    bio: Optional[str] = None
    
class StudentResponse(StudentBase):
    id: int
    user_id: int
    is_placed: bool
    has_backlogs: bool
    
    class Config:
        from_attributes = True
        
class StudentProfileResponse(StudentResponse):
    user: UserResponse
