from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.offer import OfferStatus


class OfferCreate(BaseModel):
    application_id: int
    ctc: Optional[float] = None
    joining_date: Optional[datetime] = None
    offer_letter_url: Optional[str] = None


class OfferUpdate(BaseModel):
    ctc: Optional[float] = None
    joining_date: Optional[datetime] = None
    offer_letter_url: Optional[str] = None
    status: Optional[OfferStatus] = None


class OfferRespond(BaseModel):
    accept: bool  # True = ACCEPTED, False = DECLINED


class OfferResponse(BaseModel):
    id: int
    application_id: int
    student_id: int
    job_id: int
    ctc: Optional[float]
    offer_date: datetime
    joining_date: Optional[datetime]
    offer_letter_url: Optional[str]
    status: OfferStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
