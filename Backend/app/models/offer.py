import enum
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class OfferStatus(str, enum.Enum):
    EXTENDED = "EXTENDED"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
    REVOKED = "REVOKED"


class Offer(Base):
    __tablename__ = "offers"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), unique=True, nullable=False)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)

    ctc = Column(Float, nullable=True)           # in LPA
    offer_date = Column(DateTime(timezone=True), server_default=func.now())
    joining_date = Column(DateTime(timezone=True), nullable=True)
    offer_letter_url = Column(String(500), nullable=True)
    status = Column(SQLEnum(OfferStatus), nullable=False, default=OfferStatus.EXTENDED)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    application = relationship("Application", back_populates="offer")
    student = relationship("Student", backref="offers")
    job = relationship("Job", back_populates="offers")
