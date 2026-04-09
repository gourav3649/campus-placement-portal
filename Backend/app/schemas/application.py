from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from app.models.application import ApplicationStatus


# Base schemas
class ApplicationBase(BaseModel):
    """Base application schema."""
    job_id: int
    resume_id: Optional[int] = None
    cover_letter: Optional[str] = None


class ApplicationCreate(ApplicationBase):
    """Schema for creating an application."""
    pass


class ApplicationUpdate(BaseModel):
    """Schema for updating an application."""
    status: Optional[ApplicationStatus] = None
    cover_letter: Optional[str] = None


class ApplicationInDB(ApplicationBase):
    """Schema for application in database."""
    id: int
    student_id: int
    status: ApplicationStatus
    ai_rank_score: Optional[float]  # Cosine similarity (-1 to 1)
    match_score: Optional[float]
    skills_match_score: Optional[float]
    experience_match_score: Optional[float]
    rank: Optional[int]
    ai_summary: Optional[str]
    strengths: Optional[str]
    weaknesses: Optional[str]
    applied_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class Application(ApplicationInDB):
    """Public application schema."""
    pass


class ApplicationWithDetails(Application):
    """Application with job and student details."""
    job_title: str
    company_name: str
    student_name: str
    student_email: str
    
    class Config:
        from_attributes = True


class ApplicationRanking(BaseModel):
    """Schema for ranked application (based on embedding cosine similarity)."""
    application_id: int
    student_id: int
    student_name: str
    similarity_score: float  # Cosine similarity between resume and job (-1 to 1)
    rank: int
    
    class Config:
        from_attributes = True


class ApplicationList(BaseModel):
    """Schema for paginated application list."""
    total: int
    page: int
    page_size: int
    applications: List[Application]


class StudentRankingView(BaseModel):
    """Schema for student's view of their ranking on a job."""
    application_id: int
    job_id: int
    job_title: str
    similarity_score: float  # Cosine similarity (-1 to 1)
    rank: int
    total_applicants: int
    status: ApplicationStatus
    
    class Config:
        from_attributes = True


class CandidatePreview(BaseModel):
    """Schema for dashboard candidate preview with ranking."""
    application_id: int
    student_id: int
    student_name: str
    email: Optional[str]
    similarity_score: float  # Cosine similarity (-1 to 1)
    rank: int
    status: ApplicationStatus
    applied_at: datetime
    
    class Config:
        from_attributes = True


class RankingRequest(BaseModel):
    """Request schema for triggering AI ranking."""
    job_id: int
    rerank: bool = Field(default=False, description="Force re-ranking of all applications")
