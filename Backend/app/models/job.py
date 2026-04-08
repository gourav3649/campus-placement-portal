import enum
from sqlalchemy import Column, Integer, String, Boolean, Float, Text, ForeignKey, DateTime, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class DriveStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"

class JobType(str, enum.Enum):
    FULL_TIME = "FULL_TIME"
    INTERNSHIP = "INTERNSHIP"
    CONTRACT = "CONTRACT"

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    college_id = Column(Integer, ForeignKey("colleges.id", ondelete="CASCADE"), nullable=False, index=True)
    recruiter_id = Column(Integer, ForeignKey("recruiters.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Basic Info
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    requirements = Column(Text, nullable=True)
    responsibilities = Column(Text, nullable=True)
    required_skills = Column(Text, nullable=True) # comma separated
    
    # Job Details
    job_type = Column(SQLEnum(JobType), nullable=False, default=JobType.FULL_TIME)
    location = Column(String(255), nullable=True)
    is_remote = Column(Boolean, default=False)
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    positions_available = Column(Integer, nullable=True)
    
    # Drive Schedule
    deadline = Column(DateTime(timezone=True), nullable=True)
    drive_date = Column(DateTime(timezone=True), nullable=True)
    reporting_time = Column(String(50), nullable=True)
    
    # Eligibility Rules
    min_cgpa = Column(Float, nullable=True)
    allowed_branches = Column(JSON, nullable=True) # list of branch strings
    max_backlogs = Column(Integer, nullable=True)
    exclude_placed_students = Column(Boolean, default=True)
    
    # AI generated embedding for matching
    embedding_vector = Column(Text, nullable=True)
    
    # Workflow
    status = Column(SQLEnum(DriveStatus), nullable=False, default=DriveStatus.DRAFT)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    @property
    def company_name(self) -> str:
        if self.recruiter:
            return self.recruiter.company_name
        return "Unknown"

    # Relationships
    college = relationship("College", back_populates="jobs")
    recruiter = relationship("Recruiter", back_populates="jobs")
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")
    offers = relationship("Offer", back_populates="job", cascade="all, delete-orphan")
