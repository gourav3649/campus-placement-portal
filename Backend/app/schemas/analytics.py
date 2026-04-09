"""PHASE 5: Analytics schema responses."""
from pydantic import BaseModel
from typing import Optional
from app.models.application import ApplicationStatus


class CandidateInsight(BaseModel):
    """PHASE 5: Student's self-insight for an application."""
    avg_score: Optional[float]
    rounds_cleared: int
    current_status: ApplicationStatus
    performance_label: str  # "Strong Candidate", "Good Candidate", "Needs Improvement"


class TopCandidate(BaseModel):
    """PHASE 5: Top candidate summary for recruiter."""
    student_id: int
    student_name: str
    avg_score: Optional[float]
    rounds_cleared: int
    latest_status: ApplicationStatus


class DriveSummary(BaseModel):
    """PHASE 5: Drive/job summary for officer."""
    total_applicants: int
    in_progress_count: int
    accepted_count: int
    rejected_count: int
