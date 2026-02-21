"""Pydantic schemas for College model."""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime


class CollegeBase(BaseModel):
    """Base college schema with common fields."""
    name: str = Field(..., min_length=2, max_length=255, description="College name")
    location: Optional[str] = Field(None, max_length=255, description="College location")
    accreditation: Optional[str] = Field(None, max_length=100, description="Accreditation (NAAC/NBA)")
    website: Optional[str] = Field(None, max_length=255, description="College website URL")
    contact_email: Optional[EmailStr] = Field(None, description="College contact email")
    contact_phone: Optional[str] = Field(None, max_length=20, description="College contact phone")
    description: Optional[str] = Field(None, description="College description")
    logo_url: Optional[str] = Field(None, max_length=500, description="Logo URL")
    established_year: Optional[int] = Field(None, ge=1800, le=2100, description="Year established")


class CollegeCreate(CollegeBase):
    """Schema for creating a new college."""
    pass


class CollegeUpdate(BaseModel):
    """Schema for updating a college (all fields optional)."""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    accreditation: Optional[str] = Field(None, max_length=100)
    website: Optional[str] = Field(None, max_length=255)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = None
    logo_url: Optional[str] = Field(None, max_length=500)
    established_year: Optional[int] = Field(None, ge=1800, le=2100)
    is_active: Optional[bool] = None


class College(CollegeBase):
    """Schema for college response (includes database fields)."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CollegeWithStats(College):
    """College schema with statistics."""
    student_count: int = Field(0, description="Number of students")
    active_job_count: int = Field(0, description="Number of active job drives")
    placement_officer_count: int = Field(0, description="Number of placement officers")
    
    class Config:
        from_attributes = True
