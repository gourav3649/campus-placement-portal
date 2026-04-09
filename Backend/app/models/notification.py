import enum
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class NotificationType(str, enum.Enum):
    """PHASE 4: Notification types for key events."""
    APPLICATION_SUBMITTED = "application_submitted"
    STATUS_UPDATED = "status_updated"
    ROUND_ADDED = "round_added"
    ROUND_RESULT = "round_result"
    OFFER_EXTENDED = "offer_extended"
    OFFER_ACCEPTED = "offer_accepted"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    related_job_id = Column(Integer, ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True)
    related_application_id = Column(Integer, ForeignKey("applications.id", ondelete="SET NULL"), nullable=True)

    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(SQLEnum(NotificationType), nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
