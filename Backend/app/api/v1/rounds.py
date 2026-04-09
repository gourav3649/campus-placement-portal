from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Any

from app.database import get_db
from app.models.application_round import ApplicationRound, RoundResult
from app.models.application import Application, ApplicationStatus
from app.models.student import Student
from app.models.notification import NotificationType
from app.schemas.round import RoundCreate, RoundUpdate, RoundResponse
from app.api.deps import get_current_placement_officer, get_current_student
from app.services.notification_service import create_notification
from app.services.workflow_validation import (
    can_add_round,
    validate_round_progression,
    can_modify_round,
    get_last_round,
)

router = APIRouter()


@router.post("/applications/{app_id}/rounds", response_model=RoundResponse, status_code=status.HTTP_201_CREATED)
async def add_round(
    app_id: int,
    round_in: RoundCreate,
    db: AsyncSession = Depends(get_db),
    officer: Any = Depends(get_current_placement_officer),
) -> Any:
    """PHASE 2: Add round with workflow validation."""
    app_result = await db.execute(select(Application).filter(Application.id == app_id))
    application = app_result.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    # PHASE 2: Check if application allows new rounds
    can_add, reason = await can_add_round(application, db)
    if not can_add:
        raise HTTPException(status_code=400, detail=reason)
    
    # PHASE 2: Validate round number progression
    valid_progression, reason = await validate_round_progression(app_id, round_in.round_number, db)
    if not valid_progression:
        raise HTTPException(status_code=400, detail=reason)

    db_round = ApplicationRound(
        application_id=app_id,
        updated_by_id=officer.user_id,
        **round_in.model_dump(),
    )
    # FIX 1: Set evaluated_by_id if ANY evaluation field provided
    if round_in.score is not None or round_in.recommendation is not None or round_in.feedback is not None:
        db_round.evaluated_by_id = officer.user_id
    db.add(db_round)
    await db.flush()

    # Update application status to IN_PROGRESS if APPLIED
    if application.status == ApplicationStatus.APPLIED:
        application.status = ApplicationStatus.IN_PROGRESS
    
    # FIX 1: Sync application status with round result
    if round_in.result == RoundResult.FAILED:
        application.status = ApplicationStatus.REJECTED
    # If PASSED, keep IN_PROGRESS (do NOT auto accept)

    # Notify student if result is not PENDING
    if round_in.result in (RoundResult.PASSED, RoundResult.FAILED):
        student_result = await db.execute(select(Student).filter(Student.id == application.student_id))
        student = student_result.scalar_one_or_none()
        if student:
            notif_type = NotificationType.SHORTLISTED if round_in.result == RoundResult.PASSED else NotificationType.ROUND_RESULT
            await create_notification(
                db,
                user_id=student.user_id,
                title=f"Round Update: {round_in.round_name}",
                message=f"Your result for '{round_in.round_name}': {round_in.result.value}",
                notification_type=notif_type,
                related_application_id=app_id,
            )

    await db.commit()
    await db.refresh(db_round)
    return db_round


@router.get("/applications/{app_id}/rounds", response_model=List[RoundResponse])
async def get_rounds_for_application(
    app_id: int,
    db: AsyncSession = Depends(get_db),
    student: Student = Depends(get_current_student),
) -> Any:
    # Student can only see their own rounds
    app_result = await db.execute(select(Application).filter(Application.id == app_id, Application.student_id == student.id))
    if not app_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Application not found")

    result = await db.execute(
        select(ApplicationRound).filter(ApplicationRound.application_id == app_id)
        .order_by(ApplicationRound.round_number.asc())
    )
    return result.scalars().all()


