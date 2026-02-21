from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.job import JobType, JobStatus, DriveStatus


# Base schemas
class JobBase(BaseModel):
    """
    Base job schema.
    
    Single-college mode:
    - college_id: Auto-injected from settings (not user-provided)
    - drive_status: Approval workflow (draft → approved → closed)
    - Eligibility criteria: min_cgpa, allowed_branches, max_backlogs
    """
    # Basic fields
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    requirements: Optional[str] = None
    responsibilities: Optional[str] = None
    job_type: JobType
    
    # Approval workflow
    drive_status: DriveStatus = Field(DriveStatus.DRAFT, description="Approval workflow status")
    
    # Location and work mode
    location: Optional[str] = Field(None, max_length=255)
    is_remote: bool = False
    
    # Compensation
    salary_min: Optional[float] = Field(None, ge=0)
    salary_max: Optional[float] = Field(None, ge=0)
    currency: str = Field(default="USD", max_length=10)
    
    # Requirements
    required_skills: Optional[str] = None  # JSON string or comma-separated
    experience_years: Optional[int] = Field(None, ge=0)
    education_level: Optional[str] = Field(None, max_length=100)
    
    # Eligibility Criteria (NEW - Pre-AI filtering)
    min_cgpa: Optional[float] = Field(None, ge=0.0, le=10.0, description="Minimum CGPA required")
    allowed_branches: Optional[str] = Field(None, description="JSON list of allowed branches")
    max_backlogs: Optional[int] = Field(None, ge=0, description="Maximum backlogs allowed (0 = no backlogs)")
    exclude_placed_students: bool = Field(True, description="Exclude already placed students")
    
    # Metadata
    positions_available: int = Field(default=1, ge=1)
    deadline: Optional[datetime] = None


class JobCreate(JobBase):
    """Schema for creating a job posting."""
    pass


class JobUpdate(BaseModel):
    """Schema for updating a job posting (all fields optional)."""
    # Basic fields
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    requirements: Optional[str] = None
    responsibilities: Optional[str] = None
    job_type: Optional[JobType] = None
    status: Optional[JobStatus] = None
    drive_status: Optional[DriveStatus] = None  # NEW
    
    # Location
    location: Optional[str] = Field(None, max_length=255)
    is_remote: Optional[bool] = None
    
    # Compensation
    salary_min: Optional[float] = Field(None, ge=0)
    salary_max: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=10)
    
    # Requirements
    required_skills: Optional[str] = None
    experience_years: Optional[int] = Field(None, ge=0)
    education_level: Optional[str] = Field(None, max_length=100)
    
    # Eligibility Criteria (NEW)
    min_cgpa: Optional[float] = Field(None, ge=0.0, le=10.0)
    allowed_branches: Optional[str] = None
    max_backlogs: Optional[int] = Field(None, ge=0)
    exclude_placed_students: Optional[bool] = None
    
    # Metadata
    positions_available: Optional[int] = Field(None, ge=1)
    deadline: Optional[datetime] = None


class JobInDB(JobBase):
    """Schema for job in database."""
    id: int
    recruiter_id: int
    status: JobStatus  # Legacy
    drive_status: DriveStatus  # NEW: Current approval status
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class Job(JobInDB):
    """Public job schema."""
    pass


class JobWithRecruiter(Job):
    """Job schema with recruiter information."""
    company_name: str
    company_website: Optional[str]
    
    class Config:
        from_attributes = True


class JobList(BaseModel):
    """Schema for paginated job list."""
    total: int
    page: int
    page_size: int
    jobs: List[Job]
