from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Student(Base):
    """
    Student profile model - Multi-tenant aware.
    
    Multi-tenancy:
    - Every student belongs to exactly ONE college
    - Students can only apply to jobs from their own college
    - Eligibility is enforced at college level
    
    Placement Status:
    - Tracks placement status (is_placed)
    - Academic standing (backlogs, CGPA, branch)
    - Used for eligibility filtering before AI ranking
    """
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Multi-tenant: College Assignment
    college_id = Column(
        Integer, 
        ForeignKey("colleges.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True  # CRITICAL: Index for multi-tenant queries
    )
    
    # Personal Information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20))
    
    # Academic Information
    enrollment_number = Column(String(50), unique=True, index=True)
    university = Column(String(255))  # For legacy support
    degree = Column(String(100))
    major = Column(String(100))
    branch = Column(String(100))  # NEW: CS, ECE, ME, etc. - for eligibility
    graduation_year = Column(Integer)
    cgpa = Column(Float)
    
    # Placement Status (NEW: For eligibility filtering)
    has_backlogs = Column(Boolean, default=False, nullable=False)  # Active backlogs
    is_placed = Column(Boolean, default=False, nullable=False)  # Already placed
    
    # Additional Information
    bio = Column(Text)
    linkedin_url = Column(String(255))
    github_url = Column(String(255))
    portfolio_url = Column(String(255))
    
    # Skills (stored as JSON or comma-separated, depending on your preference)
    skills = Column(Text)  # Store as JSON string or use ARRAY in PostgreSQL
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="student_profile")
    college = relationship("College", back_populates="students")  # NEW: Multi-tenant relationship
    resumes = relationship("Resume", back_populates="student", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="student", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Student {self.first_name} {self.last_name} @ College {self.college_id}>"
    
    @property
    def full_name(self):
        """Get student's full name."""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_eligible_for_placement(self):
        """Check if student is eligible for new placements."""
        return not self.is_placed and self.cgpa is not None
