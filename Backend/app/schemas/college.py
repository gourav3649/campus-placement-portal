from pydantic import BaseModel
from typing import Optional

class CollegeBase(BaseModel):
    name: str
    location: Optional[str] = None
    website: Optional[str] = None

class CollegeCreate(CollegeBase):
    pass

class CollegeUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    is_active: Optional[bool] = None

class CollegeResponse(CollegeBase):
    id: int
    is_active: bool
    
    class Config:
        from_attributes = True
