from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from typing import List, Any

from app.database import get_db
from app.models.application import Application, ApplicationStatus
from app.models.job import Job, DriveStatus
from app.models.student import Student
from app.schemas.application import ApplicationCreate, ApplicationResponse
from app.api.deps import get_current_student, get_current_placement_officer, get_current_recruiter
from app.services.eligibility import check_eligibility

router = APIRouter()

@router.post("/", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def apply_to_job(
    app_in: ApplicationCreate,
    db: AsyncSession = Depends(get_db),
    student: Student = Depends(get_current_student),
) -> Any:
    """Student applies to a job. Eligibility is checked automatically."""
    # Check job exists and is APPROVED
    result = await db.execute(select(Job).filter(Job.id == app_in.job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != DriveStatus.APPROVED:
        raise HTTPException(status_code=400, detail="This drive is not open for applications")
    if job.college_id != student.college_id:
        raise HTTPException(status_code=403, detail="This drive is not for your college")

    # Duplicate check
    existing = await db.execute(
        select(Application).filter(Application.student_id == student.id, Application.job_id == app_in.job_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="You have already applied to this drive")

    # Run eligibility check
    is_eligible, reasons = check_eligibility(student, job)
    final_status = ApplicationStatus.PENDING if is_eligible else ApplicationStatus.ELIGIBILITY_FAILED

    application = Application(
        student_id=student.id,
        job_id=app_in.job_id,
        status=final_status,
        is_eligible=is_eligible,
        eligibility_reasons=reasons if not is_eligible else None,
        resume_id=app_in.resume_id,
        cover_letter=app_in.cover_letter
    )
    db.add(application)
    await db.commit()
    
    # Eager load for response
    result = await db.execute(
        select(Application)
        .options(
            selectinload(Application.student),
            selectinload(Application.job).selectinload(Job.recruiter),
            selectinload(Application.rounds)
        )
        .filter(Application.id == application.id)
    )
    return result.scalar_one()

@router.get("/me", response_model=List[ApplicationResponse])
async def my_applications(
    db: AsyncSession = Depends(get_db),
    student: Student = Depends(get_current_student),
) -> Any:
    result = await db.execute(
        select(Application)
        .options(
            selectinload(Application.job).selectinload(Job.recruiter),
            selectinload(Application.rounds)
        )
        .filter(Application.student_id == student.id)
        .order_by(Application.applied_at.desc())
    )
    return result.scalars().unique().all()

@router.get("/{app_id}", response_model=ApplicationResponse)
async def get_application(
    app_id: int,
    db: AsyncSession = Depends(get_db),
    student: Student = Depends(get_current_student),
) -> Any:
    result = await db.execute(
        select(Application)
        .options(
            selectinload(Application.job).selectinload(Job.recruiter), 
            selectinload(Application.rounds)
        )
        .filter(Application.id == app_id, Application.student_id == student.id)
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app

@router.put("/{app_id}/withdraw", response_model=ApplicationResponse)
async def withdraw_application(
    app_id: int,
    db: AsyncSession = Depends(get_db),
    student: Student = Depends(get_current_student),
) -> Any:
    result = await db.execute(
        select(Application).filter(Application.id == app_id, Application.student_id == student.id)
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    if app.status not in (ApplicationStatus.PENDING, ApplicationStatus.REVIEWING):
        raise HTTPException(status_code=400, detail="Only PENDING or REVIEWING applications can be withdrawn")

    app.status = ApplicationStatus.WITHDRAWN
    await db.commit()
    
    # Eager load for response
    result = await db.execute(
        select(Application)
        .options(
            selectinload(Application.student),
            selectinload(Application.job).selectinload(Job.recruiter),
            selectinload(Application.rounds)
        )
        .filter(Application.id == app.id)
    )
    return result.scalar_one()

# -- Recruiter View --

@router.get("/recruiter/job/{job_id}", response_model=List[ApplicationResponse])
async def list_applications_for_job_recruiter(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    recruiter: Any = Depends(get_current_recruiter),
) -> Any:
    """Recruiter views all applications for their specific drive (read-only)."""
    # Verify job belongs to recruiter
    job_result = await db.execute(select(Job).filter(Job.id == job_id, Job.recruiter_id == recruiter.id))
    if not job_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Job not found or not yours")

    result = await db.execute(
        select(Application)
        .options(
            selectinload(Application.student),
            selectinload(Application.job).selectinload(Job.recruiter),
            selectinload(Application.rounds)
        )
        .filter(Application.job_id == job_id)
        .order_by(Application.applied_at.asc())
    )
    return result.scalars().unique().all()

# -- Officer View --

@router.get("/job/{job_id}", response_model=List[ApplicationResponse])
async def list_applications_for_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    officer: Any = Depends(get_current_placement_officer),
) -> Any:
    """Officer views all applications for a specific drive."""
    # Verify job belongs to officer's college
    job_result = await db.execute(select(Job).filter(Job.id == job_id, Job.college_id == officer.college_id))
    if not job_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Job not found")

    result = await db.execute(
        select(Application)
        .options(
            selectinload(Application.student),
            selectinload(Application.job).selectinload(Job.recruiter),
            selectinload(Application.rounds)
        )
        .filter(Application.job_id == job_id)
        .order_by(Application.ai_rank.asc().nullslast())
    )
    return result.scalars().unique().all()

@router.put("/officer/{app_id}/status", response_model=ApplicationResponse)
async def update_application_status(
    app_id: int,
    new_status: str, # Accept as string then convert or use enum
    db: AsyncSession = Depends(get_db),
    officer: Any = Depends(get_current_placement_officer),
) -> Any:
    """Officer manually updates an application status (e.g. REVIEWING -> SHORTLISTED)."""
    result = await db.execute(select(Application).filter(Application.id == app_id))
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    app.status = new_status
    await db.commit()
    
    # Eager load for response
    result = await db.execute(
        select(Application)
        .options(
            selectinload(Application.student),
            selectinload(Application.job).selectinload(Job.recruiter),
            selectinload(Application.rounds)
        )
        .filter(Application.id == app.id)
    )
    return result.scalar_one()
