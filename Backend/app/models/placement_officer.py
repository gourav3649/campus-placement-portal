from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class PlacementOfficer(Base):
    __tablename__ = "placement_officers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    college_id = Column(Integer, ForeignKey("colleges.id"), nullable=False, index=True)
    
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    designation = Column(String(100), nullable=True)
    department = Column(String(100), nullable=True)

    # Relationships
    user = relationship("User", back_populates="placement_officer_profile")
    college = relationship("College", back_populates="placement_officers")
