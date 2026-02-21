"""
Eligibility Service

High-level service for eligibility checking with database integration.
Handles:
1. Checking eligibility for single application
2. Filtering eligible applications for bulk ranking  
3. Updating application status based on eligibility
4. Analytics on eligibility filtering
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.student import Student
from app.models.job import Job
from app.models.application import Application, ApplicationStatus
from app.eligibility.rules_engine import EligibilityEngine

logger = logging.getLogger(__name__)


class EligibilityService:
    """
    Service layer for eligibility checking.
    
    Responsibilities:
    - Check eligibility for applications
    - Mark ineligible applications in database
    - Filter applications for AI ranking
    - Provide eligibility analytics
    """
    
    def __init__(self):
        """Initialize with eligibility engine."""
        self.engine = EligibilityEngine()
    
    async def check_application_eligibility(
        self,
        db: AsyncSession,
        application: Application,
        update_db: bool = True
    ) -> Tuple[bool, List[str]]:
        """
        Check eligibility for a single application.
        
        Args:
            db: Database session
            application: Application to check
            update_db: If True, update application record with results
            
        Returns:
            (is_eligible, failure_reasons)
        """
        # Fetch student
        student_result = await db.execute(
            select(Student).filter(Student.id == application.student_id)
        )
        student = student_result.scalar_one_or_none()
        
        if not student:
            logger.error(f"Student {application.student_id} not found for application {application.id}")
            return False, ["student_not_found"]
        
        # Fetch job
        job_result = await db.execute(
            select(Job).filter(Job.id == application.job_id)
        )
        job = job_result.scalar_one_or_none()
        
        if not job:
            logger.error(f"Job {application.job_id} not found for application {application.id}")
            return False, ["job_not_found"]
        
        # Run eligibility check
        is_eligible, failure_reasons = self.engine.check_eligibility(student, job)
        
        # Update application if requested
        if update_db:
            application.is_eligible = is_eligible
            application.eligibility_reasons = json.dumps(failure_reasons) if failure_reasons else None
            application.eligibility_checked_at = datetime.now()
            
            # If ineligible, mark application as rejected
            if not is_eligible:
                application.status = ApplicationStatus.ELIGIBILITY_FAILED
                logger.info(
                    f"Application {application.id} marked ineligible: {', '.join(failure_reasons)}"
                )
            
            await db.commit()
            await db.refresh(application)
        
        return is_eligible, failure_reasons
    
    async def filter_eligible_applications(
        self,
        db: AsyncSession,
        job_id: int,
        check_all: bool = False
    ) -> List[Application]:
        """
        Get all eligible applications for a job.
        
        This is the CRITICAL method called before AI ranking.
        AI should ONLY process applications returned by this method.
        
        Args:
            db: Database session
            job_id: Job ID to filter applications for
            check_all: If True, recheck all applications. If False, use cached results.
            
        Returns:
            List of eligible applications
        """
        # Fetch all applications for this job
        query = select(Application).filter(Application.job_id == job_id)
        result = await db.execute(query)
        applications = result.scalars().all()
        
        eligible_applications = []
        
        for app in applications:
            # If already checked and failed, skip
            if app.is_eligible == False and not check_all:
                continue
            
            # If already checked and passed, include
            if app.is_eligible == True and not check_all:
                eligible_applications.append(app)
                continue
            
            # Not yet checked or forcing recheck
            is_eligible, reasons = await self.check_application_eligibility(
                db, app, update_db=True
            )
            
            if is_eligible:
                eligible_applications.append(app)
        
        logger.info(
            f"Filtered {len(eligible_applications)} eligible applications "
            f"out of {len(applications)} total for job {job_id}"
        )
        
        return eligible_applications
    
    async def bulk_check_eligibility(
        self,
        db: AsyncSession,
        application_ids: List[int]
    ) -> Dict[int, Tuple[bool, List[str]]]:
        """
        Check eligibility for multiple applications at once.
        
        Args:
            db: Database session
            application_ids: List of application IDs to check
            
        Returns:
            Dictionary mapping application_id -> (is_eligible, reasons)
        """
        results = {}
        
        for app_id in application_ids:
            # Fetch application
            app_result = await db.execute(
                select(Application).filter(Application.id == app_id)
            )
            app = app_result.scalar_one_or_none()
            
            if not app:
                results[app_id] = (False, ["application_not_found"])
                continue
            
            # Check eligibility
            is_eligible, reasons = await self.check_application_eligibility(
                db, app, update_db=True
            )
            
            results[app_id] = (is_eligible, reasons)
        
        return results
    
    async def get_eligibility_stats(
        self,
        db: AsyncSession,
        job_id: int
    ) -> Dict[str, any]:
        """
        Get eligibility statistics for a job.
        
        Useful for placement officers to understand:
        - How many students are eligible
        - Common rejection reasons
        - CGPA/branch distribution
        
        Args:
            db: Database session
            job_id: Job ID
            
        Returns:
            Dictionary with statistics
        """
        # Fetch all applications
        query = select(Application).filter(Application.job_id == job_id)
        result = await db.execute(query)
        applications = result.scalars().all()
        
        stats = {
            "total_applications": len(applications),
            "eligible_count": 0,
            "ineligible_count": 0,
            "not_checked_count": 0,
            "rejection_reasons": {},
        }
        
        for app in applications:
            if app.is_eligible is None:
                stats["not_checked_count"] += 1
            elif app.is_eligible:
                stats["eligible_count"] += 1
            else:
                stats["ineligible_count"] += 1
                
                # Parse rejection reasons
                if app.eligibility_reasons:
                    try:
                        reasons = json.loads(app.eligibility_reasons)
                        for reason in reasons:
                            stats["rejection_reasons"][reason] = \
                                stats["rejection_reasons"].get(reason, 0) + 1
                    except json.JSONDecodeError:
                        pass
        
        # Calculate percentages
        if stats["total_applications"] > 0:
            stats["eligible_percentage"] = (
                stats["eligible_count"] / stats["total_applications"] * 100
            )
            stats["ineligible_percentage"] = (
                stats["ineligible_count"] / stats["total_applications"] * 100
            )
        
        return stats
    
    async def mark_ineligible_applications(
        self,
        db: AsyncSession,
        job_id: int
    ) -> int:
        """
        Check and mark all ineligible applications for a job.
        
        This should be run:
        1. After job is approved by placement officer
        2. Before AI ranking is triggered
        3. When eligibility rules are updated
        
        Args:
            db: Database session
            job_id: Job ID
            
        Returns:
            Number of applications marked as ineligible
        """
        ineligible_count = 0
        
        # Fetch all pending applications
        query = select(Application).filter(
            Application.job_id == job_id,
            Application.status == ApplicationStatus.PENDING
        )
        result = await db.execute(query)
        applications = result.scalars().all()
        
        for app in applications:
            is_eligible, reasons = await self.check_application_eligibility(
                db, app, update_db=True
            )
            
            if not is_eligible:
                ineligible_count += 1
        
        logger.info(
            f"Marked {ineligible_count} applications as ineligible for job {job_id}"
        )
        
        return ineligible_count
    
    async def revalidate_all_applications(
        self,
        db: AsyncSession,
        job_id: int
    ) -> Dict[str, int]:
        """
        Revalidate eligibility for ALL applications (both eligible and ineligible).
        
        Use cases:
        1. Job eligibility rules updated (min_cgpa, allowed_branches, etc.)
        2. Defensive check before ranking
        3. Manual revalidation triggered by placement officer
        
        This differs from mark_ineligible_applications which only checks PENDING apps.
        This method rechecks ALL applications to catch:
        - Previously eligible apps that became ineligible (e.g., student got placed)
        - Previously ineligible apps that became eligible (e.g., rules loosened)
        
        Args:
            db: Database session
            job_id: Job ID
            
        Returns:
            Dictionary with revalidation statistics
        """
        # Fetch ALL applications for this job (regardless of status)
        query = select(Application).filter(Application.job_id == job_id)
        result = await db.execute(query)
        applications = result.scalars().all()
        
        stats = {
            "total_applications": len(applications),
            "newly_eligible": 0,        # Was ineligible, now eligible
            "newly_ineligible": 0,      # Was eligible, now ineligible
            "still_eligible": 0,
            "still_ineligible": 0,
            "eligibility_changes": []   # Detailed change log
        }
        
        for app in applications:
            old_eligibility = app.is_eligible
            
            # Recheck eligibility
            is_eligible, reasons = await self.check_application_eligibility(
                db, app, update_db=True
            )
            
            # Track changes
            if old_eligibility is None:
                # First time checked
                if is_eligible:
                    stats["newly_eligible"] += 1
                else:
                    stats["newly_ineligible"] += 1
            elif old_eligibility == True and is_eligible == False:
                # Became ineligible
                stats["newly_ineligible"] += 1
                stats["eligibility_changes"].append({
                    "application_id": app.id,
                    "student_id": app.student_id,
                    "change": "eligible_to_ineligible",
                    "reasons": reasons
                })
                logger.warning(
                    f"Application {app.id} became INELIGIBLE: {', '.join(reasons)}"
                )
            elif old_eligibility == False and is_eligible == True:
                # Became eligible
                stats["newly_eligible"] += 1
                stats["eligibility_changes"].append({
                    "application_id": app.id,
                    "student_id": app.student_id,
                    "change": "ineligible_to_eligible",
                    "reasons": []
                })
                logger.info(
                    f"Application {app.id} became ELIGIBLE (rules may have changed)"
                )
            elif is_eligible:
                stats["still_eligible"] += 1
            else:
                stats["still_ineligible"] += 1
        
        logger.info(
            f"Revalidated {stats['total_applications']} applications for job {job_id}: "
            f"{stats['newly_ineligible']} became ineligible, {stats['newly_eligible']} became eligible"
        )
        
        return stats
