from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Any

from app.database import get_db
from app.models.placement_officer import PlacementOfficer
from app.schemas.placement_officer import PlacementOfficerUpdate, PlacementOfficerProfileResponse
from app.api.deps import get_current_placement_officer

router = APIRouter()

@router.get("/me", response_model=PlacementOfficerProfileResponse)
async def get_my_profile(
    current_officer: PlacementOfficer = Depends(get_current_placement_officer)
) -> Any:
    return current_officer

@router.put("/me", response_model=PlacementOfficerProfileResponse)
async def update_my_profile(
    officer_in: PlacementOfficerUpdate,
    db: AsyncSession = Depends(get_db),
    current_officer: PlacementOfficer = Depends(get_current_placement_officer)
) -> Any:
    update_data = officer_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_officer, field, value)
        
    db.add(current_officer)
    await db.commit()
    await db.refresh(current_officer)
    return current_officer
