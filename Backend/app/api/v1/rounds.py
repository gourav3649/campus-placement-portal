from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Any

from app.database import get_db
from app.models.application_round import ApplicationRound, RoundResult
from app.models.application import Application
from app.models.student import Student
from app.models.notification import NotificationType
from app.schemas.round import RoundCreate, RoundUpdate, RoundResponse
from app.api.deps import get_current_placement_officer, get_current_student
from app.services.notification_service import create_notification

router = APIRouter()


@router.post("/applications/{app_id}/rounds", response_model=RoundResponse, status_code=status.HTTP_201_CREATED)
async def add_round(
    app_id: int,
    round_in: RoundCreate,
    db: AsyncSession = Depends(get_db),
    officer: Any = Depends(get_current_placement_officer),
) -> Any:
    app_result = await db.execute(select(Application).filter(Application.id == app_id))
    application = app_result.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    db_round = ApplicationRound(
        application_id=app_id,
        updated_by_id=officer.user_id,
        **round_in.model_dump(),
    )
    db.add(db_round)
    await db.flush()

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
    result = await db.execute(select(ApplicationRound).filter(ApplicationRound.id == round_id))
    db_round = result.scalar_one_or_none()
    if not db_round:
        raise HTTPException(status_code=404, detail="Round not found")

    old_result = db_round.result
    for field, value in round_in.model_dump(exclude_unset=True).items():
        setattr(db_round, field, value)
    db_round.updated_by_id = officer.user_id
    await db.flush()

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
    result = await db.execute(select(ApplicationRound).filter(ApplicationRound.id == round_id))
    db_round = result.scalar_one_or_none()
    if not db_round:
        raise HTTPException(status_code=404, detail="Round not found")

    await db.delete(db_round)
    await db.commit()
