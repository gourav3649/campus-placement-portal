"""
Eligibility service: checks a student against a job's requirements.
Returns (is_eligible, list_of_reasons).
"""
from typing import Tuple, List
from datetime import datetime
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.student import Student
from app.models.job import Job
from app.models.application import Application, ApplicationStatus

logger = logging.getLogger(__name__)


def check_eligibility(student: Student, job: Job) -> Tuple[bool, List[str]]:
    failures: List[str] = []

    # 1. CGPA check
    if job.min_cgpa is not None and student.cgpa < job.min_cgpa:
        failures.append(
            f"CGPA {student.cgpa:.2f} is below the minimum required {job.min_cgpa:.2f}"
        )

    # 2. Branch check
    if job.allowed_branches:
        if student.branch not in job.allowed_branches:
            failures.append(
                f"Branch '{student.branch}' is not in the allowed branches: {', '.join(job.allowed_branches)}"
            )

    # 3. Backlogs check
    if job.max_backlogs is not None:
        # If max_backlogs is 0, students with any backlog are excluded
        if student.has_backlogs and job.max_backlogs == 0:
            failures.append("Students with active backlogs are not eligible for this drive")

    # 4. Already placed check
    if job.exclude_placed_students and student.is_placed:
        failures.append("Already placed students are not eligible for this drive")

    return (len(failures) == 0, failures)


class EligibilityService:
    """Async eligibility checking service for applications."""
    
    async def check_application_eligibility(
        self,
        db: AsyncSession,
        application: Application,
        update_db: bool = False,
    ) -> Tuple[bool, List[str]]:
        """
        Check if an application is eligible based on student and job requirements.
        
        Args:
            db: Database session
            application: Application to check
            update_db: If True, update application status and eligibility_reasons in DB
        
        Returns:
            Tuple of (is_eligible, failure_reasons)
        """
        try:
            # Fetch student
            student_result = await db.execute(
                select(Student).filter(Student.id == application.student_id)
            )
            student = student_result.scalar_one_or_none()
            
            if not student:
                logger.error(f"Student not found for application {application.id}")
                reasons = ["Student record not found"]
                return (False, reasons)
            
            # Fetch job
            job_result = await db.execute(
                select(Job).filter(Job.id == application.job_id)
            )
            job = job_result.scalar_one_or_none()
            
            if not job:
                logger.error(f"Job not found for application {application.id}")
                reasons = ["Job record not found"]
                return (False, reasons)
            
            # Check eligibility using the utility function
            is_eligible, failure_reasons = check_eligibility(student, job)
            
            logger.info(
                f"Eligibility check for application {application.id}: "
                f"is_eligible={is_eligible}, reasons={failure_reasons}"
            )
            
            # Update database if requested
            if update_db:
                import json
                if not is_eligible:
                    application.status = ApplicationStatus.ELIGIBILITY_FAILED
                    application.eligibility_reasons = json.dumps(failure_reasons)
                    application.eligibility_checked_at = datetime.utcnow()
                else:
                    # Mark as ELIGIBLE if it's still PENDING
                    if application.status == ApplicationStatus.PENDING:
                        application.status = ApplicationStatus.ELIGIBLE
                    application.eligibility_checked_at = datetime.utcnow()
                
                await db.commit()
                await db.refresh(application)
                logger.debug(f"Updated application {application.id} status to {application.status}")
            
            return (is_eligible, failure_reasons)
            
        except Exception as e:
            logger.error(f"Error checking eligibility for application {application.id}: {str(e)}", exc_info=True)
            return (False, [f"Eligibility check error: {str(e)}"])

