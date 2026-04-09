from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# Base schemas
class ResumeBase(BaseModel):
    """Base resume schema."""
    filename: str
    content_type: str


class ResumeCreate(BaseModel):
    """Schema for creating a resume record (after upload)."""
    filename: str
    file_path: str
    content_type: str


class ResumeResponse(BaseModel):
    """Schema for resume API response."""
    id: int
    student_id: int
    filename: str
    file_path: str
    content_type: str
    raw_text: Optional[str] = None  # Extracted text (always None in response for privacy)
    embedding_vector: Optional[str] = None  # Embedding (None in response, internal only)
    uploaded_at: datetime
    
    class Config:
        from_attributes = True


class ResumeDetail(ResumeResponse):
    """Resume with text details (for student viewing)."""
    raw_text: Optional[str] = None  # Can include if needed
    embedding_vector: Optional[str] = None  # Never exposed in API
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
