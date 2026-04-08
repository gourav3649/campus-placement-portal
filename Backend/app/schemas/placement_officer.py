from pydantic import BaseModel, EmailStr
from typing import Optional
from .user import UserResponse

class PlacementOfficerBase(BaseModel):
    name: str
    email: EmailStr
    designation: Optional[str] = None
    department: Optional[str] = None
    college_id: int

class PlacementOfficerCreate(PlacementOfficerBase):
    user_id: int

class PlacementOfficerUpdate(BaseModel):
    name: Optional[str] = None
    designation: Optional[str] = None
    department: Optional[str] = None

class PlacementOfficerResponse(PlacementOfficerBase):
    id: int
    user_id: int
    
    class Config:
        from_attributes = True
        
class PlacementOfficerProfileResponse(PlacementOfficerResponse):
    user: UserResponse
