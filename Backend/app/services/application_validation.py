"""
Application Validation Service - Phase 0: System Integrity Fixes

Centralized validation logic to prevent invalid placement states.
This ensures:
1. Students cannot apply after being placed
2. Students cannot have duplicate applications for same job
3. All validation happens BEFORE application creation
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.student import Student
from app.models.application import Application
from app.models.job import Job


async def validate_application_allowed(
    student: Student,
    job_id: int,
    db: AsyncSession
) -> dict:
    """
    Centralized validation before allowing application submission.
    
    Returns: {
        'allowed': bool,
        'reason': str (error message if not allowed)
    }
    
    Checks:
    1. Student is not placed
    2. Student has not already applied to this job
    3. Job exists and is accepting applications
    """
    
    # CHECK 1: Student is not placed
    if student.is_placed:
        return {
            'allowed': False,
            'reason': 'You are already placed and cannot apply to new jobs'
        }
    
    # CHECK 2: Student has not already applied to this job
    existing_app = await db.execute(
        select(Application).filter(
            Application.student_id == student.id,
            Application.job_id == job_id
        )
    )
    if existing_app.scalar_one_or_none():
        return {
            'allowed': False,
            'reason': 'You have already applied to this job'
        }
    
    # CHECK 3: Job exists
    job_result = await db.execute(
        select(Job).filter(Job.id == job_id)
    )
    job = job_result.scalar_one_or_none()
    if not job:
        return {
            'allowed': False,
            'reason': 'Job not found'
        }
    
    # CHECK 4: Job must be OPEN
    from app.models.job import JobStatus
    if job.status != JobStatus.OPEN:
        return {
            'allowed': False,
            'reason': 'This job is no longer accepting applications'
        }
    
    # CHECK 5: Drive must be APPROVED (if exists)
    from app.models.job import DriveStatus
    if hasattr(job, 'drive_status') and job.drive_status != DriveStatus.APPROVED:
        return {
            'allowed': False,
            'reason': 'This job drive is not approved'
        }
    
    return {'allowed': True, 'reason': None}
