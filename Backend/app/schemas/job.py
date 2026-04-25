from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.job import DriveStatus, JobType


class JobBase(BaseModel):
    title: str
    description: str
    requirements: Optional[str] = None
    responsibilities: Optional[str] = None
    required_skills: Optional[str] = None
    job_type: JobType = JobType.FULL_TIME
    location: Optional[str] = None
    is_remote: bool = False
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    positions_available: Optional[int] = None
    deadline: Optional[datetime] = None
    min_cgpa: Optional[float] = None
    allowed_branches: Optional[List[str]] = None
    max_backlogs: Optional[int] = None
    exclude_placed_students: bool = True


class JobCreate(JobBase):
    college_id: int


class JobUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    responsibilities: Optional[str] = None
    required_skills: Optional[str] = None
    job_type: Optional[JobType] = None
    location: Optional[str] = None
    is_remote: Optional[bool] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    positions_available: Optional[int] = None
    deadline: Optional[datetime] = None
    min_cgpa: Optional[float] = None
    allowed_branches: Optional[List[str]] = None
    max_backlogs: Optional[int] = None
    exclude_placed_students: Optional[bool] = None


class JobResponse(JobBase):
    id: int
    recruiter_id: int
    college_id: int
    drive_status: DriveStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class JobWithStats(JobResponse):
    """Job response with aggregate application stats for Placement Officer view."""
    total_applied: int = 0
    eligible_count: int = 0
    selected_count: int = 0
