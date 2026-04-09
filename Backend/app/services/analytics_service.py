"""PHASE 5: Analytics service for computing aggregations from existing data."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, Float
from app.models.application import Application, ApplicationStatus
from app.models.application_round import ApplicationRound, RoundResult
from app.models.student import Student
from app.models.job import Job


class CandidateAggregation:
    """Container for candidate score aggregations."""
    def __init__(self, application_id: int, avg_score: float | None, rounds_cleared: int):
        self.application_id = application_id
        self.avg_score = avg_score
        self.rounds_cleared = rounds_cleared


async def get_candidate_aggregations(
    db: AsyncSession,
    application_ids: list[int],
) -> dict[int, CandidateAggregation]:
    """
    PHASE 5: Compute avg_score and rounds_cleared for each application.
    
    Returns dict mapping application_id -> CandidateAggregation
    """
    if not application_ids:
        return {}
    
    # FIX 1 & 2: Cast avg_score to Float and ensure only non-null scores are used
    result = await db.execute(
        select(
            ApplicationRound.application_id,
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
        .filter(ApplicationRound.application_id.in_(application_ids))
        .group_by(ApplicationRound.application_id)
    )
    
    aggregations = {}
    for row in result:
        aggregations[row[0]] = CandidateAggregation(
            application_id=row[0],
            avg_score=row[1],
            rounds_cleared=row[2] or 0,
        )
    
    # Fill in missing applications with 0 scores
    for app_id in application_ids:
        if app_id not in aggregations:
            aggregations[app_id] = CandidateAggregation(
                application_id=app_id,
                avg_score=None,
                rounds_cleared=0,
            )
    
    return aggregations


async def get_drive_summary(
    db: AsyncSession,
    job_id: int,
) -> dict:
    """PHASE 5: Get summary stats for a job/drive."""
    # FIX 1: Use proper case() syntax
    result = await db.execute(
        select(
            func.count(Application.id).label('total_applicants'),
            func.sum(
                case(
                    (Application.status == ApplicationStatus.IN_PROGRESS, 1),
                    else_=0
                )
            ).label('in_progress_count'),
            func.sum(
                case(
                    (Application.status == ApplicationStatus.ACCEPTED, 1),
                    else_=0
                )
            ).label('accepted_count'),
            func.sum(
                case(
                    (Application.status == ApplicationStatus.REJECTED, 1),
                    else_=0
                )
            ).label('rejected_count'),
        )
        .filter(Application.job_id == job_id)
    )
    
    # FIX 3: Use one() instead of scalar_one()
    row = result.one()
    return {
        'total_applicants': row[0] or 0,
        'in_progress_count': row[1] or 0,
        'accepted_count': row[2] or 0,
        'rejected_count': row[3] or 0,
    }
