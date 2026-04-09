from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, Enum as SQLEnum, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class ApplicationStatus(str, enum.Enum):
    """
    PHASE 2: Standardized Application Status Flow
    
    Clean lifecycle:
    APPLIED → IN_PROGRESS → ACCEPTED/REJECTED
    APPLIED → REJECTED (early rejection)
    Any → WITHDRAWN (student withdrawal)
    
    Final states (ACCEPTED, REJECTED) are immutable.
    """
    APPLIED = "applied"        # Initial submission
    IN_PROGRESS = "in_progress"  # Undergoing evaluation rounds
    REJECTED = "rejected"      # Final: rejected (immutable)
    ACCEPTED = "accepted"      # Final: accepted (immutable)
    WITHDRAWN = "withdrawn"    # Student withdrawal (immutable)


class Application(Base):
    """
    PHASE 2: Job application model with standardized workflow.
    
    Lifecycle:
    APPLIED → IN_PROGRESS (first round added)
    IN_PROGRESS → ACCEPTED/REJECTED (final decision via last round result)
    Any state → WITHDRAWN (student withdrawal)
    
    Final states (ACCEPTED, REJECTED, WITHDRAWN) are immutable.
    
    Each application can have multiple rounds.
    Only the latest round determines progression.
    """
    __tablename__ = "applications"
    
    __table_args__ = (
        UniqueConstraint('student_id', 'job_id', name='uq_student_job_application'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"))
    
    # Application Details
    status = Column(SQLEnum(ApplicationStatus), default=ApplicationStatus.APPLIED, nullable=False)
    cover_letter = Column(Text)
    
    # Eligibility Tracking (NEW)
    is_eligible = Column(Boolean, nullable=True)  # None = not checked, True/False = result
    eligibility_reasons = Column(Text, nullable=True)  # JSON: ["min_cgpa_not_met", "branch_not_allowed"]
    eligibility_checked_at = Column(DateTime(timezone=True), nullable=True)
    
    # AI Ranking Score (embedding-based cosine similarity only)
    ai_rank_score = Column(Float, nullable=True)  # Cosine similarity 0-1
    
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
    rounds = relationship("ApplicationRound", back_populates="application", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Application {self.id}: Student {self.student_id} -> Job {self.job_id}>"
