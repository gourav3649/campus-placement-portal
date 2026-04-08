from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.notification import NotificationType


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    message: str
    notification_type: NotificationType
    is_read: bool
    related_job_id: Optional[int]
    related_application_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True
