from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Any, Optional
import logging
import asyncio
import json

from app.database import get_db
from app.models.job import Job, DriveStatus
from app.models.application import Application, ApplicationStatus
from app.models.round import Round
from app.models.recruiter import Recruiter
from app.schemas.job import JobCreate, JobUpdate, JobResponse, JobWithStats
from app.schemas.job_round import JobRoundCreate, JobRoundResponse
from app.api.deps import get_current_recruiter, get_current_placement_officer, get_current_student
from app.services.notification_service import create_notification
from app.services.embedding_service import generate_embedding, prepare_job_text_for_embedding
from app.models.notification import NotificationType

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Recruiter endpoints ────────────────────────────────────────────────────────

@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_in: JobCreate,
    db: AsyncSession = Depends(get_db),
    recruiter: Recruiter = Depends(get_current_recruiter),
    background_tasks: BackgroundTasks = BackgroundTasks(),
) -> Any:
    """Recruiter posts a new drive. Starts as DRAFT."""
    if not recruiter.is_verified:
        raise HTTPException(status_code=403, detail="Your recruiter account is not yet verified by the placement office.")

    job_data = job_in.model_dump()
    
    db_job = Job(
        **job_data,
        recruiter_id=recruiter.id,
        drive_status=DriveStatus.DRAFT,  # Use drive_status, not status
    )
    
    db.add(db_job)
    await db.commit()
    await db.refresh(db_job)
    
    # Queue embedding generation as background task (non-blocking)
    background_tasks.add_task(generate_job_embedding, db_job.id)
    
    logger.info(f"Job created successfully (job_id: {db_job.id}, recruiter: {recruiter.id})")
    return db_job


@router.get("/my-jobs", response_model=List[JobWithStats])
async def list_my_jobs(
    db: AsyncSession = Depends(get_db),
    recruiter: Recruiter = Depends(get_current_recruiter),
) -> Any:
    result = await db.execute(select(Job).filter(Job.recruiter_id == recruiter.id))
    jobs = result.scalars().all()
    
    jobs_with_stats = []
    for job in jobs:
        total = await db.scalar(select(func.count(Application.id)).filter(Application.job_id == job.id))
        
        eligible = await db.scalar(select(func.count(Application.id)).filter(
            Application.job_id == job.id, Application.is_eligible == True
        ))
        
        selected = await db.scalar(select(func.count(Application.id)).filter(
            Application.job_id == job.id, Application.status == ApplicationStatus.ACCEPTED
        ))
        
        jws = JobWithStats.model_validate(job)
        jws.total_applied = total or 0
        jws.eligible_count = eligible or 0
        jws.selected_count = selected or 0
        jobs_with_stats.append(jws)

    return jobs_with_stats


