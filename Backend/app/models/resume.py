from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Resume(Base):
    """Resume model for storing parsed resume data."""
    __tablename__ = "resumes"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    
    # File Information
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)  # Size in bytes
    mime_type = Column(String(100))
    
    # Parsed Content
    raw_text = Column(Text)  # Full extracted text
    
    # AI-Extracted Information (JSON format)
    parsed_data = Column(Text)  # Store full parsed JSON
    
    # Specific parsed fields for easy querying
    extracted_skills = Column(Text)  # JSON array of skills
    extracted_experience = Column(Text)  # JSON array of experience
    extracted_education = Column(Text)  # JSON array of education
    extracted_certifications = Column(Text)  # JSON array of certifications
    
    # Semantic Embeddings (for AI matching)
    embedding_vector = Column(Text)  # Store as JSON or binary
    
    # Metadata
    is_primary = Column(Boolean, default=False)  # Primary resume for the student
    parse_status = Column(String(50), default="pending")  # pending, processing, completed, failed
    parse_error = Column(Text)  # Error message if parsing failed
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    student = relationship("Student", back_populates="resumes")
    
    def __repr__(self):
        return f"<Resume {self.filename} for Student {self.student_id}>"
