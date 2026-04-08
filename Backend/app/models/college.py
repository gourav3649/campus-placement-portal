from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

class College(Base):
    __tablename__ = "colleges"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    location = Column(String(255), nullable=True)
    website = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationships
    students = relationship("Student", back_populates="college", cascade="all, delete-orphan")
    placement_officers = relationship("PlacementOfficer", back_populates="college", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="college", cascade="all, delete-orphan")
