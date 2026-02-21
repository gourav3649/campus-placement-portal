from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, Enum as SQLEnum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class ApplicationStatus(str, enum.Enum):
    """
    Application status enumeration.
    
    Workflow with eligibility:
    1. Student applies → PENDING
    2. System checks eligibility:
       - Eligible → PENDING (wait for AI ranking)
       - Not eligible → REJECTED (eligibility_failed)
    3. Recruiter/AI reviews → REVIEWING
    4. Final decision → SHORTLISTED/REJECTED/ACCEPTED
    """
    PENDING = "pending"
    ELIGIBILITY_FAILED = "eligibility_failed"  # NEW: Failed eligibility check
    REVIEWING = "reviewing"
    SHORTLISTED = "shortlisted"
    REJECTED = "rejected"
    ACCEPTED = "accepted"
    WITHDRAWN = "withdrawn"


class Application(Base):
    """
    Job application model - Eligibility-aware.
    
    Eligibility Workflow:
    1. Application created → is_eligible = None (not yet checked)
    2. Eligibility check runs → is_eligible = True/False
    3. If False → status = ELIGIBILITY_FAILED, NOT sent to AI
    4. If True → status = PENDING, sent to AI ranking
    
    This ensures AI only processes qualified candidates.
    """
    __tablename__ = "applications"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"))
    
    # Application Details
    status = Column(SQLEnum(ApplicationStatus), default=ApplicationStatus.PENDING, nullable=False)
    cover_letter = Column(Text)
    
    # Eligibility Tracking (NEW)
    is_eligible = Column(Boolean, nullable=True)  # None = not checked, True/False = result
    eligibility_reasons = Column(Text, nullable=True)  # JSON: ["min_cgpa_not_met", "branch_not_allowed"]
    eligibility_checked_at = Column(DateTime(timezone=True), nullable=True)
    
    # AI-generated scores (from semantic matching) - ONLY for eligible candidates
    match_score = Column(Float)  # Overall match score (0-100)
    skills_match_score = Column(Float)  # Skills compatibility
    experience_match_score = Column(Float)  # Experience compatibility
    
    # Ranking (calculated asynchronously) - ONLY among eligible pool
    rank = Column(Integer)  # Rank among ELIGIBLE applicants for this job
    rank_among_eligible = Column(Integer)  # Explicit: rank among eligible only
    
    # AI Analysis
    ai_summary = Column(Text)  # AI-generated summary of candidate fit
    strengths = Column(Text)  # Key strengths (JSON)
    weaknesses = Column(Text)  # Areas of concern (JSON)
    
    # Timestamps
    applied_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    student = relationship("Student", back_populates="applications")
    job = relationship("Job", back_populates="applications")
    resume = relationship("Resume")
    
    def __repr__(self):
        return f"<Application {self.id}: Student {self.student_id} -> Job {self.job_id}>"
