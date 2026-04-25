from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class JobRoundCreate(BaseModel):
    """Schema for creating a job-level round template."""
    round_number: int
    name: str
    is_eliminatory: bool = True
    max_score: Optional[float] = None


class JobRoundResponse(BaseModel):
    """Schema for returning a job-level round template."""
    id: int
    job_id: int
    round_number: int
    name: str
    is_eliminatory: bool
    max_score: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True
