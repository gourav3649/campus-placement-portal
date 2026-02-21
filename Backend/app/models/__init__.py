"""Database models package."""
from app.models.user import User
from app.models.student import Student
from app.models.recruiter import Recruiter
from app.models.college import College
from app.models.placement_officer import PlacementOfficer
from app.models.job import Job, JobType, JobStatus, DriveStatus
from app.models.application import Application, ApplicationStatus
from app.models.resume import Resume

__all__ = [
    "User",
    "Student",
    "Recruiter",
    "College",
    "PlacementOfficer",
    "Job",
    "JobType",
    "JobStatus",
    "DriveStatus",
    "Application",
    "ApplicationStatus",
    "Resume",
]
