import enum
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class RoundResult(str, enum.Enum):
    PENDING = "PENDING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    ABSENT = "ABSENT"


class ApplicationRound(Base):
    __tablename__ = "application_rounds"
    
    # FIX 3: Enforce unique round_number per application
    __table_args__ = (
        UniqueConstraint('application_id', 'round_number', name='uq_app_round_number'),
    )

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    updated_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    round_number = Column(Integer, nullable=False)
    round_name = Column(String(100), nullable=False)  # e.g. "Online Test", "Technical Interview"
    result = Column(SQLEnum(RoundResult), nullable=False, default=RoundResult.PENDING)
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    application = relationship("Application", back_populates="rounds")
