from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    college_id = Column(Integer, ForeignKey("colleges.id"), nullable=False, index=True)
    
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    branch = Column(String(100), nullable=False)
    graduation_year = Column(Integer, nullable=False)
    cgpa = Column(Float, nullable=False)
    skills = Column(Text, nullable=True) # comma separated
    bio = Column(Text, nullable=True)
    
    is_placed = Column(Boolean, default=False)
    has_backlogs = Column(Boolean, default=False)

    # Relationships
    user = relationship("User", back_populates="student_profile")
    college = relationship("College", back_populates="students")
    resumes = relationship("Resume", back_populates="student", cascade="all, delete-orphan")
