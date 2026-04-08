from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.application import ApplicationStatus


class ApplicationCreate(BaseModel):
    job_id: int
    resume_id: Optional[int] = None
    cover_letter: Optional[str] = None


class ApplicationUpdateStatus(BaseModel):
    status: ApplicationStatus


class StudentSummary(BaseModel):
    id: int
    first_name: str
    last_name: str
    branch: str
    cgpa: float

    class Config:
        from_attributes = True

class RoundSummary(BaseModel):
    id: int
    round_number: int
    round_name: str
    result: str

    class Config:
        from_attributes = True

class JobSummary(BaseModel):
    id: int
    title: str
    company_name: str

    class Config:
        from_attributes = True

class ApplicationResponse(BaseModel):
    id: int
    student_id: int
    job_id: int
    resume_id: Optional[int]
    cover_letter: Optional[str]
    status: ApplicationStatus
    is_eligible: bool
    eligibility_reasons: Optional[List[str]]
    ai_score: Optional[float]
    ai_rank: Optional[int]
    applied_at: datetime
    updated_at: datetime
    student: Optional[StudentSummary] = None
    job: Optional[JobSummary] = None
    rounds: List[RoundSummary] = []

    class Config:
        from_attributes = True
