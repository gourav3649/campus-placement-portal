from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import datetime


# Base schemas
class StudentBase(BaseModel):
    """
    Base student schema.
    
    Single-college mode:
    - college_id: Auto-injected from settings (not user-provided)
    - branch: Department/Stream (CS, ECE, ME, etc.)
    - has_backlogs: Academic standing
    - is_placed: Placement status
    """
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    
    # Academic fields
    branch: Optional[str] = Field(None, max_length=100, description="Branch/Department (CS, ECE, ME)")
    
    # Academic fields
    enrollment_number: Optional[str] = Field(None, max_length=50)
    university: Optional[str] = Field(None, max_length=255)  # Legacy support
    degree: Optional[str] = Field(None, max_length=100)
    major: Optional[str] = Field(None, max_length=100)
    graduation_year: Optional[int] = Field(None, ge=2000, le=2050)
    cgpa: Optional[float] = Field(None, ge=0.0, le=10.0)
    
    # Placement status (NEW)
    has_backlogs: bool = Field(False, description="Has active academic backlogs")
    is_placed: bool = Field(False, description="Already placed in a company")
    
    # Profile fields
    bio: Optional[str] = None
    linkedin_url: Optional[HttpUrl] = None
    github_url: Optional[HttpUrl] = None
    portfolio_url: Optional[HttpUrl] = None
    skills: Optional[str] = None  # Comma-separated or JSON


class StudentCreate(StudentBase):
    """Schema for creating a student profile."""
    user_id: int


class StudentUpdate(BaseModel):
    """Schema for updating student profile (all fields optional)."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    
    # Multi-tenant fields (NEW)
    branch: Optional[str] = Field(None, max_length=100)
    
    # Academic fields
    enrollment_number: Optional[str] = Field(None, max_length=50)
    university: Optional[str] = Field(None, max_length=255)
    degree: Optional[str] = Field(None, max_length=100)
    major: Optional[str] = Field(None, max_length=100)
    graduation_year: Optional[int] = Field(None, ge=2000, le=2050)
    cgpa: Optional[float] = Field(None, ge=0.0, le=10.0)
    
    # Placement status (NEW) - Can be updated by placement officer
    has_backlogs: Optional[bool] = None
    is_placed: Optional[bool] = None
    
    # Profile fields
    bio: Optional[str] = None
    linkedin_url: Optional[HttpUrl] = None
    github_url: Optional[HttpUrl] = None
    portfolio_url: Optional[HttpUrl] = None
    skills: Optional[str] = None


class StudentInDB(StudentBase):
    """Schema for student in database."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class Student(StudentInDB):
    """Public student schema."""
    pass


class StudentProfile(BaseModel):
    """Complete student profile with user info and multi-tenant fields."""
    id: int
    user_id: int
    email: str
    college_id: int  # NEW
    first_name: str
    last_name: str
    phone: Optional[str]
    branch: Optional[str]  # NEW
    enrollment_number: Optional[str]
    university: Optional[str]
    degree: Optional[str]
    major: Optional[str]
    graduation_year: Optional[int]
    cgpa: Optional[float]
    has_backlogs: bool  # NEW
    is_placed: bool  # NEW
    bio: Optional[str]
    linkedin_url: Optional[str]
    github_url: Optional[str]
    portfolio_url: Optional[str]
    skills: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
