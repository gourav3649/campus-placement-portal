"""
Notification service helper — call create_notification() from any route
to send an in-app notification to a user.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.notification import Notification, NotificationType


async def create_notification(
    db: AsyncSession,
    *,
    user_id: int,
    title: str,
    message: str,
    notification_type: NotificationType = NotificationType.GENERAL,
    related_job_id: int | None = None,
    related_application_id: int | None = None,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        related_job_id=related_job_id,
        related_application_id=related_application_id,
    )
    db.add(notification)
    # Caller is responsible for commit — this lets us batch with other writes
    return notification
