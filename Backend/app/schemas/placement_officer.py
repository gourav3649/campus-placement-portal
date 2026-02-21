"""Pydantic schemas for Placement Officer model."""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime


class PlacementOfficerBase(BaseModel):
    """Base placement officer schema."""
    name: str = Field(..., min_length=2, max_length=255, description="Officer name")
    email: EmailStr = Field(..., description="Officer email")
    phone: Optional[str] = Field(None, max_length=20, description="Contact phone")
    designation: Optional[str] = Field(None, max_length=100, description="Designation/Title")
    department: Optional[str] = Field(None, max_length=100, description="Department")


class PlacementOfficerCreate(PlacementOfficerBase):
    """
    Schema for creating a new placement officer.
    
    Requires:
    - user_id: Existing user account with PLACEMENT_OFFICER role
    - college_id: College this officer belongs to
    """
    user_id: int = Field(..., description="User ID (must have PLACEMENT_OFFICER role)")
    college_id: int = Field(..., description="College ID")


class PlacementOfficerUpdate(BaseModel):
    """Schema for updating placement officer (all fields optional)."""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    designation: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=100)


class PlacementOfficer(PlacementOfficerBase):
    """Schema for placement officer response."""
    id: int
    user_id: int
    college_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Commented out to avoid circular import - can be added back with proper forward reference
# class PlacementOfficerWithCollege(PlacementOfficer):
#     """Placement officer schema with college details."""
#     college: "College"
#     
#     class Config:
#         from_attributes = True
