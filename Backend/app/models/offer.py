import enum
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class OfferStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    REVOKED = "REVOKED"


class Offer(Base):
    __tablename__ = "offers"
    
    __table_args__ = (
        UniqueConstraint('application_id', name='uq_offer_application_id'),
    )

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    
    status = Column(SQLEnum(OfferStatus), nullable=False, default=OfferStatus.PENDING)
    ctc = Column(Float, nullable=True)
    offer_letter_url = Column(String(500), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    application = relationship("Application", back_populates="offer", uselist=False)
