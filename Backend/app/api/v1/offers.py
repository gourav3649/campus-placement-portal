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

    # Notify student of offer
    student_result = await db.execute(select(Student).filter(Student.id == application.student_id))
    student = student_result.scalar_one_or_none()
    if student:
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
    """
    Student responds to an offer (accept or decline).
    
    When student ACCEPTS an offer:
    - Lock the offer row to prevent race conditions
    - Check if student already has another accepted offer
    - If not, mark this offer as ACCEPTED
    - Mark student as placed
    - Revoke all other EXTENDED offers for this student
    - Update related application status
    - All changes atomic (transaction-safe)
    """
    try:
        # FIX 2: Load policy BEFORE acquiring locks
        from app.services.policy_service import get_active_policy, is_dream_job
        policy = await get_active_policy(db)
        
        # FIX 1 - Lock student first
        await db.execute(
            select(Student).filter(Student.id == student.id).with_for_update()
        )
        
        # Then lock offer
        result = await db.execute(
            select(Offer).filter(Offer.id == offer_id, Offer.student_id == student.id).with_for_update()
        )
        offer = result.scalar_one_or_none()
        if not offer:
            raise HTTPException(status_code=404, detail="Offer not found")
        if offer.status != OfferStatus.EXTENDED:
            raise HTTPException(status_code=400, detail="Offer has already been responded to")

        if response.accept:
            
            # FIX 3: Count ALL accepted offers and check max_offers_per_student
            accepted_offers_result = await db.execute(
                select(Offer).filter(
                    Offer.student_id == offer.student_id,
                    Offer.status == OfferStatus.ACCEPTED
                )
            )
            accepted_offers = accepted_offers_result.scalars().all()
            accepted_count = len(accepted_offers)
            
            # Enforce max offers policy
            if accepted_count >= policy.max_offers_per_student:
                raise HTTPException(
                    status_code=400,
                    detail=f"You cannot accept more than {policy.max_offers_per_student} offer(s)"
                )
            
            # FIX 4: Check if ANY accepted offer is dream
            if accepted_offers:
                is_current_dream = is_dream_job(offer.ctc, policy.dream_company_ctc_threshold)
                existing_has_dream = any(
                    is_dream_job(o.ctc, policy.dream_company_ctc_threshold)
                    for o in accepted_offers
                )
                
                # If existing has dream and current is not, block
                if existing_has_dream and not is_current_dream:
                    raise HTTPException(
                        status_code=400,
                        detail="You have already accepted a dream company offer. Cannot accept non-dream offer."
                    )
            
            # FIX 2 - Step 3: Correct acceptance flow
            offer.status = OfferStatus.ACCEPTED
            
            # Mark student as placed
            student_result = await db.execute(
                select(Student).filter(Student.id == offer.student_id)
            )
            student_to_update = student_result.scalar_one()
            student_to_update.is_placed = True
            
            # Mark related application as accepted
            application_result = await db.execute(
                select(Application).filter(Application.id == offer.application_id)
            )
            application = application_result.scalar_one()
            
            # FIX 4 - Guard Application Status Before Accept
            if application.status in [ApplicationStatus.REJECTED, ApplicationStatus.WITHDRAWN]:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot accept offer for invalid application state"
                )
            
            application.status = ApplicationStatus.ACCEPTED
            
            # FIX 2 - Step 4: Revoke other offers
            other_offers_result = await db.execute(
                select(Offer).filter(
                    Offer.student_id == offer.student_id,
                    Offer.id != offer.id,
                    Offer.status == OfferStatus.EXTENDED
                )
            )
            other_offers = other_offers_result.scalars().all()
            
            for other_offer in other_offers:
                other_offer.status = OfferStatus.REVOKED
            
            # Create notification for student accepting offer
            from app.models.notification import NotificationType
            await create_notification(
                db,
                user_id=student.user_id,
                title="Offer Accepted ✓",
                message=f"Congratulations! You have accepted the offer for {offer.ctc} LPA. Other offers have been revoked.",
                notification_type=NotificationType.OFFER_EXTENDED,
                related_application_id=offer.application_id,
            )
            
            # Create notifications for other offers being revoked
            for other_offer in other_offers:
                await create_notification(
                    db,
                    user_id=student.user_id,
                    title="Other Offer Revoked",
                    message="Since you accepted an offer from another company, this offer has been automatically revoked.",
                    notification_type=NotificationType.OFFER_EXTENDED,
                    related_application_id=other_offer.application_id,
                )
        else:
            # Student is declining this offer
            offer.status = OfferStatus.DECLINED
            
            # Create notification
            from app.models.notification import NotificationType
            await create_notification(
                db,
                user_id=student.user_id,
                title="Offer Declined",
                message="You have declined the offer. You can continue exploring other opportunities.",
                notification_type=NotificationType.OFFER_EXTENDED,
                related_application_id=offer.application_id,
            )
        
        # Commit all changes atomically
        await db.commit()
        await db.refresh(offer)
        
    # FIX 1 - Correct Exception Handling
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Internal error while processing offer"
        )
    
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
