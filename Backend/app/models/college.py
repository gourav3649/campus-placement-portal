"""College model for multi-tenant campus recruitment."""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class College(Base):
    """
    College/University entity - Primary tenant in multi-tenant architecture.
    
    Each college is an independent tenant with:
    - Own students
    - Own placement officers
    - Own job drives
    - Isolated data access
    """
    __tablename__ = "colleges"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # College Information
    name = Column(String(255), nullable=False, unique=True, index=True)
    location = Column(String(255))
    accreditation = Column(String(100))  # NAAC, NBA, etc.
    website = Column(String(255))
    contact_email = Column(String(255))
    contact_phone = Column(String(20))
    
    # Additional Info
    description = Column(Text)
    logo_url = Column(String(500))
    established_year = Column(Integer)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships - Define multi-tenant hierarchy
    students = relationship("Student", back_populates="college", cascade="all, delete-orphan")
    placement_officers = relationship("PlacementOfficer", back_populates="college", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="college", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<College {self.id}: {self.name}>"
    
    @property
    def student_count(self):
        """Get total number of students in this college."""
        return len(self.students)
    
    @property
    def active_job_count(self):
        """Get number of active jobs for this college."""
        from app.models.job import JobStatus
        return len([job for job in self.jobs if job.status == JobStatus.OPEN])
