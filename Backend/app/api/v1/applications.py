from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional, Dict
from app.database import get_db
from app.api.deps import get_current_student, get_current_recruiter, get_current_user
from app.core.rbac import Role
from app.models.application import Application, ApplicationStatus
from app.models.job import Job, JobStatus
from app.models.student import Student
from app.schemas.application import (
    ApplicationCreate, ApplicationUpdate, Application as ApplicationSchema,
    ApplicationWithDetails, ApplicationRanking, RankingRequest, CandidatePreview
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
    PHASE 0: Validates placement lock & eligibility before creating application.
    Only eligible applications trigger AI matching.
    
    Validations (in order):
    1. Student is not already placed
    2. Student has not already applied to this job
    3. Job exists and is accepting applications
    """
    # PHASE 0: PLACEMENT LOCK CHECK
    # If student is already placed, block new applications
    from app.services.application_validation import validate_application_allowed
    
    validation_result = await validate_application_allowed(
        student=current_student,
        job_id=application_data.job_id,
        db=db
    )
    
    if not validation_result['allowed']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=validation_result['reason']
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
    
    # FIX 2 - Specific DB Exception Handling
    from sqlalchemy.exc import IntegrityError
    
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail="You have already applied to this job"
        )
    
    await db.refresh(application)
    
    # Trigger ranking for this job (will score this application and all others)
    from app.services.ranking_service import update_application_scores
    background_tasks.add_task(update_application_scores, application.job_id)
    
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
    
    # Build query - order by similarity score (descending)
    query = select(Application).filter(Application.job_id == job_id)
    
    if status_filter:
        query = query.filter(Application.status == status_filter)
    
    # Order by ai_rank_score descending (highest similarity first), nulls last
    query = query.order_by(Application.ai_rank_score.desc().nullslast())
    
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
    
    # Trigger ranking in background
    from app.services.ranking_service import update_application_scores
    background_tasks.add_task(update_application_scores, job_id)
    
    return {
        "message": "Ranking process started",
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
    
    # Get applications with similarity scores, sorted by score descending
    # Only includes eligible applications (same as ranking service)
    query = (
        select(Application)
        .filter(Application.job_id == job_id)
        .filter(Application.is_eligible == True)
        .filter(Application.ai_rank_score.isnot(None))
        .order_by(Application.ai_rank_score.desc().nullslast())
        .limit(top_n)
    )
    
    result = await db.execute(query)
    applications = result.scalars().all()
    
    # Build response with student details and ranks
    ranked_list = []
    for rank, app in enumerate(applications, start=1):
        student_result = await db.execute(
            select(Student).filter(Student.id == app.student_id)
        )
        student = student_result.scalar_one()
        
        ranked_list.append(
            ApplicationRanking(
                application_id=app.id,
                student_id=student.id,
                student_name=f"{student.first_name} {student.last_name}",
                similarity_score=app.ai_rank_score,
                rank=rank
            )
        )
    
    return ranked_list


@router.get("/{application_id}/ranking", response_model=Optional[Dict])
async def get_application_ranking(
    application_id: int,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get student's ranking on a specific job application.
    
    Returns rank based on stored ai_rank_score (same source as recruiter views).
    Rank is derived by comparing position in sorted eligible applicants.
    """
    from app.models.student import Student
    
    # Fetch application
    app_result = await db.execute(
        select(Application).filter(Application.id == application_id)
    )
    application = app_result.scalar_one_or_none()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    # Auth: Student can see only their own ranking
    if current_user.role == Role.STUDENT:
        student_result = await db.execute(
            select(Student).filter(Student.user_id == current_user.id)
        )
        student = student_result.scalar_one_or_none()
        if not student or application.student_id != student.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot view other student's ranking"
            )
    
    # If no score yet, return null
    if application.ai_rank_score is None:
        return None
    
    # Get ALL eligible applications for this job, ordered by score (same as recruiter view)
    # This ensures consistent rank calculation across all endpoints
    all_apps_result = await db.execute(
        select(Application.id, Application.ai_rank_score)
        .filter(Application.job_id == application.job_id)
        .filter(Application.is_eligible == True)
        .filter(Application.ai_rank_score.isnot(None))
        .order_by(Application.ai_rank_score.desc().nullslast())
    )
    ranked_apps = all_apps_result.all()
    
    # Find rank of current application (position in sorted list)
    rank = None
    total_applicants = len(ranked_apps)
    for position, (app_id, _) in enumerate(ranked_apps, start=1):
        if app_id == application.id:
            rank = position
            break
    
    if rank is None:
        # Application is eligible but not in ranked list (shouldn't happen)
        return None
    
    return {
        "application_id": application.id,
        "similarity_score": round(application.ai_rank_score, 4),
        "rank": rank,
        "total_applicants": total_applicants,
        "status": application.status
    }


@router.get("/job/{job_id}/top_candidates", response_model=List[CandidatePreview])
async def get_top_candidates(
    job_id: int,
    top_n: int = Query(10, ge=1, le=100),
    current_recruiter = Depends(get_current_recruiter),
    db: AsyncSession = Depends(get_db)
):
    """
    Get top ranked candidates for a job (dashboard view).
    
    Shows highest similarity scores first.
    Requires: RECRUITER role, must own the job
    """
    from app.models.student import Student
    from app.models.recruiter import Recruiter
    
    # Check if recruiter owns the job
    job_result = await db.execute(select(Job).filter(Job.id == job_id))
    job = job_result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    recruiter_result = await db.execute(
        select(Recruiter).filter(Recruiter.user_id == current_recruiter.id)
    )
    recruiter = recruiter_result.scalar_one_or_none()
    
    if not recruiter or job.recruiter_id != recruiter.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view candidates for this job"
        )
    
    # Get top ranked applications (batch query efficient)
    # Only includes eligible applications (same as ranking service)
    query = (
        select(Application, Student)
        .join(Student, Application.student_id == Student.id)
        .filter(Application.job_id == job_id)
        .filter(Application.is_eligible == True)
        .filter(Application.ai_rank_score.isnot(None))
        .order_by(Application.ai_rank_score.desc().nullslast())
        .limit(top_n)
    )
    
    result = await db.execute(query)
    app_student_pairs = result.all()
    
    # Build response with rank calculation
    candidates = []
    for rank, (app, student) in enumerate(app_student_pairs, start=1):
        candidates.append(
            CandidatePreview(
                application_id=app.id,
                student_id=student.id,
                student_name=f"{student.first_name} {student.last_name}",
                email=student.user.email if student.user else None,
                similarity_score=round(app.ai_rank_score, 4),
                rank=rank,
                status=app.status,
                applied_at=app.applied_at
            )
        )
    
    return candidates
