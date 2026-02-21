"""Placement Officer API endpoints - College-level administrative operations."""

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional

from app.database import get_db, AsyncSessionLocal
from app.api.deps import get_current_user, get_current_placement_officer
from app.core.rbac import Role, Permission, require_permission
from app.models.placement_officer import PlacementOfficer
from app.models.student import Student
from app.models.job import Job, DriveStatus
from app.models.application import Application, ApplicationStatus
from app.schemas.placement_officer import (
    PlacementOfficer as PlacementOfficerSchema,
    PlacementOfficerCreate,
    PlacementOfficerUpdate
)
from app.schemas.student import Student as StudentSchema
from app.schemas.job import Job as JobSchema

from app.eligibility import EligibilityService

router = APIRouter(prefix="/placement-officers", tags=["Placement Officers"])


@router.post("", response_model=PlacementOfficerSchema, status_code=status.HTTP_201_CREATED)
async def create_placement_officer(
    officer_data: PlacementOfficerCreate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new placement officer.
    
    Requires: ADMIN role
    
    User must already exist with PLACEMENT_OFFICER role.
    """
    require_permission(Permission.MANAGE_USERS)(current_user.role)
    
    # Check if user already has placement officer profile
    existing = await db.execute(
        select(PlacementOfficer).filter(PlacementOfficer.user_id == officer_data.user_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already has a placement officer profile"
        )
    
    # Create placement officer
    officer = PlacementOfficer(**officer_data.model_dump())
    
    db.add(officer)
    await db.commit()
    await db.refresh(officer)
    
    return officer


@router.get("/me", response_model=PlacementOfficerSchema)
async def get_my_profile(
    current_officer: PlacementOfficer = Depends(get_current_placement_officer),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current placement officer's profile.
    
    Requires: PLACEMENT_OFFICER role
    """
    return current_officer    


@router.get("/college/{college_id}/students", response_model=List[StudentSchema])
async def get_college_students(
    college_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    branch: Optional[str] = None,
    is_placed: Optional[bool] = None,
    min_cgpa: Optional[float] = None,
    current_officer: PlacementOfficer = Depends(get_current_placement_officer),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all students in placement officer's college.
    
    Requires: PLACEMENT_OFFICER role with VIEW_ALL_STUDENTS permission
    Multi-tenant: Can only view students from own college
    """
    require_permission(Permission.VIEW_ALL_STUDENTS)(current_officer.user.role)
    
    # MULTI-TENANT SECURITY: Ensure officer can only access their college
    if college_id != current_officer.college_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access students from other colleges"
        )
    
    # Build query
    query = select(Student).filter(Student.college_id == college_id)
    
    # Apply filters
    if branch:
        query = query.filter(Student.branch == branch)
    if is_placed is not None:
        query = query.filter(Student.is_placed == is_placed)
    if min_cgpa is not None:
        query = query.filter(Student.cgpa >= min_cgpa)
    
    # Pagination
    query = query.offset(skip).limit(limit).order_by(Student.last_name, Student.first_name)
    
    result = await db.execute(query)
    students = result.scalars().all()
    
    return students


@router.post("/jobs/{job_id}/approve", response_model=JobSchema)
async def approve_job(
    job_id: int,
    approved: bool = True,
    current_officer: PlacementOfficer = Depends(get_current_placement_officer),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db)
):
    """
    Approve or reject a job drive.
    
    Requires: PLACEMENT_OFFICER role with APPROVE_JOB permission
    Multi-tenant: Can only approve jobs for own college
    
    Workflow:
    1. Recruiter creates job → drive_status = DRAFT
    2. Placement officer reviews job
    3. If approved → drive_status = APPROVED, trigger eligibility checks
    4. If rejected → drive_status = REJECTED
    """
    require_permission(Permission. APPROVE_JOB)(current_officer.user.role)
    
    # Fetch job
    result = await db.execute(select(Job).filter(Job.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # MULTI-TENANT SECURITY: Can only approve jobs for own college
    if job.college_id != current_officer.college_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot approve jobs for other colleges"
        )
    
    # Update drive status
    if approved:
        job.drive_status = DriveStatus.APPROVED
        job.status = "open"  # Also mark as open
        
        # Trigger eligibility checking for existing applications in background
        from app.eligibility import EligibilityService
        eligibility_service = EligibilityService()
        
        async def check_eligibility_background():
            """Background task to mark ineligible applications."""
            async with AsyncSessionLocal() as bg_db:
                await eligibility_service.mark_ineligible_applications(bg_db, job_id)
        
        # NOTE: For production, use Celery instead of BackgroundTasks
        background_tasks.add_task(check_eligibility_background)
        
    else:
        job.drive_status = DriveStatus.REJECTED
    
    await db.commit()
    await db.refresh(job)
    
    return job


@router.get("/college/{college_id}/applications", response_model=List[dict])
async def get_college_applications(
    college_id: int,
    job_id: Optional[int] = None,
    status: Optional[ApplicationStatus] = None,
    is_eligible: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_officer: PlacementOfficer = Depends(get_current_placement_officer),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all applications for college's jobs.
    
    Requires: PLACEMENT_OFFICER role with VIEW_ALL_APPLICATIONS permission
    Multi-tenant: Can only view applications from own college
    """
    require_permission(Permission.VIEW_ALL_APPLICATIONS)(current_officer.user.role)
    
    # MULTI-TENANT SECURITY
    if college_id != current_officer.college_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access applications from other colleges"
        )
    
    # Build query to get applications for jobs in this college
    query = (
        select(Application)
        .join(Job, Application.job_id == Job.id)
        .filter(Job.college_id == college_id)
    )
    
    # Apply filters
    if job_id:
        query = query.filter(Application.job_id == job_id)
    if status:
        query = query.filter(Application.status == status)
    if is_eligible is not None:
        query = query.filter(Application.is_eligible == is_eligible)
    
    # Pagination
    query = query.offset(skip).limit(limit).order_by(Application.applied_at.desc())
    
    result = await db.execute(query)
    applications = result.scalars().all()
    
    return applications


@router.get("/college/{college_id}/analytics")
async def get_college_analytics(
    college_id: int,
    current_officer: PlacementOfficer = Depends(get_current_placement_officer),
    db: AsyncSession = Depends(get_db)
):
    """
    Get placement analytics for college.
    
    Requires: PLACEMENT_OFFICER role with VIEW_COLLEGE_ANALYTICS permission
    Multi-tenant: Can only view analytics for own college
    
    Returns:
    - Total students
    - Placed students count
    - Active jobs count
    - Applications count
    - Eligibility statistics
    """
    require_permission(Permission.VIEW_COLLEGE_ANALYTICS)(current_officer.user.role)
    
    # MULTI-TENANT SECURITY
    if college_id != current_officer.college_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access analytics for other colleges"
        )
    
    # Total students
    total_students = (await db.execute(
        select(func.count()).select_from(Student).filter(Student.college_id == college_id)
    )).scalar()
    
    # Placed students
    placed_students = (await db.execute(
        select(func.count()).select_from(Student).filter(
            Student.college_id == college_id,
            Student.is_placed == True
        )
    )).scalar()
    
    # Active jobs
    active_jobs = (await db.execute(
        select(func.count()).select_from(Job).filter(
            Job.college_id == college_id,
            Job.drive_status == DriveStatus.APPROVED
        )
    )).scalar()
    
    # Total applications
    total_applications = (await db.execute(
        select(func.count())
        .select_from(Application)
        .join(Job, Application.job_id == Job.id)
        .filter(Job.college_id == college_id)
    )).scalar()
    
    # Eligible vs ineligible
    eligible_applications = (await db.execute(
        select(func.count())
        .select_from(Application)
        .join(Job, Application.job_id == Job.id)
        .filter(
            Job.college_id == college_id,
            Application.is_eligible == True
        )
    )).scalar()
    
    ineligible_applications = (await db.execute(
        select(func.count())
        .select_from(Application)
        .join(Job, Application.job_id == Job.id)
        .filter(
            Job.college_id == college_id,
            Application.is_eligible == False
        )
    )).scalar()
    
    return {
        "college_id": college_id,
        "total_students": total_students,
        "placed_students": placed_students,
        "placement_rate": (placed_students / total_students * 100) if total_students > 0 else 0,
        "active_jobs": active_jobs,
        "total_applications": total_applications,
        "eligible_applications": eligible_applications,
        "ineligible_applications": ineligible_applications,
        "eligibility_rate": (eligible_applications / total_applications * 100) if total_applications > 0 else 0
    }