@router.put("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: int,
    job_in: JobUpdate,
    db: AsyncSession = Depends(get_db),
    recruiter: Recruiter = Depends(get_current_recruiter),
) -> Any:
    result = await db.execute(select(Job).filter(Job.id == job_id, Job.recruiter_id == recruiter.id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.drive_status != DriveStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Only DRAFT jobs can be edited")

    # Track which fields are being updated (for embedding recomputation)
    embedding_relevant_fields = {'title', 'description', 'required_skills', 'requirements', 'responsibilities'}
    fields_to_update = job_in.model_dump(exclude_unset=True)
    needs_embedding_update = any(field in embedding_relevant_fields for field in fields_to_update.keys())
    
    # Apply updates
    for field, value in fields_to_update.items():
        setattr(job, field, value)
    
    # Recompute embedding if relevant fields changed (NON-BLOCKING)
    if needs_embedding_update:
        try:
            job_text = prepare_job_text_for_embedding(job)
            # Use asyncio.to_thread to avoid blocking the event loop
            embedding_vector = await asyncio.to_thread(generate_embedding, job_text)
            job.embedding_vector = embedding_vector
            logger.info(f"Job embedding recomputed after update (job_id: {job_id}, recruiter: {recruiter.id})")
        except ValueError as ve:
            logger.warning(f"Job embedding recomputation failed (validation): {str(ve)} (job_id: {job_id}) - Continuing without embedding")
        except Exception as e:
            logger.warning(f"Job embedding recomputation failed (unexpected): {str(e)} (job_id: {job_id}) - Continuing without embedding")
    
    await db.commit()
    await db.refresh(job)
    
    logger.info(f"Job updated successfully (job_id: {job_id}, recruiter: {recruiter.id}, embedding_updated: {needs_embedding_update})")
    return job


@router.post("/{job_id}/rounds", response_model=JobRoundResponse, status_code=status.HTTP_201_CREATED)
async def create_round(
    job_id: int,
    round_in: JobRoundCreate,
    db: AsyncSession = Depends(get_db),
    recruiter: Recruiter = Depends(get_current_recruiter),
) -> Any:
    """Create a round template for a job. Recruiter must own the job."""
    # Step 1: Fetch job and verify ownership
    result = await db.execute(select(Job).where(Job.id == job_id, Job.recruiter_id == recruiter.id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Step 1b: Job must still be in DRAFT
    if job.drive_status != DriveStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Cannot modify rounds after job is approved")

    # Step 2: Block if applications already exist
    result = await db.execute(
        select(Application.id).where(Application.job_id == job_id).limit(1)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Cannot modify rounds after applications start")

    # Step 3: Compute sequential round number (server-controlled)
    existing_rounds_result = await db.execute(
        select(Round).where(Round.job_id == job_id).order_by(Round.round_number)
    )
    existing_rounds = existing_rounds_result.scalars().all()
    round_number = len(existing_rounds) + 1

    # Step 4 & 5: Create, save, refresh
    db_round = Round(
        job_id=job_id,
        round_number=round_number,
        name=round_in.name,
        is_eliminatory=round_in.is_eliminatory,
        max_score=round_in.max_score,
    )
    db.add(db_round)
    await db.commit()
    await db.refresh(db_round)

    # Step 6: Return
    return db_round


# ── Placement Officer endpoints ────────────────────────────────────────────────

@router.get("/pending-approval", response_model=List[JobWithStats])
async def list_pending_jobs(
    db: AsyncSession = Depends(get_db),
    officer: Any = Depends(get_current_placement_officer),
) -> Any:
    result = await db.execute(
        select(Job).filter(Job.college_id == officer.college_id, Job.drive_status == DriveStatus.DRAFT)
    )
    return result.scalars().all()


@router.get("/all", response_model=List[JobWithStats])
async def list_all_college_jobs(
    db: AsyncSession = Depends(get_db),
    officer: Any = Depends(get_current_placement_officer),
) -> Any:
    """All jobs for this college (any status). Officer view with stats."""
    result = await db.execute(select(Job).filter(Job.college_id == officer.college_id))
    jobs = result.scalars().all()

    jobs_with_stats = []
    for job in jobs:
        total = await db.scalar(select(func.count(Application.id)).filter(Application.job_id == job.id))
        eligible = await db.scalar(select(func.count(Application.id)).filter(
            Application.job_id == job.id, Application.is_eligible == True
        ))
        selected = await db.scalar(select(func.count(Application.id)).filter(
            Application.job_id == job.id, Application.status == ApplicationStatus.ACCEPTED
        ))
        jws = JobWithStats.model_validate(job)
        jws.total_applied = total or 0
        jws.eligible_count = eligible or 0
        jws.selected_count = selected or 0
        jobs_with_stats.append(jws)

    return jobs_with_stats


@router.put("/{job_id}/approve", response_model=JobResponse)
async def approve_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    officer: Any = Depends(get_current_placement_officer),
) -> Any:
    result = await db.execute(select(Job).filter(Job.id == job_id, Job.college_id == officer.college_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.drive_status != DriveStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Only DRAFT jobs can be approved")

    # Check recruiter is verified
    recruiter_result = await db.execute(select(Recruiter).filter(Recruiter.id == job.recruiter_id))
    recruiter = recruiter_result.scalar_one_or_none()
    if not recruiter or not recruiter.is_verified:
        raise HTTPException(status_code=403, detail="Recruiter is not verified. Verify the recruiter before approving drives.")

    # Ensure embedding is generated (in case it failed during creation or update)
    # Embedding is NON-BLOCKING: System continues even if embedding fails
    if not job.embedding_vector:
        try:
            job_text = prepare_job_text_for_embedding(job)
            # Use asyncio.to_thread to avoid blocking the event loop on expensive computation
            # TEMPORARILY DISABLED FOR DEBUGGING - asyncio.to_thread causing timeouts
            # embedding_vector = await asyncio.to_thread(generate_embedding, job_text)
            # job.embedding_vector = embedding_vector
            logger.info(f"Job embedding generation skipped (disabled for debugging)")
        except ValueError as ve:
            logger.warning(f"Job embedding generation failed during approval (validation): {str(ve)} (job_id: {job_id}) - Continuing without embedding")
        except Exception as e:
            logger.warning(f"Job embedding generation failed during approval (unexpected): {str(e)} (job_id: {job_id}) - Continuing without embedding")
    else:
        logger.debug(f"Job embedding already present, skipping generation (job_id: {job_id})")

    job.drive_status = DriveStatus.APPROVED
    await db.flush()
    await db.commit()

    # PHASE 4: Notify all students in this college (after commit)
    try:
        from app.models.student import Student
        from app.models.user import User
        students_result = await db.execute(
            select(Student).filter(Student.college_id == officer.college_id)
        )
        students = students_result.scalars().all()
        for student in students:
            await create_notification(
                db=db,
                user_id=student.user_id,
                title=f"New Drive: {job.title}",
                message=f"{recruiter.company_name} is hiring! Apply before {job.deadline.strftime('%d %b %Y') if job.deadline else 'the deadline'}.",
                notification_type=NotificationType.DRIVE_OPENED,
                related_job_id=job.id,
            )
        
        await db.commit()
        logger.info(f"Notifications sent for approved job (job_id: {job_id})")
    except Exception as e:
        logger.warning(f"Failed to send notifications for approved job (job_id: {job_id}): {str(e)} - Continuing")
    
    await db.refresh(job)
    
    logger.info(f"Job approved successfully (job_id: {job_id}, officer: {officer.id})")
    return job


@router.put("/{job_id}/reject", response_model=JobResponse)
async def reject_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    officer: Any = Depends(get_current_placement_officer),
) -> Any:
    result = await db.execute(select(Job).filter(Job.id == job_id, Job.college_id == officer.college_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.drive_status = DriveStatus.REJECTED
    await db.commit()
    await db.refresh(job)
    return job


@router.put("/{job_id}/close", response_model=JobResponse)
async def close_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    officer: Any = Depends(get_current_placement_officer),
) -> Any:
    result = await db.execute(select(Job).filter(Job.id == job_id, Job.college_id == officer.college_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.drive_status = DriveStatus.CLOSED
    await db.commit()
    await db.refresh(job)
    return job


# ── Student / Public endpoints ─────────────────────────────────────────────────

@router.get("/", response_model=List[JobResponse])
async def list_approved_jobs(
    db: AsyncSession = Depends(get_db),
    student: Any = Depends(get_current_student),
) -> Any:
    """Students see only APPROVED jobs from their college."""
    result = await db.execute(
        select(Job).filter(Job.college_id == student.college_id, Job.drive_status == DriveStatus.APPROVED)
    )
    return result.scalars().all()


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    student: Any = Depends(get_current_student),
) -> Any:
    result = await db.execute(
        select(Job).filter(Job.id == job_id, Job.college_id == student.college_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


# ── Background Tasks ───────────────────────────────────────────────────────────

async def generate_job_embedding(job_id: int):
    """Background task to generate embedding for a job."""
    from app.database import AsyncSessionLocal
    from sqlalchemy import select
    from app.models.job import Job
    from app.services.embedding_service import generate_embedding, prepare_job_text_for_embedding
    import logging
    import asyncio
    
    logger = logging.getLogger(__name__)
    
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(Job).where(Job.id == job_id))
            job = result.scalar_one_or_none()

            if not job:
                logger.error(f"Job not found for embedding: {job_id}")
                return

            job_text = prepare_job_text_for_embedding(job)

            embedding = await asyncio.to_thread(generate_embedding, job_text)

            # Ensure embedding is valid before saving
            if embedding and isinstance(embedding, list):
                job.embedding_vector = embedding
                await db.commit()
                logger.info(f"Embedding generated for job {job_id}")
            else:
                logger.error(f"Invalid embedding for job {job_id}")

        except Exception as e:
            logger.error(f"Embedding generation failed for job {job_id}: {str(e)}")
