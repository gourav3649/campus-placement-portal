"""
PHASE 2: Application Workflow Validation Service

Enforces:
1. Valid state transitions
2. Round progression rules
3. Final state immutability
4. Round number incrementality
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.models.application import Application, ApplicationStatus
from app.models.application_round import ApplicationRound, RoundResult


# Valid state transitions
VALID_TRANSITIONS = {
    ApplicationStatus.APPLIED: [ApplicationStatus.IN_PROGRESS, ApplicationStatus.REJECTED, ApplicationStatus.WITHDRAWN],
    ApplicationStatus.IN_PROGRESS: [ApplicationStatus.ACCEPTED, ApplicationStatus.REJECTED, ApplicationStatus.WITHDRAWN],
    ApplicationStatus.REJECTED: [],  # Final state - immutable
    ApplicationStatus.ACCEPTED: [],  # Final state - immutable
    ApplicationStatus.WITHDRAWN: [],  # Final state - immutable
}


async def validate_status_transition(
    current_status: ApplicationStatus,
    new_status: ApplicationStatus
) -> bool:
    """
    PHASE 2: Validate state transition.
    
    Returns True if transition is allowed, raises HTTPException if invalid.
    """
    if current_status == new_status:
        return True
    
    allowed_transitions = VALID_TRANSITIONS.get(current_status, [])
    
    if new_status not in allowed_transitions:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from {current_status.value} to {new_status.value}"
        )
    
    return True


async def can_add_round(
    application: Application,
    db: AsyncSession
) -> tuple[bool, str]:
    """
    PHASE 2: Check if new round can be added.
    
    Rules:
    - Cannot add round if application is ACCEPTED/REJECTED/WITHDRAWN
    - Cannot add round if last round result was FAILED
    - Application must be in IN_PROGRESS status
    
    Returns: (can_add: bool, reason: str)
    """
    # Final states - no more rounds
    if application.status in [ApplicationStatus.ACCEPTED, ApplicationStatus.REJECTED, ApplicationStatus.WITHDRAWN]:
        return (False, f"Cannot add rounds to {application.status.value} application")
    
    # Must be IN_PROGRESS to add rounds
    if application.status != ApplicationStatus.IN_PROGRESS:
        return (False, f"Application must be IN_PROGRESS to add rounds (currently {application.status.value})")
    
    # Check if last round failed
    if application.rounds:
        last_round = max(application.rounds, key=lambda r: r.round_number)
        if last_round.result == RoundResult.FAILED:
            return (False, "Cannot add round after FAILED result")
    
    return (True, "")


async def validate_round_progression(
    application_id: int,
    new_round_number: int,
    db: AsyncSession
) -> tuple[bool, str]:
    """
    PHASE 2: Validate round number progression.
    
    Rules:
    - Round numbers must strictly increase
    - Cannot skip round numbers
    
    Returns: (valid: bool, reason: str)
    """
    # Get all rounds for this application
    rounds_result = await db.execute(
        select(ApplicationRound).filter(ApplicationRound.application_id == application_id)
    )
    existing_rounds = rounds_result.scalars().all()
    
    if not existing_rounds:
        # First round must be 1
        if new_round_number != 1:
            return (False, "First round number must be 1")
        return (True, "")
    
    max_round_number = max(r.round_number for r in existing_rounds)
    
    # New round must be max + 1
    if new_round_number != max_round_number + 1:
        return (False, f"Round number must be {max_round_number + 1} (next in sequence)")
    
    return (True, "")


async def get_last_round(
    application_id: int,
    db: AsyncSession
) -> ApplicationRound | None:
    """Get the most recent round for an application."""
    result = await db.execute(
        select(ApplicationRound)
        .filter(ApplicationRound.application_id == application_id)
        .order_by(ApplicationRound.round_number.desc())
    )
    return result.scalars().first()


async def can_modify_round(
    round_id: int,
    db: AsyncSession
) -> tuple[bool, str]:
    """
    PHASE 2: Check if round can be modified.
    
    Rule: Cannot modify if newer rounds exist (immutable history)
    
    Returns: (can_modify: bool, reason: str)
    """
    # Get the round
    round_result = await db.execute(
        select(ApplicationRound).filter(ApplicationRound.id == round_id)
    )
    target_round = round_result.scalar_one_or_none()
    
    if not target_round:
        return (False, "Round not found")
    
    # Check if there are newer rounds
    newer_rounds_result = await db.execute(
        select(ApplicationRound).filter(
            ApplicationRound.application_id == target_round.application_id,
            ApplicationRound.round_number > target_round.round_number
        )
    )
    
    if newer_rounds_result.scalars().first():
        return (False, "Cannot modify past rounds (newer rounds exist)")
    
    return (True, "")
