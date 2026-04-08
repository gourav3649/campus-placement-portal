from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Any

from app.database import get_db
from app.models.offer import Offer, OfferStatus
from app.models.application import Application, ApplicationStatus
from app.models.student import Student
from app.models.notification import NotificationType
from app.schemas.offer import OfferCreate, OfferUpdate, OfferRespond, OfferResponse
from app.api.deps import get_current_placement_officer, get_current_student
from app.services.notification_service import create_notification

router = APIRouter()


@router.post("/", response_model=OfferResponse, status_code=status.HTTP_201_CREATED)
async def create_offer(
    offer_in: OfferCreate,
    db: AsyncSession = Depends(get_db),
    officer: Any = Depends(get_current_placement_officer),
) -> Any:
    """Officer creates an offer. Auto-marks student as placed and application as ACCEPTED."""
    app_result = await db.execute(select(Application).filter(Application.id == offer_in.application_id))
    application = app_result.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    # Check no offer already exists
    existing = await db.execute(select(Offer).filter(Offer.application_id == offer_in.application_id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="An offer already exists for this application")

    # Create offer
    offer = Offer(
        application_id=offer_in.application_id,
        student_id=application.student_id,
        job_id=application.job_id,
        ctc=offer_in.ctc,
        joining_date=offer_in.joining_date,
        offer_letter_url=offer_in.offer_letter_url,
        status=OfferStatus.EXTENDED,
    )
    db.add(offer)

    # Mark application as ACCEPTED
    application.status = ApplicationStatus.ACCEPTED

    # Mark student as placed
    student_result = await db.execute(select(Student).filter(Student.id == application.student_id))
    student = student_result.scalar_one_or_none()
    if student:
        student.is_placed = True
        await create_notification(
            db,
            user_id=student.user_id,
            title="You received an offer! 🎉",
            message=f"Congratulations! You've received an offer{f' of {offer_in.ctc} LPA' if offer_in.ctc else ''}. Please accept or decline from your Applications page.",
            notification_type=NotificationType.OFFER_EXTENDED,
            related_application_id=offer_in.application_id,
        )

    await db.commit()
    await db.refresh(offer)
    return offer


@router.get("/me", response_model=List[OfferResponse])
async def my_offers(
    db: AsyncSession = Depends(get_db),
    student: Student = Depends(get_current_student),
) -> Any:
    result = await db.execute(select(Offer).filter(Offer.student_id == student.id))
    return result.scalars().all()


@router.put("/{offer_id}/respond", response_model=OfferResponse)
async def respond_to_offer(
    offer_id: int,
    response: OfferRespond,
    db: AsyncSession = Depends(get_db),
    student: Student = Depends(get_current_student),
) -> Any:
    result = await db.execute(select(Offer).filter(Offer.id == offer_id, Offer.student_id == student.id))
    offer = result.scalar_one_or_none()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    if offer.status != OfferStatus.EXTENDED:
        raise HTTPException(status_code=400, detail="Offer has already been responded to")

    offer.status = OfferStatus.ACCEPTED if response.accept else OfferStatus.DECLINED
    await db.commit()
    await db.refresh(offer)
    return offer


@router.put("/{offer_id}", response_model=OfferResponse)
async def update_offer(
    offer_id: int,
    offer_in: OfferUpdate,
    db: AsyncSession = Depends(get_db),
    officer: Any = Depends(get_current_placement_officer),
) -> Any:
    result = await db.execute(select(Offer).filter(Offer.id == offer_id))
    offer = result.scalar_one_or_none()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")

    for field, value in offer_in.model_dump(exclude_unset=True).items():
        setattr(offer, field, value)
    await db.commit()
    await db.refresh(offer)
    return offer


@router.get("/job/{job_id}", response_model=List[OfferResponse])
async def offers_for_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    officer: Any = Depends(get_current_placement_officer),
) -> Any:
    result = await db.execute(select(Offer).filter(Offer.job_id == job_id))
    return result.scalars().all()
