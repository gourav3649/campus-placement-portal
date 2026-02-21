from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from app.database import get_db
from app.api.deps import get_current_user, get_current_recruiter
from app.core.rbac import Role, Permission, require_permission
from app.core.config import get_settings
from app.models.job import Job, JobStatus
from app.models.recruiter import Recruiter
from app.schemas.job import JobCreate, JobUpdate, Job as JobSchema, JobList

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post("", response_model=JobSchema, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_data: JobCreate,
    current_recruiter: Recruiter = Depends(get_current_recruiter),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new job posting.
    
    Requires: RECRUITER role with POST_JOBS permission
    SINGLE-COLLEGE MODE: college_id auto-injected from settings, job created as DRAFT
    """
    require_permission(Permission.POST_JOBS)(current_recruiter.user.role)
    
    settings = get_settings()
    
    # SINGLE-COLLEGE MODE: Auto-inject college_id from settings
    college_id = settings.COLLEGE_ID
    
    # Validate college exists
    from app.models.college import College
    college_result = await db.execute(
        select(College).filter(College.id == college_id, College.is_active == True)
    )
    college = college_result.scalar_one_or_none()
    if not college:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="College not found or inactive. Please check COLLEGE_ID in settings."
        )
    
    # Create job with auto-injected college_id
    job_dict = job_data.model_dump()
    job_dict['college_id'] = college_id  # SINGLE-COLLEGE MODE: Auto-injected
    
    job = Job(
        recruiter_id=current_recruiter.id,
        **job_dict
    )
    
    # MULTI-TENANT: Set default drive_status to DRAFT (requires placement officer approval)
    if hasattr(job, 'drive_status'):
        from app.models.job import DriveStatus
        if not job.drive_status:
            job.drive_status = DriveStatus.DRAFT
    
    db.add(job)
    await db.commit()
    await db.refresh(job)
    
    return job


@router.get("", response_model=JobList)
async def list_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    job_type: Optional[str] = None,
    location: Optional[str] = None,
    is_remote: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    List all open job postings with pagination and filters.
    
    MULTI-TENANT: Students only see jobs from their college with APPROVED status.
    Recruiters see all jobs.
    """
    # Build query
    query = select(Job).filter(Job.status == JobStatus.OPEN)
    
    # MULTI-TENANT FILTERING FOR STUDENTS
    if current_user.role == Role.STUDENT:
        from app.models.student import Student
        student_result = await db.execute(
            select(Student).filter(Student.user_id == current_user.id)
        )
        student = student_result.scalar_one_or_none()
        
        if student:
            # Only show jobs from student's college
            query = query.filter(Job.college_id == student.college_id)
            
            # Only show APPROVED drives
            from app.models.job import DriveStatus
            query = query.filter(Job.drive_status == DriveStatus.APPROVED)
    
    # Apply filters
    if job_type:
        query = query.filter(Job.job_type == job_type)
    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))
    if is_remote is not None:
        query = query.filter(Job.is_remote == is_remote)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Get paginated results
    query = query.offset(skip).limit(limit).order_by(Job.created_at.desc())
    result = await db.execute(query)
    jobs = result.scalars().all()
    
    return JobList(
        total=total,
        page=skip // limit + 1,
        page_size=limit,
        jobs=jobs
    )


