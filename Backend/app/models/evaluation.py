import enum
from sqlalchemy import Column, Integer, Float, Text, ForeignKey, DateTime, Enum as SQLEnum, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class EvaluationStatus(str, enum.Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"


class Evaluation(Base):
    """
    Recruiter evaluation of one application in one round.

    Records score, pass/fail result, and feedback for a candidate
    after completing a specific round of the hiring process.

    UNIQUE(application_id, round_id) — one evaluation per application per round.
    """
    __tablename__ = "evaluations"

    __table_args__ = (
        UniqueConstraint("application_id", "round_id", name="uq_application_round_evaluation"),
        Index("idx_evaluation_application", "application_id"),
        Index("idx_evaluation_round", "round_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    round_id = Column(Integer, ForeignKey("rounds.id", ondelete="CASCADE"), nullable=False)

    status = Column(SQLEnum(EvaluationStatus), nullable=False)
    score = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)
    evaluated_by = Column(Integer, ForeignKey("recruiters.id", ondelete="SET NULL"), nullable=True)

    evaluated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    application = relationship("Application", back_populates="evaluations")
    round = relationship("Round", back_populates="evaluations")

    def __repr__(self):
        return f"<Evaluation app={self.application_id} round={self.round_id} status={self.status}>"
