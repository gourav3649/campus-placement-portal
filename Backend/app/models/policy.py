from sqlalchemy import Column, Integer, Boolean, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from app.database import Base


class PlacementPolicy(Base):
    """
    Global placement policy configuration.
    
    Controls:
    - Max offers per student
    - Dream company thresholds
    - Multiple offer allowance
    
    FIX 1: Enforces single policy row via is_active unique constraint.
    """
    __tablename__ = "placement_policies"
    
    # FIX 1: Ensure only one active policy row
    __table_args__ = (
        UniqueConstraint('is_active', name='one_active_policy'),
    )

    id = Column(Integer, primary_key=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Offer limits
    max_offers_per_student = Column(Integer, default=1)
    allow_multiple_offers = Column(Boolean, default=False)

    # Dream company threshold (in LPA)
    dream_company_ctc_threshold = Column(Integer, default=10)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
