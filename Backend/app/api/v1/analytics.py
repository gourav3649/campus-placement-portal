"""PHASE 5: Analytics endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, Float
from typing import List

from app.database import get_db
from app.models.application import Application, ApplicationStatus
from app.models.application_round import ApplicationRound, RoundResult
from app.models.student import Student
from app.models.user import User
from app.models.job import Job
from app.schemas.analytics import CandidateInsight, TopCandidate, DriveSummary
from app.api.deps import get_current_student, get_current_recruiter, get_current_placement_officer
from app.services.analytics_service import get_candidate_aggregations, get_drive_summary

router = APIRouter(tags=["Analytics"])


@router.get("/jobs/{job_id}/top-candidates", response_model=List[TopCandidate])
async def get_top_candidates(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    recruiter: Student = Depends(get_current_recruiter),
) -> List[TopCandidate]:
    """PHASE 5: Get top 10 candidates for a job, sorted by avg_score and rounds_cleared."""
    # Verify recruiter owns this job
    job_result = await db.execute(select(Job).filter(Job.id == job_id, Job.recruiter_id == recruiter.id))
    if not job_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Job not found")
    
    # FIX 1 & 2: Cast avg_score to Float and ensure only non-null scores are used
    subq = (
        select(
            Application.id.label('app_id'),
            Application.student_id,
            Application.status,
            func.avg(
                case(
                    (ApplicationRound.score.isnot(None), ApplicationRound.score),
                    else_=None
                )
            ).cast(Float).label('avg_score'),
            func.sum(
                case(
                    (ApplicationRound.result == RoundResult.PASSED, 1),
                    else_=0
                )
            ).label('rounds_cleared'),
        )
        .outerjoin(ApplicationRound, Application.id == ApplicationRound.application_id)
        .filter(Application.job_id == job_id)
        .group_by(Application.id, Application.student_id, Application.status)
        .subquery()
    )
    
    # FIX 2: Proper join to User table via Student
    result = await db.execute(
        select(
            subq.c.student_id,
            User.full_name,
            subq.c.avg_score,
            subq.c.rounds_cleared,
            subq.c.status,
        )
        .select_from(subq)
        .join(Student, subq.c.student_id == Student.id)
        .join(User, Student.user_id == User.id)
        # FIX 4: Sort with nullslast() for avg_score
        .order_by(subq.c.avg_score.desc().nullslast(), subq.c.rounds_cleared.desc())
        .limit(10)
    )
    
    candidates = []
    for row in result:
        candidates.append(
            TopCandidate(
                student_id=row[0],
                student_name=row[1],
                avg_score=row[2],
                rounds_cleared=row[3],
                latest_status=row[4],
            )
        )
    return candidates


@router.get("/applications/{app_id}/insight", response_model=CandidateInsight)
async def get_application_insight(
    app_id: int,
    db: AsyncSession = Depends(get_db),
    student: Student = Depends(get_current_student),
) -> CandidateInsight:
    """PHASE 5: Get self-insight for student's application."""
    # Verify student owns this application
    app_result = await db.execute(
        select(Application).filter(Application.id == app_id, Application.student_id == student.id)
    )
    application = app_result.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Get aggregations
    aggregations = await get_candidate_aggregations(db, [app_id])
    agg = aggregations.get(app_id)
    
    # Compute label
    if agg.avg_score is None:
        label = "Needs Improvement"
    elif agg.avg_score >= 80:
        label = "Strong Candidate"
    elif agg.avg_score >= 60:
        label = "Good Candidate"
    else:
        label = "Needs Improvement"
    
    return CandidateInsight(
        avg_score=agg.avg_score,
        rounds_cleared=agg.rounds_cleared,
        current_status=application.status,
        performance_label=label,
    )


@router.get("/jobs/{job_id}/summary", response_model=DriveSummary)
async def get_job_summary(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    officer: Student = Depends(get_current_placement_officer),
) -> DriveSummary:
    """PHASE 5: Get summary for a job, accessible to placement officer."""
    # Verify job exists in officer's college
    job_result = await db.execute(select(Job).filter(Job.id == job_id, Job.college_id == officer.college_id))
    if not job_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Job not found")
    
    summary = await get_drive_summary(db, job_id)
    return DriveSummary(**summary)
