"""Placement Officer model - College admin role."""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class PlacementOfficer(Base):
    """
    Placement Officer - College-level admin role.
    
    Responsibilities:
    - Approve job postings for their college
    - View all students in their college
    - View all applications from their college students
    - Set eligibility rules for drives
    - Manage placement drives
    - View analytics for their college
    
    Security:
    - Can ONLY access data from their own college
    - Cannot see students/jobs from other colleges
    - Enforced by college_id FK constraint
    """
    __tablename__ = "placement_officers"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    college_id = Column(Integer, ForeignKey("colleges.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Profile Information
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(20))
    designation = Column(String(100))  # e.g., "Training & Placement Officer"
    department = Column(String(100))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="placement_officer")
    college = relationship("College", back_populates="placement_officers")
    
    def __repr__(self):
        return f"<PlacementOfficer {self.id}: {self.name} @ College {self.college_id}>"
