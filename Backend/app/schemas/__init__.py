"""Pydantic schemas package."""
from app.schemas.user import (
    User, UserCreate, UserUpdate, UserInDB,
    Token, TokenPayload, LoginRequest, PasswordChange
)
from app.schemas.student import (
    Student, StudentCreate, StudentUpdate, StudentInDB, StudentProfile
)
from app.schemas.recruiter import (
    Recruiter, RecruiterCreate, RecruiterUpdate, RecruiterInDB, RecruiterProfile
)
from app.schemas.job import (
    Job, JobCreate, JobUpdate, JobInDB, JobWithRecruiter, JobList
)
from app.schemas.application import (
    Application, ApplicationCreate, ApplicationUpdate, ApplicationInDB,
    ApplicationWithDetails, ApplicationRanking, ApplicationList, RankingRequest
)
from app.schemas.resume import (
    Resume, ResumeCreate, ResumeUpdate, ResumeInDB,
    ParsedResumeData, ResumeWithParsedData, ResumeUploadResponse
)

__all__ = [
    # User schemas
    "User", "UserCreate", "UserUpdate", "UserInDB",
    "Token", "TokenPayload", "LoginRequest", "PasswordChange",
    # Student schemas
    "Student", "StudentCreate", "StudentUpdate", "StudentInDB", "StudentProfile",
    # Recruiter schemas
    "Recruiter", "RecruiterCreate", "RecruiterUpdate", "RecruiterInDB", "RecruiterProfile",
    # Job schemas
    "Job", "JobCreate", "JobUpdate", "JobInDB", "JobWithRecruiter", "JobList",
    # Application schemas
    "Application", "ApplicationCreate", "ApplicationUpdate", "ApplicationInDB",
    "ApplicationWithDetails", "ApplicationRanking", "ApplicationList", "RankingRequest",
    # Resume schemas
    "Resume", "ResumeCreate", "ResumeUpdate", "ResumeInDB",
    "ParsedResumeData", "ResumeWithParsedData", "ResumeUploadResponse",
]
