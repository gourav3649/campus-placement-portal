"""
Policy Service - PHASE 1: Policy Engine (Minimal)

Load and manage global placement policies.
Only ONE policy exists per instance.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.models.policy import PlacementPolicy


async def get_active_policy(db: AsyncSession) -> PlacementPolicy:
    """
    Get the active global placement policy.
    
    FIX 1: Use pessimistic locking to prevent duplicate policy rows.
    If no policy exists, create one with defaults:
    - max_offers_per_student: 1
    - allow_multiple_offers: False
    - dream_company_ctc_threshold: 10 LPA
    
    Returns: PlacementPolicy instance
    """
    # FIX: Filter active policy with lock to prevent duplicates
    result = await db.execute(select(PlacementPolicy).filter(PlacementPolicy.is_active == True).with_for_update())
    policy = result.scalar_one_or_none()

    if not policy:
        # Create default policy
        policy = PlacementPolicy(
            max_offers_per_student=1,
            allow_multiple_offers=False,
            dream_company_ctc_threshold=10,
            is_active=True
        )
        
        # FIX 2: Handle race condition during policy creation
        try:
            db.add(policy)
            await db.commit()
        except IntegrityError:
            # Another request already created the policy
            await db.rollback()
            result = await db.execute(select(PlacementPolicy).filter(PlacementPolicy.is_active == True))
            policy = result.scalar_one()
        
        await db.refresh(policy)

    return policy


def is_dream_job(ctc: float, threshold: int) -> bool:
    """
    Determine if a job is a dream company job.
    
    Args:
        ctc: Offer CTC in LPA
        threshold: Dream company threshold in LPA
    
    Returns: True if ctc >= threshold
    """
    if ctc is None:
        return False
    return ctc >= threshold


def validate_application_policy(student, job):
    """
    Validate student can apply based on placement policy.
    
    Raises HTTPException if student cannot apply.
    """
    from fastapi import HTTPException
    
    if student.is_placed:
        raise HTTPException(status_code=403, detail="Cannot apply after being placed")
