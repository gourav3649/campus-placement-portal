from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.database import get_db
from app.api.deps import get_current_student, get_current_user
from app.models.student import Student
from app.models.application import Application
from app.schemas.student import StudentUpdate, StudentProfile
from app.schemas.application import Application as ApplicationSchema

router = APIRouter(prefix="/students", tags=["Students"])


@router.get("/me", response_model=StudentProfile)
async def get_my_profile(
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current student's profile.
    
    Requires: STUDENT role
    """
    # Get user email
    result = await db.execute(
        select(Student).filter(Student.id == current_student.id)
    )
    student = result.scalar_one_or_none()
    
    # Join with user to get email
    from app.models.user import User
    user_result = await db.execute(
        select(User).filter(User.id == student.user_id)
    )
    user = user_result.scalar_one()
    
    return StudentProfile(
        id=student.id,
        user_id=student.user_id,
        email=user.email,
        first_name=student.first_name,
        last_name=student.last_name,
        phone=student.phone,
        enrollment_number=student.enrollment_number,
        university=student.university,
        degree=student.degree,
        major=student.major,
        graduation_year=student.graduation_year,
        cgpa=student.cgpa,
        bio=student.bio,
        linkedin_url=student.linkedin_url,
        github_url=student.github_url,
        portfolio_url=student.portfolio_url,
        skills=student.skills,
        created_at=student.created_at
    )


@router.put("/me", response_model=StudentProfile)
async def update_my_profile(
    profile_update: StudentUpdate,
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current student's profile.
    
    Requires: STUDENT role
    """
    # Check if placement status is changing
    placement_status_changed = False
    if 'is_placed' in profile_update.model_dump(exclude_unset=True):
        old_is_placed = current_student.is_placed
        new_is_placed = profile_update.is_placed
        if old_is_placed != new_is_placed:
            placement_status_changed = True
            print(f"[Students] Student {current_student.id} placement status changing: {old_is_placed} -> {new_is_placed}")
    
    # Update only provided fields
    update_data = profile_update.model_dump(exclude_unset=True)
    
    # Convert URLs to strings
    for url_field in ['linkedin_url', 'github_url', 'portfolio_url']:
        if url_field in update_data and update_data[url_field] is not None:
            update_data[url_field] = str(update_data[url_field])
    
    for field, value in update_data.items():
        setattr(current_student, field, value)
    
    await db.commit()
    await db.refresh(current_student)
    
    # TRIGGER ELIGIBILITY REVALIDATION if placement status changed
    if placement_status_changed:
        from app.eligibility import EligibilityService
        from app.models.application import Application
        eligibility_service = EligibilityService()
        
        # Get all jobs this student applied to
        apps_result = await db.execute(
            select(Application).filter(Application.student_id == current_student.id)
        )
        applications = apps_result.scalars().all()
        
        if applications:
            print(f"[Students] Revalidating eligibility for {len(applications)} applications...")
            revalidated_count = 0
            for app in applications:
                is_eligible, reasons = await eligibility_service.check_application_eligibility(
                    db, app, update_db=True
                )
                revalidated_count += 1
            print(f"[Students] Revalidated {revalidated_count} applications for student {current_student.id}")
    
    # Get user email
    from app.models.user import User
    user_result = await db.execute(
        select(User).filter(User.id == current_student.user_id)
    )
    user = user_result.scalar_one()
    
    return StudentProfile(
        id=current_student.id,
        user_id=current_student.user_id,
        email=user.email,
        first_name=current_student.first_name,
        last_name=current_student.last_name,
        phone=current_student.phone,
        enrollment_number=current_student.enrollment_number,
        university=current_student.university,
        degree=current_student.degree,
        major=current_student.major,
        graduation_year=current_student.graduation_year,
        cgpa=current_student.cgpa,
        bio=current_student.bio,
        linkedin_url=current_student.linkedin_url,
        github_url=current_student.github_url,
        portfolio_url=current_student.portfolio_url,
        skills=current_student.skills,
        created_at=current_student.created_at
    )


@router.get("/me/applications", response_model=List[ApplicationSchema])
async def get_my_applications(
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all applications submitted by current student.
    
    Requires: STUDENT role
    """
    result = await db.execute(
        select(Application)
        .filter(Application.student_id == current_student.id)
        .order_by(Application.applied_at.desc())
    )
    applications = result.scalars().all()
    
    return applications


@router.get("/{student_id}", response_model=StudentProfile)
async def get_student_profile(
    student_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get a specific student's profile.
    
    Public endpoint (authenticated users only).
    """
    result = await db.execute(
        select(Student).filter(Student.id == student_id)
    )
    student = result.scalar_one_or_none()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Get user email
    from app.models.user import User
    user_result = await db.execute(
        select(User).filter(User.id == student.user_id)
    )
    user = user_result.scalar_one()
    
    return StudentProfile(
        id=student.id,
        user_id=student.user_id,
        email=user.email,
        first_name=student.first_name,
        last_name=student.last_name,
        phone=student.phone,
        enrollment_number=student.enrollment_number,
        university=student.university,
        degree=student.degree,
        major=student.major,
        graduation_year=student.graduation_year,
        cgpa=student.cgpa,
        bio=student.bio,
        linkedin_url=student.linkedin_url,
        github_url=student.github_url,
        portfolio_url=student.portfolio_url,
        skills=student.skills,
        created_at=student.created_at
    )
