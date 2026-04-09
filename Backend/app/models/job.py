from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class JobType(str, enum.Enum):
    """Job type enumeration."""
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    INTERNSHIP = "internship"
    CONTRACT = "contract"


class JobStatus(str, enum.Enum):
    """Job posting status - Legacy field."""
    OPEN = "open"
    CLOSED = "closed"
    DRAFT = "draft"


class DriveStatus(str, enum.Enum):
    """
    Placement Drive Status - College approval workflow.
    
    Workflow:
    1. Recruiter creates job → DRAFT
    2. Placement Officer reviews → APPROVED
    3. Students can apply only to APPROVED drives
    4. Drive closes after deadline → CLOSED
    """
    DRAFT = "draft"            # Created by recruiter, awaiting approval
    APPROVED = "approved"      # Approved by placement officer
    REJECTED = "rejected"      # Rejected by placement officer
    CLOSED = "closed"          # Drive completed
    CANCELLED = "cancelled"    # Cancelled by recruiter or admin


class Job(Base):
    """
    Job posting model - Multi-tenant with college-specific drives.
    
    Multi-tenancy:
    - Each job is targeted to ONE college
    - Only students from that college can apply
    - Placement officer from that college must approve
    
    Eligibility Filtering:
    - Jobs define eligibility criteria (CGPA, branch, backlogs)
    - System filters ineligible students BEFORE AI ranking
    - Only eligible students are sent to AI matching engine
    """
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    recruiter_id = Column(Integer, ForeignKey("recruiters.id"), nullable=False)
    
    # Multi-tenant: College Assignment (NEW)
    college_id = Column(
        Integer,
        ForeignKey("colleges.id", ondelete="CASCADE"),
        nullable=False,
        index=True  # CRITICAL: Index for multi-tenant queries
    )
    
    # Job Information
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    requirements = Column(Text)  # Store as JSON or text
    responsibilities = Column(Text)
    
    # Job Details
    job_type = Column(SQLEnum(JobType), nullable=False)
    status = Column(SQLEnum(JobStatus), default=JobStatus.OPEN, nullable=False)  # Legacy
    drive_status = Column(SQLEnum(DriveStatus), default=DriveStatus.DRAFT, nullable=False)  # NEW
    location = Column(String(255))
    is_remote = Column(Boolean, default=False)
    
    # Compensation
    salary_min = Column(Float)
    salary_max = Column(Float)
    currency = Column(String(10), default="USD")
    
    # Requirements
    required_skills = Column(Text)  # Store as JSON string
    experience_years = Column(Integer)
    education_level = Column(String(100))
    
    # Eligibility Criteria (NEW: Pre-AI filtering rules)
    min_cgpa = Column(Float, nullable=True)  # e.g., 7.0 minimum
    allowed_branches = Column(Text, nullable=True)  # JSON: ["CS", "ECE", "IT"]
    max_backlogs = Column(Integer, nullable=True)  # e.g., 0 (no backlogs), 2 (max 2)
    exclude_placed_students = Column(Boolean, default=True, nullable=False)  # Skip already placed
    
    # Metadata
    positions_available = Column(Integer, default=1)
    deadline = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    recruiter = relationship("Recruiter", back_populates="jobs")
    college = relationship("College", back_populates="jobs")  # NEW: Multi-tenant relationship
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")
    offers = relationship("Offer", back_populates="job", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Job {self.title} @ College {self.college_id}>"
    
    @property
    def is_active(self):
        """Check if job is open for applications."""
        return self.drive_status == DriveStatus.APPROVED and self.status == JobStatus.OPEN
