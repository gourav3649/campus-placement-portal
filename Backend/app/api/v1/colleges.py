from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Any

from app.database import get_db
from app.models.college import College
from app.schemas.college import CollegeCreate, CollegeUpdate, CollegeResponse
from app.api.deps import get_current_admin

router = APIRouter()

@router.post("/", response_model=CollegeResponse)
async def create_college(
    college_in: CollegeCreate,
    db: AsyncSession = Depends(get_db),
    admin: Any = Depends(get_current_admin)
) -> Any:
    db_college = College(
        name=college_in.name,
        location=college_in.location,
        website=college_in.website
    )
    db.add(db_college)
    await db.commit()
    await db.refresh(db_college)
    return db_college

@router.get("/", response_model=List[CollegeResponse])
async def list_colleges(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100
) -> Any:
    # Anyone can list colleges (needed for registration dropdown)
    result = await db.execute(select(College).offset(skip).limit(limit))
    return result.scalars().all()

@router.put("/{college_id}", response_model=CollegeResponse)
async def update_college(
    college_id: int,
    college_in: CollegeUpdate,
    db: AsyncSession = Depends(get_db),
    admin: Any = Depends(get_current_admin)
) -> Any:
    result = await db.execute(select(College).filter(College.id == college_id))
    college = result.scalar_one_or_none()
    
    if not college:
        raise HTTPException(status_code=404, detail="College not found")
        
    update_data = college_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(college, field, value)
        
    db.add(college)
    await db.commit()
    await db.refresh(college)
    return college
