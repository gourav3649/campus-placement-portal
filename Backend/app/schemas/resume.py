from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ResumeBase(BaseModel):
    filename: str
    content_type: str

class ResumeCreate(ResumeBase):
    student_id: int
    file_path: str

class ResumeUpdate(BaseModel):
    raw_text: Optional[str] = None
    embedding_vector: Optional[str] = None

class ResumeResponse(ResumeBase):
    id: int
    student_id: int
    file_path: str
    uploaded_at: datetime
    
    class Config:
        from_attributes = True

class ResumeDetailResponse(ResumeResponse):
    raw_text: Optional[str]
