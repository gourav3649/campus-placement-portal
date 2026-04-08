from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Any

from app.database import get_db
from app.models.student import Student
from app.schemas.student import StudentUpdate, StudentProfileResponse
from app.api.deps import get_current_student, get_current_placement_officer

router = APIRouter()

@router.get("/me", response_model=StudentProfileResponse)
async def get_my_profile(
    current_student: Student = Depends(get_current_student)
) -> Any:
    return current_student

@router.put("/me", response_model=StudentProfileResponse)
async def update_my_profile(
    student_in: StudentUpdate,
    db: AsyncSession = Depends(get_db),
    current_student: Student = Depends(get_current_student)
) -> Any:
    update_data = student_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_student, field, value)
        
    db.add(current_student)
    await db.commit()
    await db.refresh(current_student)
    return current_student

@router.get("/", response_model=List[StudentProfileResponse])
async def list_students(
    db: AsyncSession = Depends(get_db),
    officer: Any = Depends(get_current_placement_officer),
    skip: int = 0,
    limit: int = 100
) -> Any:
    # Officer can only see students in their college
    result = await db.execute(
        select(Student)
        .filter(Student.college_id == officer.college_id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()
