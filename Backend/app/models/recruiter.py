from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Recruiter(Base):
    """Recruiter profile model."""
    __tablename__ = "recruiters"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Company Information
    company_name = Column(String(255), nullable=False, index=True)
    company_website = Column(String(255))
    company_description = Column(Text)
    
    # Recruiter Information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    position = Column(String(100))
    phone = Column(String(20))
    
    # Additional Information
    linkedin_url = Column(String(255))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="recruiter_profile")
    jobs = relationship("Job", back_populates="recruiter", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Recruiter {self.first_name} {self.last_name} - {self.company_name}>"
