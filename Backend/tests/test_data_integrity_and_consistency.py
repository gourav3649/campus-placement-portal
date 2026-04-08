"""
Phase 2.5: Data Integrity & Cross-Role Consistency Tests.
Verify that Officer, Recruiter, and Student views show identical data.
"""

import pytest
import time
from typing import Tuple, List
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application, ApplicationStatus
from app.models.application_round import ApplicationRound
from app.models.job import Job, JobType, DriveStatus
from app.models.student import Student
from app.models.user import User
from app.models.college import College
from app.core.security import hash_password
from app.core.rbac import Role

from tests.stress_test_utils import (
    TestReporter,
    TestResult,
    generate_unique_id,
    generate_email,
    DBValidator,
)
from tests.fixtures import (
    db_session,
    base_college,
    recruiter_user,
    bulk_students_100,
)


class TestDataIntegrityConsistency:
    """
    Verify data integrity across different views and roles.
    """
    
    reporter = TestReporter()
    
    @pytest.mark.asyncio
    async def test_application_data_consistency_across_views(
        self,
        db_session: AsyncSession,
        base_college: College,
        recruiter_user: Tuple[User],
        bulk_students_100: List,
    ):
        """
        Create application with rounds → Fetch from Officer, Recruiter, Student views.
        Verify all return identical data.
        """
        test_name = "test_application_data_consistency_across_views"
        start_time = time.time()
        
        try:
            _, recruiter = recruiter_user
            
            # Setup: Job + Student + Application + Rounds
            job = Job(
                college_id=base_college.id,
                recruiter_id=recruiter.id,
                title=f"Job {generate_unique_id()}",
                description="Test job",
                job_type=JobType.FULL_TIME,
                min_cgpa=7.0,
                allowed_branches=["CSE"],
                status=DriveStatus.APPROVED,
            )
            db_session.add(job)
            await db_session.flush()
            
            student = bulk_students_100[0]
            
            app = Application(
                student_id=student.id,
                job_id=job.id,
                status=ApplicationStatus.REVIEWING,
                is_eligible=True,
            )
            db_session.add(app)
            await db_session.commit()
            await db_session.refresh(app)
            app_id = app.id
            
            # Add 2 rounds
            for i in [1, 2]:
                round_obj = ApplicationRound(
                    application_id=app_id,
                    round_number=i,
                    round_name=f"Round {i}",
                    result="PASSED" if i == 1 else "PENDING",
                )
                db_session.add(round_obj)
            
            await db_session.commit()
            
            # Fetch from different "views" (all from same session for now, simulating API calls)
            # Officer view: all applications for job
            officer_result = await db_session.execute(
                select(Application)
                .options(
                    selectinload(Application.student),
                    selectinload(Application.job),
                    selectinload(Application.rounds),
                )
                .filter(Application.job_id == job.id)
            )
            officer_apps = officer_result.scalars().unique().all()
            officer_app = officer_apps[0] if officer_apps else None
            
            # Recruiter view: all applications for their job
            recruiter_result = await db_session.execute(
                select(Application)
                .options(
                    selectinload(Application.student),
                    selectinload(Application.job),
                    selectinload(Application.rounds),
                )
                .filter(Application.job_id == job.id)
            )
            recruiter_apps = recruiter_result.scalars().unique().all()
            recruiter_app = recruiter_apps[0] if recruiter_apps else None
            
            # Student view: their own application
            student_result = await db_session.execute(
                select(Application)
                .options(
                    selectinload(Application.student),
                    selectinload(Application.job),
                    selectinload(Application.rounds),
                )
                .filter(Application.id == app_id, Application.student_id == student.id)
            )
            student_app = student_result.scalar_one_or_none()
            
            # Assertions for consistency
            assert officer_app is not None, "Officer should see application"
            assert recruiter_app is not None, "Recruiter should see application"
            assert student_app is not None, "Student should see their application"
            
            # Check all have same ID, status, student name, job title
            assert officer_app.id == recruiter_app.id == student_app.id == app_id, "IDs should match"
            assert officer_app.status == recruiter_app.status == student_app.status == ApplicationStatus.REVIEWING, "Status should match"
            assert officer_app.student.first_name == recruiter_app.student.first_name == student_app.student.first_name, "Student names should match"
            assert officer_app.job.title == recruiter_app.job.title == student_app.job.title, "Job titles should match"
            
            # Check rounds are identical
            officer_round_names = sorted([r.round_name for r in officer_app.rounds])
            recruiter_round_names = sorted([r.round_name for r in recruiter_app.rounds])
            student_round_names = sorted([r.round_name for r in student_app.rounds])
            
            assert officer_round_names == recruiter_round_names == student_round_names == ["Round 1", "Round 2"], \
                f"Round names should match: O={officer_round_names}, R={recruiter_round_names}, S={student_round_names}"
            
            duration_ms = (time.time() - start_time) * 1000
            self.reporter.add_result(TestResult(
                test_name=test_name,
                passed=True,
                duration_ms=duration_ms,
            ))
        
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.reporter.add_result(TestResult(
                test_name=test_name,
                passed=False,
                duration_ms=duration_ms,
                error_msg=str(e),
            ))
            raise
    
    @pytest.mark.asyncio
    async def test_bulk_update_consistency_across_roles(
        self,
        db_session: AsyncSession,
        base_college: College,
        recruiter_user: Tuple[User],
        bulk_students_100: List,
    ):
        """
        Officer bulk-updates 20 applicants from PENDING to REVIEWING.
        Verify all roles see the updated status consistently.
        """
        test_name = "test_bulk_update_consistency_across_roles"
        start_time = time.time()
        
        try:
            _, recruiter = recruiter_user
            
            # Setup: Job + 20 applications
            job = Job(
                college_id=base_college.id,
                recruiter_id=recruiter.id,
                title=f"Job {generate_unique_id()}",
                description="Test job",
                job_type=JobType.FULL_TIME,
                min_cgpa=7.0,
                allowed_branches=["CSE"],
                status=DriveStatus.APPROVED,
            )
            db_session.add(job)
            await db_session.flush()
            
            app_ids = []
            for i in range(20):
                app = Application(
                    student_id=bulk_students_100[i].id,
                    job_id=job.id,
                    status=ApplicationStatus.PENDING,
                    is_eligible=True,
                )
                db_session.add(app)
                await db_session.flush()
                app_ids.append(app.id)
            
            await db_session.commit()
            
            # Simulate officer bulk update
            for app_id in app_ids[:10]:  # Update first 10
                result = await db_session.execute(
                    select(Application).filter(Application.id == app_id)
                )
                app = result.scalar_one()
                app.status = ApplicationStatus.REVIEWING
            
            await db_session.commit()
            
            # Verify from multiple views
            # Officer view
            officer_result = await db_session.execute(
                select(Application)
                .filter(Application.job_id == job.id)
                .order_by(Application.id)
            )
            officer_apps = officer_result.scalars().all()
            
            # Recruiter view
            recruiter_result = await db_session.execute(
                select(Application)
                .filter(Application.job_id == job.id)
                .order_by(Application.id)
            )
            recruiter_apps = recruiter_result.scalars().all()
            
            # Verify counts match
            assert len(officer_apps) == len(recruiter_apps) == 20, "Both views should see 20 apps"
            
            # Verify status distribution matches
            officer_reviewing = sum(1 for a in officer_apps if a.status == ApplicationStatus.REVIEWING)
            recruiter_reviewing = sum(1 for a in recruiter_apps if a.status == ApplicationStatus.REVIEWING)
            officer_pending = sum(1 for a in officer_apps if a.status == ApplicationStatus.PENDING)
            recruiter_pending = sum(1 for a in recruiter_apps if a.status == ApplicationStatus.PENDING)
            
            assert officer_reviewing == recruiter_reviewing == 10, f"Both should see 10 REVIEWING, got O={officer_reviewing}, R={recruiter_reviewing}"
            assert officer_pending == recruiter_pending == 10, f"Both should see 10 PENDING, got O={officer_pending}, R={recruiter_pending}"
            
            # Verify each app's status matches
            for officer_app, recruiter_app in zip(officer_apps, recruiter_apps):
                assert officer_app.id == recruiter_app.id, f"App ID mismatch"
                assert officer_app.status == recruiter_app.status, \
                    f"App {officer_app.id}: Officer sees {officer_app.status}, Recruiter sees {recruiter_app.status}"
            
            duration_ms = (time.time() - start_time) * 1000
            self.reporter.add_result(TestResult(
                test_name=test_name,
                passed=True,
                duration_ms=duration_ms,
            ))
        
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.reporter.add_result(TestResult(
                test_name=test_name,
                passed=False,
                duration_ms=duration_ms,
                error_msg=str(e),
            ))
            raise
    
    @pytest.mark.asyncio
    async def test_no_orphaned_records_after_deletion(
        self,
        db_session: AsyncSession,
        base_college: College,
        recruiter_user: Tuple[User],
        bulk_students_100: List,
    ):
        """
        Create applications with rounds, delete some applications.
        Verify no orphaned rounds remain.
        """
        test_name = "test_no_orphaned_records_after_deletion"
        start_time = time.time()
        
        try:
            _, recruiter = recruiter_user
            
            # Setup: Job + 10 applications with rounds
            job = Job(
                college_id=base_college.id,
                recruiter_id=recruiter.id,
                title=f"Job {generate_unique_id()}",
                description="Test job",
                job_type=JobType.FULL_TIME,
                min_cgpa=7.0,
                allowed_branches=["CSE"],
                status=DriveStatus.APPROVED,
            )
            db_session.add(job)
            await db_session.flush()
            
            app_ids = []
            for i in range(10):
                app = Application(
                    student_id=bulk_students_100[i].id,
                    job_id=job.id,
                    status=ApplicationStatus.REVIEWING,
                    is_eligible=True,
                )
                db_session.add(app)
                await db_session.flush()
                app_ids.append(app.id)
                
                # Add 2 rounds to each
                for j in [1, 2]:
                    round_obj = ApplicationRound(
                        application_id=app.id,
                        round_number=j,
                        round_name=f"Round {j}",
                        result="PASSED",
                    )
                    db_session.add(round_obj)
            
            await db_session.commit()
            
            # Verify initial state: 10 apps, 20 rounds
            app_count = await db_session.scalar(
                select(len(select(Application).filter(Application.job_id == job.id).subquery()))
            )
            # (Fallback for count)
            app_cnt_result = await db_session.execute(
                select(Application).filter(Application.job_id == job.id)
            )
            app_cnt = len(app_cnt_result.scalars().all())
            
            round_cnt_result = await db_session.execute(
                select(ApplicationRound).filter(
                    ApplicationRound.application_id.in_(app_ids)
                )
            )
            round_cnt = len(round_cnt_result.scalars().all())
            
            assert app_cnt == 10, f"Expected 10 apps, got {app_cnt}"
            assert round_cnt == 20, f"Expected 20 rounds, got {round_cnt}"
            
            # Delete 5 applications (should cascade-delete their rounds)
            for app_id in app_ids[:5]:
                result = await db_session.execute(
                    select(Application).filter(Application.id == app_id)
                )
                app_to_delete = result.scalar_one()
                await db_session.delete(app_to_delete)
            
            await db_session.commit()
            
            # Verify after deletion: 5 apps, 10 rounds
            final_app_result = await db_session.execute(
                select(Application).filter(Application.job_id == job.id)
            )
            final_app_cnt = len(final_app_result.scalars().all())
            
            final_round_result = await db_session.execute(
                select(ApplicationRound).filter(
                    ApplicationRound.application_id.in_(app_ids)
                )
            )
            final_round_cnt = len(final_round_result.scalars().all())
            
            assert final_app_cnt == 5, f"Expected 5 apps after deletion, got {final_app_cnt}"
            assert final_round_cnt == 10, f"Expected 10 rounds after deletion, got {final_round_cnt}"
            
            # Check for orphaned rounds (rounds without valid applications)
            orphaned = await DBValidator.check_orphaned_rounds(db_session)
            assert len(orphaned) == 0, f"Found orphaned rounds: {orphaned}"
            
            duration_ms = (time.time() - start_time) * 1000
            self.reporter.add_result(TestResult(
                test_name=test_name,
                passed=True,
                duration_ms=duration_ms,
            ))
        
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.reporter.add_result(TestResult(
                test_name=test_name,
                passed=False,
                duration_ms=duration_ms,
                error_msg=str(e),
            ))
            raise
    
    @pytest.mark.asyncio
    async def test_application_state_consistency_with_rounds(
        self,
        db_session: AsyncSession,
        base_college: College,
        recruiter_user: Tuple[User],
        bulk_students_100: List,
    ):
        """
        Verify application consistency rules:
        - REJECTED/WITHDRAWN applications should not have pending future rounds
        - Applications with offers should be ACCEPTED
        """
        test_name = "test_application_state_consistency_with_rounds"
        start_time = time.time()
        
        try:
            _, recruiter = recruiter_user
            
            # Setup: Job + applications in various states
            job = Job(
                college_id=base_college.id,
                recruiter_id=recruiter.id,
                title=f"Job {generate_unique_id()}",
                description="Test job",
                job_type=JobType.FULL_TIME,
                min_cgpa=7.0,
                allowed_branches=["CSE"],
                status=DriveStatus.APPROVED,
            )
            db_session.add(job)
            await db_session.flush()
            
            apps_data = [
                (bulk_students_100[0], ApplicationStatus.REVIEWING, True),  # Normal
                (bulk_students_100[1], ApplicationStatus.REJECTED, False),   # Rejected (no rounds)
                (bulk_students_100[2], ApplicationStatus.WITHDRAWN, False),  # Withdrawn (no rounds)
            ]
            
            for i, (student, status, can_have_rounds) in enumerate(apps_data):
                app = Application(
                    student_id=student.id,
                    job_id=job.id,
                    status=status,
                    is_eligible=True,
                )
                db_session.add(app)
                await db_session.flush()
                
                # Add round only if allowed
                if can_have_rounds:
                    round_obj = ApplicationRound(
                        application_id=app.id,
                        round_number=1,
                        round_name="Round 1",
                        result="PENDING",
                    )
                    db_session.add(round_obj)
            
            await db_session.commit()
            
            # Verify consistency
            result = await db_session.execute(
                select(Application)
                .options(selectinload(Application.rounds))
                .filter(Application.job_id == job.id)
            )
            all_apps = result.scalars().unique().all()
            
            for app in all_apps:
                if app.status in (ApplicationStatus.REJECTED, ApplicationStatus.WITHDRAWN):
                    assert len(app.rounds) == 0, \
                        f"App {app.id} ({app.status}) should not have rounds, but has {len(app.rounds)}"
                else:
                    # Can have rounds
                    pass
                
                # Run validator
                is_consistent, msg = await DBValidator.verify_application_consistency(db_session, app.id)
                assert is_consistent, f"App {app.id} is inconsistent: {msg}"
            
            duration_ms = (time.time() - start_time) * 1000
            self.reporter.add_result(TestResult(
                test_name=test_name,
                passed=True,
                duration_ms=duration_ms,
            ))
        
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.reporter.add_result(TestResult(
                test_name=test_name,
                passed=False,
                duration_ms=duration_ms,
                error_msg=str(e),
            ))
            raise


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
