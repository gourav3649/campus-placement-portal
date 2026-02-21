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
    """Schema for AI-ranked application."""
    application_id: int
    student_id: int
    student_name: str
    match_score: float
    skills_match_score: float
    experience_match_score: float
    rank: int
    ai_summary: str
    strengths: List[str]
    weaknesses: List[str]
    resume_url: Optional[str]


class ApplicationList(BaseModel):
    """Schema for paginated application list."""
    total: int
    page: int
    page_size: int
    applications: List[Application]


class RankingRequest(BaseModel):
    """Request schema for triggering AI ranking."""
    job_id: int
    rerank: bool = Field(default=False, description="Force re-ranking of all applications")
