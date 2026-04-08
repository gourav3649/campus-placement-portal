from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Any

from app.database import get_db
from app.models.recruiter import Recruiter
from app.schemas.recruiter import RecruiterUpdate, RecruiterProfileResponse
from app.api.deps import get_current_recruiter, get_current_placement_officer

router = APIRouter()

@router.get("/me", response_model=RecruiterProfileResponse)
async def get_my_profile(
    db: AsyncSession = Depends(get_db),
    current_recruiter: Recruiter = Depends(get_current_recruiter)
) -> Any:
    # Eager load user for response model
    result = await db.execute(
        select(Recruiter)
        .options(selectinload(Recruiter.user))
        .filter(Recruiter.id == current_recruiter.id)
    )
    return result.scalar_one()

@router.put("/me", response_model=RecruiterProfileResponse)
async def update_my_profile(
    recruiter_in: RecruiterUpdate,
    db: AsyncSession = Depends(get_db),
    current_recruiter: Recruiter = Depends(get_current_recruiter)
) -> Any:
    update_data = recruiter_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_recruiter, field, value)
        
    db.add(current_recruiter)
    await db.commit()
    await db.refresh(current_recruiter)
    return current_recruiter

@router.get("/", response_model=List[RecruiterProfileResponse])
async def list_recruiters(
    db: AsyncSession = Depends(get_db),
    officer: Any = Depends(get_current_placement_officer),
    skip: int = 0,
    limit: int = 100
) -> Any:
    result = await db.execute(
        select(Recruiter)
        .options(selectinload(Recruiter.user))
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

@router.put("/{recruiter_id}/verify", response_model=RecruiterProfileResponse)
async def verify_recruiter(
    recruiter_id: int,
    is_verified: bool,
    db: AsyncSession = Depends(get_db),
    officer: Any = Depends(get_current_placement_officer)
) -> Any:
    result = await db.execute(
        select(Recruiter)
        .options(selectinload(Recruiter.user))
        .filter(Recruiter.id == recruiter_id)
    )
    recruiter = result.scalar_one_or_none()
    
    if not recruiter:
        raise HTTPException(status_code=404, detail="Recruiter not found")
        
    recruiter.is_verified = is_verified
    db.add(recruiter)
    await db.commit()
    await db.refresh(recruiter)
    return recruiter