@router.put("/rounds/{round_id}", response_model=RoundResponse)
async def update_round(
    round_id: int,
    round_in: RoundUpdate,
    db: AsyncSession = Depends(get_db),
    officer: Any = Depends(get_current_placement_officer),
) -> Any:
    """PHASE 2: Update round with immutability check."""
    result = await db.execute(select(ApplicationRound).filter(ApplicationRound.id == round_id))
    db_round = result.scalar_one_or_none()
    if not db_round:
        raise HTTPException(status_code=404, detail="Round not found")

    # PHASE 2: Prevent modification of past rounds
    can_modify, reason = await can_modify_round(round_id, db)
    if not can_modify:
        raise HTTPException(status_code=400, detail=reason)

    old_result = db_round.result
    for field, value in round_in.model_dump(exclude_unset=True).items():
        setattr(db_round, field, value)
    db_round.updated_by_id = officer.user_id
    # FIX 1: Set evaluated_by_id if ANY evaluation field being updated
    dump_data = round_in.model_dump(exclude_unset=True)
    if 'score' in dump_data or 'recommendation' in dump_data or 'feedback' in dump_data:
        db_round.evaluated_by_id = officer.user_id
    await db.flush()
    
    # Always recompute application status based on latest round
    app_result = await db.execute(select(Application).filter(Application.id == db_round.application_id))
    application = app_result.scalar_one_or_none()
    if application:
        last_round = await get_last_round(db_round.application_id, db)
        
        if not last_round:
            # No rounds left → reset to APPLIED
            application.status = ApplicationStatus.APPLIED
        elif last_round.result == RoundResult.FAILED:
            # Last round failed → REJECTED
            application.status = ApplicationStatus.REJECTED
        else:
            # Other results → IN_PROGRESS
            application.status = ApplicationStatus.IN_PROGRESS

    # Notify if result changed to PASSED or FAILED
    if round_in.result and round_in.result != old_result and round_in.result in (RoundResult.PASSED, RoundResult.FAILED):
        app_result = await db.execute(select(Application).filter(Application.id == db_round.application_id))
        application = app_result.scalar_one_or_none()
        if application:
            student_result = await db.execute(select(Student).filter(Student.id == application.student_id))
            student = student_result.scalar_one_or_none()
            if student:
                notif_type = NotificationType.SHORTLISTED if round_in.result == RoundResult.PASSED else NotificationType.ROUND_RESULT
                await create_notification(
                    db,
                    user_id=student.user_id,
                    title=f"Round Update: {db_round.round_name}",
                    message=f"Your result for '{db_round.round_name}': {round_in.result.value}",
                    notification_type=notif_type,
                    related_application_id=db_round.application_id,
                )

    await db.commit()
    await db.refresh(db_round)
    return db_round

@router.delete("/rounds/{round_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_round(
    round_id: int,
    db: AsyncSession = Depends(get_db),
    officer: Any = Depends(get_current_placement_officer),
) -> None:
    """FIX 2: Allow deletion ONLY for the latest round."""
    result = await db.execute(select(ApplicationRound).filter(ApplicationRound.id == round_id))
    db_round = result.scalar_one_or_none()
    if not db_round:
        raise HTTPException(status_code=404, detail="Round not found")

    # FIX 2: Check if this is the latest round
    last_round = await get_last_round(db_round.application_id, db)
    if last_round and last_round.id != db_round.id:
        raise HTTPException(
            status_code=400,
            detail="Can only delete the most recent round"
        )

    await db.delete(db_round)
    await db.flush()
    
    # FIX 1: Recompute application status after deletion
    app_result = await db.execute(select(Application).filter(Application.id == db_round.application_id))
    application = app_result.scalar_one_or_none()
    if application:
        last_round = await get_last_round(db_round.application_id, db)
        
        if not last_round:
            # No rounds left → reset to APPLIED
            application.status = ApplicationStatus.APPLIED
        elif last_round.result == RoundResult.FAILED:
            # Last round failed → REJECTED
            application.status = ApplicationStatus.REJECTED
        else:
            # Other results → IN_PROGRESS
            application.status = ApplicationStatus.IN_PROGRESS
    
    await db.commit()
