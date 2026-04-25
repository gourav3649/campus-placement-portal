from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.evaluation import EvaluationStatus


class EvaluationCreate(BaseModel):
    round_id: int
    status: EvaluationStatus
    score: Optional[float] = None
    feedback: Optional[str] = None


class EvaluationResponse(BaseModel):
    id: int
    application_id: int
    round_id: int
    status: EvaluationStatus
    score: Optional[float]
    feedback: Optional[str]
    evaluated_by: Optional[int]
    evaluated_at: datetime

    class Config:
        from_attributes = True
