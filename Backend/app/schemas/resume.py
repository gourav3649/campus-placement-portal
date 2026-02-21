from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# Base schemas
class ResumeBase(BaseModel):
    """Base resume schema."""
    filename: str


class ResumeCreate(BaseModel):
    """Schema for creating a resume record."""
    filename: str
    file_path: str
    file_size: int
    mime_type: str


class ResumeUpdate(BaseModel):
    """Schema for updating resume metadata."""
    is_primary: Optional[bool] = None


class ResumeInDB(ResumeBase):
    """Schema for resume in database."""
    id: int
    student_id: int
    file_path: str
    file_size: int
    mime_type: str
    is_primary: bool
    parse_status: str
    parse_error: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class Resume(ResumeInDB):
    """Public resume schema."""
    pass


class ParsedResumeData(BaseModel):
    """Schema for parsed resume data."""
    skills: List[str]
    experience: List[Dict[str, Any]]
    education: List[Dict[str, Any]]
    certifications: List[str]
    contact_info: Dict[str, str]
    summary: Optional[str]


class ResumeWithParsedData(Resume):
    """Resume with complete parsed data."""
    parsed_data: Optional[ParsedResumeData]
    extracted_skills: Optional[List[str]]
    extracted_experience: Optional[List[Dict[str, Any]]]
    extracted_education: Optional[List[Dict[str, Any]]]
    extracted_certifications: Optional[List[str]]


class ResumeUploadResponse(BaseModel):
    """Response after uploading a resume."""
    resume_id: int
    filename: str
    file_size: int
    parse_status: str
    message: str
