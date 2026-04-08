from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.application_round import RoundResult


class RoundCreate(BaseModel):
    round_number: int
    round_name: str
    result: RoundResult = RoundResult.PENDING
    scheduled_at: Optional[datetime] = None
    notes: Optional[str] = None


class RoundUpdate(BaseModel):
    round_name: Optional[str] = None
    result: Optional[RoundResult] = None
    scheduled_at: Optional[datetime] = None
    notes: Optional[str] = None


class RoundResponse(BaseModel):
    id: int
    application_id: int
    round_number: int
    round_name: str
    result: RoundResult
    scheduled_at: Optional[datetime]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
