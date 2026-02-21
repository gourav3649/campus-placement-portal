from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from app.database import get_db
from app.api.deps import get_current_student, get_current_recruiter, get_current_user
from app.core.rbac import Permission, require_permission
from app.models.application import Application, ApplicationStatus
from app.models.job import Job, JobStatus
from app.models.student import Student
from app.schemas.application import (
    ApplicationCreate, ApplicationUpdate, Application as ApplicationSchema,
    ApplicationWithDetails, ApplicationRanking, RankingRequest
)

router = APIRouter(prefix="/applications", tags=["Applications"])


@router.post("", response_model=ApplicationSchema, status_code=status.HTTP_201_CREATED)
async def submit_application(
    application_data: ApplicationCreate,
    background_tasks: BackgroundTasks,
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit a job application.
    
    Requires: STUDENT role
    NOW: Checks eligibility BEFORE creating application.
    Only eligible applications trigger AI matching.
    """
    # Check if job exists and is open
    job_result = await db.execute(select(Job).filter(Job.id == application_data.job_id))
    job = job_result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    if job.status != JobStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This job is no longer accepting applications"
        )
    
    # MULTI-TENANT: Check drive status (must be APPROVED)
    from app.models.job import DriveStatus
    if hasattr(job, 'drive_status') and job.drive_status != DriveStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This job drive has not been approved yet"
        )
    
    # Check if already applied
    existing_result = await db.execute(
        select(Application).filter(
            Application.student_id == current_student.id,
            Application.job_id == application_data.job_id
        )
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already applied to this job"
        )
    
    # Create application (initially PENDING)
    application = Application(
        student_id=current_student.id,
        job_id=application_data.job_id,
        resume_id=application_data.resume_id,
        cover_letter=application_data.cover_letter,
        status=ApplicationStatus.PENDING
    )
    
    db.add(application)
    await db.commit()
    await db.refresh(application)
    
    # ELIGIBILITY CHECK BEFORE AI RANKING
    from app.eligibility import EligibilityService
    eligibility_service = EligibilityService()
    
    is_eligible, failure_reasons = await eligibility_service.check_application_eligibility(
        db=db,
        application=application,
        update_db=True  # Marks application as ELIGIBILITY_FAILED if ineligible
    )
    
    if not is_eligible:
        # Application marked as ELIGIBILITY_FAILED, DO NOT trigger AI
        await db.refresh(application)
        return application
    
    # Only eligible applications trigger AI matching
    from app.services.semantic_ranking import process_application_matching
    background_tasks.add_task(process_application_matching, application.id)
    
    return application


@router.get("/{application_id}", response_model=ApplicationSchema)
async def get_application(
    application_id: int,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get details of a specific application.
    
    Students can view their own applications.
    Recruiters can view applications for their jobs.
    """
    result = await db.execute(
        select(Application).filter(Application.id == application_id)
    )
    application = result.scalar_one_or_none()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    # Authorization check
    from app.core.rbac import Role
    if current_user.role == Role.STUDENT:
        # Students can only view their own applications
        student_result = await db.execute(
            select(Student).filter(Student.user_id == current_user.id)
        )
        student = student_result.scalar_one_or_none()
        if not student or application.student_id != student.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this application"
            )
    elif current_user.role == Role.RECRUITER:
        # Recruiters can view applications for their jobs
        from app.models.recruiter import Recruiter
        recruiter_result = await db.execute(
            select(Recruiter).filter(Recruiter.user_id == current_user.id)
        )
        recruiter = recruiter_result.scalar_one_or_none()
        
        job_result = await db.execute(select(Job).filter(Job.id == application.job_id))
        job = job_result.scalar_one_or_none()
        
        if not recruiter or not job or job.recruiter_id != recruiter.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this application"
            )
    
    return application