@router.get("/{job_id}", response_model=JobSchema)
async def get_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get details of a specific job.
    
    Accessible to all authenticated users.
    """
    result = await db.execute(select(Job).filter(Job.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    return job


@router.put("/{job_id}", response_model=JobSchema)
async def update_job(
    job_id: int,
    job_update: JobUpdate,
    current_recruiter: Recruiter = Depends(get_current_recruiter),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a job posting.
    
    Requires: RECRUITER role, must own the job
    """
    result = await db.execute(select(Job).filter(Job.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Check ownership
    if job.recruiter_id != current_recruiter.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this job"
        )
    
    # Check if eligibility rules are being updated
    eligibility_fields = {'min_cgpa', 'allowed_branches', 'max_backlogs', 'exclude_placed_students'}
    update_data = job_update.model_dump(exclude_unset=True)
    eligibility_changed = bool(eligibility_fields & set(update_data.keys()))
    
    # Update fields
    for field, value in update_data.items():
        setattr(job, field, value)
    
    await db.commit()
    await db.refresh(job)
    
    # TRIGGER ELIGIBILITY REVALIDATION if eligibility rules changed
    if eligibility_changed:
        from app.eligibility import EligibilityService
        eligibility_service = EligibilityService()
        
        print(f"[Jobs] Eligibility rules updated for job {job_id}, triggering revalidation...")
        revalidation_stats = await eligibility_service.revalidate_all_applications(db, job_id)
        print(f"[Jobs] Revalidation complete: {revalidation_stats['newly_ineligible']} became ineligible, "
              f"{revalidation_stats['newly_eligible']} became eligible")
    
    return job


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: int,
    current_recruiter: Recruiter = Depends(get_current_recruiter),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a job posting.
    
    Requires: RECRUITER role, must own the job
    """
    result = await db.execute(select(Job).filter(Job.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Check ownership
    if job.recruiter_id != current_recruiter.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this job"
        )
    
    await db.delete(job)
    await db.commit()
    
    return None


@router.post("/{job_id}/close", response_model=JobSchema)
async def close_job(
    job_id: int,
    current_recruiter: Recruiter = Depends(get_current_recruiter),
    db: AsyncSession = Depends(get_db)
):
    """
    Close a job posting (stop accepting applications).
    
    Requires: RECRUITER role, must own the job
    """
    result = await db.execute(select(Job).filter(Job.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Check ownership
    if job.recruiter_id != current_recruiter.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to close this job"
        )
    
    job.status = JobStatus.CLOSED
    await db.commit()
    await db.refresh(job)
    
    return job


@router.post("/{job_id}/revalidate-eligibility")
async def revalidate_job_eligibility(
    job_id: int,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Revalidate eligibility for all applications to this job.
    
    Triggers a complete recheck of all applications, catching:
    - Students who got placed (if job excludes placed students)
    - Students whose CGPA/backlogs changed
    - Applications that became eligible after rule changes
    
    Accessible to:
    - Recruiters (who own the job)
    - Placement Officers (for their college's jobs)
    - Admins
    
    Returns:
        Revalidation statistics showing eligibility changes
    """
    from app.eligibility import EligibilityService
    from app.core.rbac import Role
    
    # Fetch job
    result = await db.execute(select(Job).filter(Job.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Authorization check
    if current_user.role == Role.RECRUITER:
        from app.models.recruiter import Recruiter
        recruiter_result = await db.execute(
            select(Recruiter).filter(Recruiter.user_id == current_user.id)
        )
        recruiter = recruiter_result.scalar_one_or_none()
        
        if not recruiter or job.recruiter_id != recruiter.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to revalidate this job's applications"
            )
    
    elif current_user.role == Role.PLACEMENT_OFFICER:
        from app.models.placement_officer import PlacementOfficer
        officer_result = await db.execute(
            select(PlacementOfficer).filter(PlacementOfficer.user_id == current_user.id)
        )
        officer = officer_result.scalar_one_or_none()
        
        # Multi-tenant check: officer can only revalidate jobs for their college
        if not officer or (hasattr(job, 'college_id') and job.college_id != officer.college_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to revalidate this job's applications"
            )
    
    elif current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to revalidate eligibility"
        )
    
    # Trigger revalidation
    eligibility_service = EligibilityService()
    stats = await eligibility_service.revalidate_all_applications(db, job_id)
    
    return {
        "job_id": job_id,
        "job_title": job.title,
        "revalidation_stats": stats,
        "message": f"Revalidated {stats['total_applications']} applications. "
                   f"{stats['newly_ineligible']} became ineligible, "
                   f"{stats['newly_eligible']} became eligible."
    }
