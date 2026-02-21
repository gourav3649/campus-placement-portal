from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.database import get_db
from app.api.deps import get_current_recruiter, get_current_user
from app.models.recruiter import Recruiter
from app.models.job import Job
from app.schemas.recruiter import RecruiterUpdate, RecruiterProfile
from app.schemas.job import Job as JobSchema

router = APIRouter(prefix="/recruiters", tags=["Recruiters"])


@router.get("/me", response_model=RecruiterProfile)
async def get_my_profile(
    current_recruiter: Recruiter = Depends(get_current_recruiter),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current recruiter's profile.
    
    Requires: RECRUITER role
    """
    # Get user email
    from app.models.user import User
    user_result = await db.execute(
        select(User).filter(User.id == current_recruiter.user_id)
    )
    user = user_result.scalar_one()
    
    return RecruiterProfile(
        id=current_recruiter.id,
        user_id=current_recruiter.user_id,
        email=user.email,
        company_name=current_recruiter.company_name,
        company_website=current_recruiter.company_website,
        company_description=current_recruiter.company_description,
        first_name=current_recruiter.first_name,
        last_name=current_recruiter.last_name,
        position=current_recruiter.position,
        phone=current_recruiter.phone,
        linkedin_url=current_recruiter.linkedin_url,
        created_at=current_recruiter.created_at
    )


@router.put("/me", response_model=RecruiterProfile)
async def update_my_profile(
    profile_update: RecruiterUpdate,
    current_recruiter: Recruiter = Depends(get_current_recruiter),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current recruiter's profile.
    
    Requires: RECRUITER role
    """
    # Update only provided fields
    update_data = profile_update.model_dump(exclude_unset=True)
    
    # Convert URLs to strings
    for url_field in ['company_website', 'linkedin_url']:
        if url_field in update_data and update_data[url_field] is not None:
            update_data[url_field] = str(update_data[url_field])
    
    for field, value in update_data.items():
        setattr(current_recruiter, field, value)
    
    await db.commit()
    await db.refresh(current_recruiter)
    
    # Get user email
    from app.models.user import User
    user_result = await db.execute(
        select(User).filter(User.id == current_recruiter.user_id)
    )
    user = user_result.scalar_one()
    
    return RecruiterProfile(
        id=current_recruiter.id,
        user_id=current_recruiter.user_id,
        email=user.email,
        company_name=current_recruiter.company_name,
        company_website=current_recruiter.company_website,
        company_description=current_recruiter.company_description,
        first_name=current_recruiter.first_name,
        last_name=current_recruiter.last_name,
        position=current_recruiter.position,
        phone=current_recruiter.phone,
        linkedin_url=current_recruiter.linkedin_url,
        created_at=current_recruiter.created_at
    )


@router.get("/me/jobs", response_model=List[JobSchema])
async def get_my_jobs(
    current_recruiter: Recruiter = Depends(get_current_recruiter),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all jobs posted by current recruiter.
    
    Requires: RECRUITER role
    """
    result = await db.execute(
        select(Job)
        .filter(Job.recruiter_id == current_recruiter.id)
        .order_by(Job.created_at.desc())
    )
    jobs = result.scalars().all()
    
    return jobs


@router.get("/{recruiter_id}", response_model=RecruiterProfile)
async def get_recruiter_profile(
    recruiter_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get a specific recruiter's profile.
    
    Public endpoint (authenticated users only).
    """
    result = await db.execute(
        select(Recruiter).filter(Recruiter.id == recruiter_id)
    )
    recruiter = result.scalar_one_or_none()
    
    if not recruiter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recruiter not found"
        )
    
    # Get user email
    from app.models.user import User
    user_result = await db.execute(
        select(User).filter(User.id == recruiter.user_id)
    )
    user = user_result.scalar_one()
    
    return RecruiterProfile(
        id=recruiter.id,
        user_id=recruiter.user_id,
        email=user.email,
        company_name=recruiter.company_name,
        company_website=recruiter.company_website,
        company_description=recruiter.company_description,
        first_name=recruiter.first_name,
        last_name=recruiter.last_name,
        position=recruiter.position,
        phone=recruiter.phone,
        linkedin_url=recruiter.linkedin_url,
        created_at=recruiter.created_at
    )
