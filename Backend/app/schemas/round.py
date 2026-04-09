from pydantic import BaseModel, field_validator, model_validator
from typing import Optional
from datetime import datetime
from app.models.application_round import RoundResult, Recommendation


class RoundCreate(BaseModel):
    """PHASE 3: Round creation with evaluation fields."""
    round_number: int
    round_name: str
    result: RoundResult = RoundResult.PENDING
    scheduled_at: Optional[datetime] = None
    notes: Optional[str] = None
    
    # PHASE 3: Recruiter evaluation
    score: Optional[int] = None
    feedback: Optional[str] = None
    recommendation: Optional[Recommendation] = None
    
    @field_validator('score')
    def validate_score(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError('Score must be between 0 and 100')
        return v
    
    @model_validator(mode='after')
    def validate_result_vs_recommendation(self):
        """FIX 2: If result is FAILED, recommendation cannot be HIRE or STRONG_HIRE."""
        if self.result == RoundResult.FAILED:
            if self.recommendation in (Recommendation.HIRE, Recommendation.STRONG_HIRE):
                raise ValueError('Cannot recommend HIRE/STRONG_HIRE for FAILED result')
        return self
    
    @model_validator(mode='after')
    def validate_score_requires_non_pending(self):
        """FIX 3: If score is provided, result must NOT be PENDING."""
        if self.score is not None and self.result == RoundResult.PENDING:
            raise ValueError('Score cannot be provided for PENDING result')
        return self


class RoundUpdate(BaseModel):
    """PHASE 3: Round update with evaluation fields."""
    round_name: Optional[str] = None
    result: Optional[RoundResult] = None
    scheduled_at: Optional[datetime] = None
    notes: Optional[str] = None
    
    # PHASE 3: Recruiter evaluation can be updated
    score: Optional[int] = None
    feedback: Optional[str] = None
    recommendation: Optional[Recommendation] = None
    
    @field_validator('score')
    def validate_score(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError('Score must be between 0 and 100')
        return v
    
    @model_validator(mode='after')
    def validate_result_vs_recommendation(self):
        """FIX 2 (NEW): Recommendation can ONLY be set if result == PASSED."""
        if self.recommendation is not None and self.result != RoundResult.PASSED:
            raise ValueError('Recommendation can only be set for PASSED result')
        return self
    
    @model_validator(mode='after')
    def validate_score_requires_non_pending(self):
        """If score is provided, result must NOT be PENDING."""
        if self.score is not None and self.result == RoundResult.PENDING:
            raise ValueError('Score cannot be provided for PENDING result')
        return self


class RoundResponse(BaseModel):
    """PHASE 3: Round response with evaluation data."""
    id: int
    application_id: int
    round_number: int
    round_name: str
    result: RoundResult
    scheduled_at: Optional[datetime]
    notes: Optional[str]
    
    # PHASE 3: Evaluation fields
    score: Optional[int]
    feedback: Optional[str]
    recommendation: Optional[Recommendation]
    evaluated_by_id: Optional[int]  # FIX 1: Evaluator tracking
    
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