@router.put("/{application_id}/status", response_model=ApplicationSchema)
async def update_application_status(
    application_id: int,
    new_status: ApplicationStatus,
    current_recruiter = Depends(get_current_recruiter),
    db: AsyncSession = Depends(get_db)
):
    """
    Update application status.
    
    Requires: RECRUITER role, must own the job
    """
    result = await db.execute(
        select(Application).filter(Application.id == application_id)
    )
    application = result.scalar_one_or_none()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    # Check if recruiter owns the job
    job_result = await db.execute(select(Job).filter(Job.id == application.job_id))
    job = job_result.scalar_one_or_none()
    
    if not job or job.recruiter_id != current_recruiter.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this application"
        )
    
    application.status = new_status
    await db.commit()
    await db.refresh(application)
    
    return application


@router.get("/job/{job_id}/list", response_model=List[ApplicationSchema])
async def list_job_applications(
    job_id: int,
    status_filter: ApplicationStatus = Query(None),
    current_recruiter = Depends(get_current_recruiter),
    db: AsyncSession = Depends(get_db)
):
    """
    List all applications for a specific job.
    
    Requires: RECRUITER role, must own the job
    """
    # Check if recruiter owns the job
    job_result = await db.execute(select(Job).filter(Job.id == job_id))
    job = job_result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    if job.recruiter_id != current_recruiter.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view applications for this job"
        )
    
    # Build query
    query = select(Application).filter(Application.job_id == job_id)
    
    if status_filter:
        query = query.filter(Application.status == status_filter)
    
    query = query.order_by(Application.rank.asc().nullslast(), Application.match_score.desc().nullslast())
    
    result = await db.execute(query)
    applications = result.scalars().all()
    
    return applications


@router.post("/job/{job_id}/rank", status_code=status.HTTP_202_ACCEPTED)
async def trigger_ai_ranking(
    job_id: int,
    background_tasks: BackgroundTasks,
    rerank: bool = Query(False, description="Force re-ranking of all applications"),
    current_recruiter = Depends(get_current_recruiter),
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger AI-powered ranking of all applications for a job.
    
    Requires: RECRUITER role, must own the job
    This is a background task that may take some time.
    """
    # Check if recruiter owns the job
    job_result = await db.execute(select(Job).filter(Job.id == job_id))
    job = job_result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    if job.recruiter_id != current_recruiter.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to rank applications for this job"
        )
    
    # Trigger AI ranking in background
    from app.services.semantic_ranking import rank_job_applications
    background_tasks.add_task(rank_job_applications, job_id, rerank)
    
    return {
        "message": "AI ranking process started",
        "job_id": job_id,
        "status": "processing"
    }


@router.get("/job/{job_id}/ranked", response_model=List[ApplicationRanking])
async def get_ranked_applications(
    job_id: int,
    top_n: int = Query(10, ge=1, le=100),
    current_recruiter = Depends(get_current_recruiter),
    db: AsyncSession = Depends(get_db)
):
    """
    Get AI-ranked applications for a job.
    
    Requires: RECRUITER role, must own the job
    Returns top N candidates with AI analysis.
    """
    # Check if recruiter owns the job
    job_result = await db.execute(select(Job).filter(Job.id == job_id))
    job = job_result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    if job.recruiter_id != current_recruiter.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view rankings for this job"
        )
    
    # Get ranked applications
    query = (
        select(Application)
        .filter(Application.job_id == job_id)
        .filter(Application.match_score.isnot(None))
        .order_by(Application.rank.asc())
        .limit(top_n)
    )
    
    result = await db.execute(query)
    applications = result.scalars().all()
    
    # Build response with student details
    ranked_list = []
    for app in applications:
        student_result = await db.execute(
            select(Student).filter(Student.id == app.student_id)
        )
        student = student_result.scalar_one()
        
        # Parse JSON fields
        import json
        strengths = json.loads(app.strengths) if app.strengths else []
        weaknesses = json.loads(app.weaknesses) if app.weaknesses else []
        
        ranked_list.append(
            ApplicationRanking(
                application_id=app.id,
                student_id=student.id,
                student_name=f"{student.first_name} {student.last_name}",
                match_score=app.match_score,
                skills_match_score=app.skills_match_score,
                experience_match_score=app.experience_match_score,
                rank=app.rank,
                ai_summary=app.ai_summary or "",
                strengths=strengths,
                weaknesses=weaknesses,
                resume_url=None  # TODO: Add resume URL generation
            )
        )
    
    return ranked_list
