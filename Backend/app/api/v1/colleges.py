"""College API endpoints - Multi-tenant college management."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional

from app.database import get_db
from app.api.deps import get_current_user, get_current_placement_officer, require_role
from app.core.rbac import Role, Permission, require_permission
from app.models.college import College
from app.models.placement_officer import PlacementOfficer
from app.models.student import Student
from app.models.job import Job  
from app.schemas.college import College as CollegeSchema, CollegeCreate, CollegeUpdate, CollegeWithStats

router = APIRouter(prefix="/colleges", tags=["Colleges"])


@router.post("", response_model=CollegeSchema, status_code=status.HTTP_201_CREATED)
async def create_college(
    college_data: CollegeCreate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new college.
    
    Requires: ADMIN role with MANAGE_COLLEGES permission
    """
    require_permission(Permission.MANAGE_COLLEGES)(current_user.role)
    
    # Check if college with same name already exists
    existing = await db.execute(
        select(College).filter(College.name == college_data.name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"College with name '{college_data.name}' already exists"
        )
    
    # Create college
    college = College(**college_data.model_dump())
    
    db.add(college)
    await db.commit()
    await db.refresh(college)
    
    return college


@router.get("", response_model=List[CollegeSchema])
async def list_colleges(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    List all colleges.
    
    Accessible to all authenticated users.
    Students see all colleges (for registration).
    Placement officers see all colleges (for reference).
    """
    query = select(College)
    
    # Apply filters
    if is_active is not None:
        query = query.filter(College.is_active == (1 if is_active else 0))
    
    if search:
        query = query.filter(
            College.name.ilike(f"%{search}%") | 
            College.location.ilike(f"%{search}%")
        )
    
    # Pagination
    query = query.offset(skip).limit(limit).order_by(College.name)
    
    result = await db.execute(query)
    colleges = result.scalars().all()
    
    return colleges


@router.get("/{college_id}", response_model=CollegeWithStats)
async def get_college(
    college_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get college details with statistics.
    
    Accessible to all authenticated users.
    """
    result = await db.execute(select(College).filter(College.id == college_id))
    college = result.scalar_one_or_none()
    
    if not college:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="College not found"
        )
    
    # Get statistics
    student_count_result = await db.execute(
        select(func.count()).select_from(Student).filter(Student.college_id == college_id)
    )
    student_count = student_count_result.scalar() or 0
    
    placement_officer_count_result = await db.execute(
        select(func.count()).select_from(PlacementOfficer).filter(PlacementOfficer.college_id == college_id)
    )
    placement_officer_count = placement_officer_count_result.scalar() or 0
    
    active_job_count_result = await db.execute(
        select(func.count()).select_from(Job).filter(
            Job.college_id == college_id,
            Job.status == "open"
        )
    )
    active_job_count = active_job_count_result.scalar() or 0
    
    # Build response
    college_dict = {
        **college.__dict__,
        "student_count": student_count,
        "active_job_count": active_job_count,
        "placement_officer_count": placement_officer_count
    }
    
    return CollegeWithStats.model_validate(college_dict)


@router.put("/{college_id}", response_model=CollegeSchema)
async def update_college(
    college_id: int,
    college_update: CollegeUpdate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update college information.
    
    Requires: ADMIN role with MANAGE_COLLEGES permission
    """
    require_permission(Permission.MANAGE_COLLEGES)(current_user.role)
    
    result = await db.execute(select(College).filter(College.id == college_id))
    college = result.scalar_one_or_none()
    
    if not college:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="College not found"
        )
    
    # Update fields
    update_data = college_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(college, field, value)
    
    await db.commit()
    await db.refresh(college)
    
    return college


@router.delete("/{college_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_college(
    college_id: int,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a college.
    
    Requires: ADMIN role with MANAGE_COLLEGES permission
    WARNING: This will cascade delete all students, placement officers, and jobs!
    """
    require_permission(Permission.MANAGE_COLLEGES)(current_user.role)
    
    result = await db.execute(select(College).filter(College.id == college_id))
    college = result.scalar_one_or_none()
    
    if not college:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="College not found"
        )
    
    await db.delete(college)
    await db.commit()
    
    return None
