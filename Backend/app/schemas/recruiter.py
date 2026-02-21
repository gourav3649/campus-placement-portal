from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from datetime import datetime


# Base schemas
class RecruiterBase(BaseModel):
    """Base recruiter schema."""
    company_name: str = Field(..., min_length=1, max_length=255)
    company_website: Optional[HttpUrl] = None
    company_description: Optional[str] = None
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    position: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    linkedin_url: Optional[HttpUrl] = None


class RecruiterCreate(RecruiterBase):
    """Schema for creating a recruiter profile."""
    user_id: int


class RecruiterUpdate(BaseModel):
    """Schema for updating recruiter profile."""
    company_name: Optional[str] = Field(None, min_length=1, max_length=255)
    company_website: Optional[HttpUrl] = None
    company_description: Optional[str] = None
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    position: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    linkedin_url: Optional[HttpUrl] = None


class RecruiterInDB(RecruiterBase):
    """Schema for recruiter in database."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class Recruiter(RecruiterInDB):
    """Public recruiter schema."""
    pass


class RecruiterProfile(BaseModel):
    """Complete recruiter profile with user info."""
    id: int
    user_id: int
    email: str
    company_name: str
    company_website: Optional[str]
    company_description: Optional[str]
    first_name: str
    last_name: str
    position: Optional[str]
    phone: Optional[str]
    linkedin_url: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
