"""PHASE 4: Notification service for creating in-app notifications."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.notification import Notification, NotificationType


async def create_notification(
    db: AsyncSession,
    *,
    user_id: int,
    title: str,
    message: str,
    notification_type: NotificationType,
    related_job_id: int | None = None,
    related_application_id: int | None = None,
) -> Notification | None:
    """PHASE 4: Create notification and flush (caller handles commit).
    
    FIX: Prevent duplicate notifications only when ALL fields match:
    user_id, notification_type, related_application_id, related_job_id, title.
    This ensures valid repeated events are allowed.
    Returns None if duplicate found, otherwise returns created Notification.
    """
    # Check for duplicate notification (all fields must match)
    existing = await db.execute(
        select(Notification).filter(
            Notification.user_id == user_id,
            Notification.notification_type == notification_type,
            Notification.related_application_id == related_application_id,
            Notification.related_job_id == related_job_id,
            Notification.title == title,
        )
    )
    if existing.scalar_one_or_none():
        # Duplicate found, skip creation
        return None
    
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        related_job_id=related_job_id,
        related_application_id=related_application_id,
    )
    db.add(notification)
    await db.flush()
    return notification
