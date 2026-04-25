from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Round(Base):
    """
    Job-level round template.

    Defines the ordered interview/evaluation rounds for a placement drive.
    A job has many rounds; each application is evaluated against each round.

    UNIQUE(job_id, round_number) — no duplicate round numbers per job.
    """
    __tablename__ = "rounds"

    __table_args__ = (
        UniqueConstraint("job_id", "round_number", name="uq_job_round_number"),
        CheckConstraint("round_number > 0", name="check_round_number_positive"),
    )

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)

    round_number = Column(Integer, nullable=False)
    name = Column(String(100), nullable=False)          # e.g. "Aptitude Test", "Technical Interview"
    is_eliminatory = Column(Boolean, default=True, nullable=False)
    max_score = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    job = relationship("Job", back_populates="rounds")
    evaluations = relationship("Evaluation", back_populates="round", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Round {self.round_number} ({self.name}) for Job {self.job_id}>"
