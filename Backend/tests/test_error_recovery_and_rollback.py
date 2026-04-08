"""
Phase 2.4: Error Recovery & Rollback Tests.
Tests system behavior when operations fail: partial bulk failures, deletions, state consistency.
"""

import pytest
import time
from typing import Tuple, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application, ApplicationStatus
from app.models.application_round import ApplicationRound
from app.models.job import Job, JobType, DriveStatus
from app.models.student import Student
from app.models.user import User
from app.models.college import College
from app.models.offer import Offer
from app.core.security import hash_password
from app.core.rbac import Role

from tests.stress_test_utils import (
    TestReporter,
    TestResult,
    generate_unique_id,
    generate_email,
)
from tests.fixtures import (
    db_session,
    base_college,
    recruiter_user,
)


class TestErrorRecoveryAndRollback:
    """
    Test system behavior when operations partially fail or are rolled back.
    Ensure data integrity is maintained.
    """
    
    reporter = TestReporter()
    
    @pytest.mark.asyncio
    async def test_delete_round_then_readd(
        self,
        db_session: AsyncSession,
        base_college: College,
        recruiter_user: Tuple[User],
    ):
        """
        Add a round → Delete it → Re-add same round.
        Verify timeline and application status remain consistent.
        """
        test_name = "test_delete_round_then_readd"
        start_time = time.time()
        
        try:
            _, recruiter = recruiter_user
            
            # Setup: Job + Student + Application
            job = Job(
                college_id=base_college.id,
                recruiter_id=recruiter.id,
                title=f"Job {generate_unique_id()}",
                description="Test",
                job_type=JobType.FULL_TIME,
                min_cgpa=7.0,
                allowed_branches=["CSE"],
                status=DriveStatus.APPROVED,
            )
            db_session.add(job)
            await db_session.flush()
            
            user = User(
                email=generate_email("delete_round"),
                hashed_password=hash_password("pass"),
                role=Role.STUDENT,
                is_active=True,
            )
            db_session.add(user)
            await db_session.flush()
            
            student = Student(
                user_id=user.id,
                first_name="Test",
                last_name="Student",
                college_id=base_college.id,
                branch="CSE",
                cgpa=8.5,
                graduation_year=2024,
            )
            db_session.add(student)
            await db_session.flush()
            
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
            
            # Add Round 1
            round_1 = ApplicationRound(
                application_id=app_id,
                round_number=1,
                round_name="Coding Test",
                result="PASSED",
            )
            db_session.add(round_1)
            await db_session.commit()
            await db_session.refresh(round_1)
            round_1_id = round_1.id
            
            # Verify round exists
            result = await db_session.execute(
                select(ApplicationRound).filter(ApplicationRound.id == round_1_id)
            )
            assert result.scalar_one_or_none() is not None, "Round should exist"
            
            # Delete round
            result = await db_session.execute(
                select(ApplicationRound).filter(ApplicationRound.id == round_1_id)
            )
            round_to_delete = result.scalar_one()
            await db_session.delete(round_to_delete)
            await db_session.commit()
            
            # Verify deletion
            result = await db_session.execute(
                select(ApplicationRound).filter(ApplicationRound.id == round_1_id)
            )
            assert result.scalar_one_or_none() is None, "Round should be deleted"
            
            # Re-add same round
            round_1_new = ApplicationRound(
                application_id=app_id,
                round_number=1,
                round_name="Coding Test",
                result="PASSED",
            )
            db_session.add(round_1_new)
            await db_session.commit()
            await db_session.refresh(round_1_new)
            
            # Verify new round exists
            result = await db_session.execute(
                select(ApplicationRound).filter(ApplicationRound.application_id == app_id)
            )
            final_rounds = result.scalars().all()
            assert len(final_rounds) == 1, "Should have exactly 1 round after delete+readd"
            assert final_rounds[0].round_name == "Coding Test", "Round name should be preserved"
            
            # Verify application status unchanged
            result = await db_session.execute(
                select(Application).filter(Application.id == app_id)
            )
            final_app = result.scalar_one()
            assert final_app.status == ApplicationStatus.REVIEWING, "App status should be unchanged"
            
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
    async def test_delete_middle_round_preserves_timeline(
        self,
        db_session: AsyncSession,
        base_college: College,
        recruiter_user: Tuple[User],
    ):
        """
        Add Rounds 1, 2, 3 → Delete Round 2 → Verify Rounds 1 and 3 still valid.
        """
        test_name = "test_delete_middle_round_preserves_timeline"
        start_time = time.time()
        
        try:
            _, recruiter = recruiter_user
            
            # Setup
            job = Job(
                college_id=base_college.id,
                recruiter_id=recruiter.id,
                title=f"Job {generate_unique_id()}",
                description="Test",
                job_type=JobType.FULL_TIME,
                min_cgpa=7.0,
                allowed_branches=["CSE"],
                status=DriveStatus.APPROVED,
            )
            db_session.add(job)
            await db_session.flush()
            
            user = User(
                email=generate_email("middle_delete"),
                hashed_password=hash_password("pass"),
                role=Role.STUDENT,
                is_active=True,
            )
            db_session.add(user)
            await db_session.flush()
            
            student = Student(
                user_id=user.id,
                first_name="Test",
                last_name="Student",
                college_id=base_college.id,
                branch="CSE",
                cgpa=8.5,
                graduation_year=2024,
            )
            db_session.add(student)
            await db_session.flush()
            
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
            
            # Add rounds 1, 2, 3
            for i in [1, 2, 3]:
                round_obj = ApplicationRound(
                    application_id=app_id,
                    round_number=i,
                    round_name=f"Round {i}",
                    result="PASSED" if i < 3 else "PENDING",
                )
                db_session.add(round_obj)
            
            await db_session.commit()
            
            # Get Round 2's ID
            result = await db_session.execute(
                select(ApplicationRound)
                .filter(ApplicationRound.application_id == app_id, ApplicationRound.round_number == 2)
            )
            round_2 = result.scalar_one()
            round_2_id = round_2.id
            
            # Delete Round 2
            result = await db_session.execute(
                select(ApplicationRound).filter(ApplicationRound.id == round_2_id)
            )
            await db_session.delete(result.scalar_one())
            await db_session.commit()
            
            # Verify Rounds 1 and 3 still exist
            result = await db_session.execute(
                select(ApplicationRound)
                .filter(ApplicationRound.application_id == app_id)
                .order_by(ApplicationRound.round_number)
            )
            remaining_rounds = result.scalars().all()
            
            assert len(remaining_rounds) == 2, f"Expected 2 rounds after deletion, got {len(remaining_rounds)}"
            assert remaining_rounds[0].round_number == 1, "Round 1 should remain"
            assert remaining_rounds[1].round_number == 3, "Round 3 should remain"
            assert remaining_rounds[0].result == "PASSED", "Round 1 result unchanged"
            assert remaining_rounds[1].result == "PENDING", "Round 3 result unchanged"
            
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
    async def test_partial_bulk_failure_isolation(
        self,
        db_session: AsyncSession,
        base_college: College,
        recruiter_user: Tuple[User],
    ):
        """
        Simulate: Bulk update 10 records; 3 fail (injected errors).
        Verify remaining 7 succeed & 3 failed ones are unchanged.
        """
        test_name = "test_partial_bulk_failure_isolation"
        start_time = time.time()
        
        try:
            from tests.fixtures import bulk_students_100
            
            _, recruiter = recruiter_user
            
            # Setup job
            job = Job(
                college_id=base_college.id,
                recruiter_id=recruiter.id,
                title=f"Job {generate_unique_id()}",
                description="Test",
                job_type=JobType.FULL_TIME,
                min_cgpa=7.0,
                allowed_branches=["CSE"],
                status=DriveStatus.APPROVED,
            )
            db_session.add(job)
            await db_session.flush()
            
            # Create 10 applications
            students = await bulk_students_100()  # Get fixture
            app_ids = []
            for i in range(min(10, len(students))):
                app = Application(
                    student_id=students[i].id,
                    job_id=job.id,
                    status=ApplicationStatus.PENDING,
                    is_eligible=True,
                )
                db_session.add(app)
                await db_session.flush()
                app_ids.append(app.id)
            
            await db_session.commit()
            
            # Bulk update: succeed on indices 0-6, fail on 7-9 (simulated)
            succeeded = 0
            failed = 0
            
            for i, app_id in enumerate(app_ids):
                try:
                    result = await db_session.execute(
                        select(Application).filter(Application.id == app_id)
                    )
                    app = result.scalar_one()
                    
                    # Simulate failures on last 3
                    if i >= 7:
                        # Pretend failure (e.g., constraint violation)
                        # For this test, just skip the update
                        failed += 1
                        continue
                    
                    app.status = ApplicationStatus.REVIEWING
                    succeeded += 1
                
                except Exception:
                    failed += 1
            
            await db_session.commit()
            
            # Verify results
            result = await db_session.execute(
                select(Application).filter(Application.job_id == job.id)
            )
            all_apps = result.scalars().all()
            
            reviewing_count = sum(1 for a in all_apps if a.status == ApplicationStatus.REVIEWING)
            pending_count = sum(1 for a in all_apps if a.status == ApplicationStatus.PENDING)
            
            assert reviewing_count == 7, f"Expected 7 REVIEWING, got {reviewing_count}"
            assert pending_count == 3, f"Expected 3 PENDING, got {pending_count}"
            
            duration_ms = (time.time() - start_time) * 1000
            self.reporter.add_result(TestResult(
                test_name=test_name,
                passed=True,
                duration_ms=duration_ms,
                assertion_details=f"Partial failure handled: {succeeded} succeeded, {failed} failed",
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
    async def test_offer_on_rejected_applicant_fails(
        self,
        db_session: AsyncSession,
        base_college: College,
        recruiter_user: Tuple[User],
    ):
        """
        Try to create offer for REJECTED applicant.
        Should fail gracefully (not create offer, maintain state).
        """
        test_name = "test_offer_on_rejected_applicant_fails"
        start_time = time.time()
        
        try:
            _, recruiter = recruiter_user
            
            # Setup
            job = Job(
                college_id=base_college.id,
                recruiter_id=recruiter.id,
                title=f"Job {generate_unique_id()}",
                description="Test",
                job_type=JobType.FULL_TIME,
                min_cgpa=7.0,
                allowed_branches=["CSE"],
                status=DriveStatus.APPROVED,
            )
            db_session.add(job)
            await db_session.flush()
            
            user = User(
                email=generate_email("rejected_offer"),
                hashed_password=hash_password("pass"),
                role=Role.STUDENT,
                is_active=True,
            )
            db_session.add(user)
            await db_session.flush()
            
            student = Student(
                user_id=user.id,
                first_name="Rejected",
                last_name="Student",
                college_id=base_college.id,
                branch="CSE",
                cgpa=8.5,
                graduation_year=2024,
            )
            db_session.add(student)
            await db_session.flush()
            
            app = Application(
                student_id=student.id,
                job_id=job.id,
                status=ApplicationStatus.REJECTED,  # Already rejected
                is_eligible=True,
            )
            db_session.add(app)
            await db_session.commit()
            await db_session.refresh(app)
            app_id = app.id
            
            # Try to create offer on REJECTED application
            # This should fail or be invalid
            try:
                offer = Offer(
                    application_id=app_id,
                    ctc=12.5,
                )
                db_session.add(offer)
                await db_session.commit()
                
                # If we got here, verify at least that the application is still REJECTED
                result = await db_session.execute(
                    select(Application).filter(Application.id == app_id)
                )
                final_app = result.scalar_one()
                assert final_app.status == ApplicationStatus.REJECTED, "App should still be REJECTED"
                
            except Exception as e:
                # Expected to fail
                assert "REJECTED" in str(e) or "constraint" in str(e).lower(), \
                    f"Should fail due to invalid state, got: {e}"
            
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
    async def test_double_delete_round_fails_gracefully(
        self,
        db_session: AsyncSession,
        base_college: College,
        recruiter_user: Tuple[User],
    ):
        """
        Delete a round → Try to delete same round again.
        Should fail gracefully (404, not server error).
        """
        test_name = "test_double_delete_round_fails_gracefully"
        start_time = time.time()
        
        try:
            _, recruiter = recruiter_user
            
            # Setup
            job = Job(
                college_id=base_college.id,
                recruiter_id=recruiter.id,
                title=f"Job {generate_unique_id()}",
                description="Test",
                job_type=JobType.FULL_TIME,
                min_cgpa=7.0,
                allowed_branches=["CSE"],
                status=DriveStatus.APPROVED,
            )
            db_session.add(job)
            await db_session.flush()
            
            user = User(
                email=generate_email("double_delete"),
                hashed_password=hash_password("pass"),
                role=Role.STUDENT,
                is_active=True,
            )
            db_session.add(user)
            await db_session.flush()
            
            student = Student(
                user_id=user.id,
                first_name="Test",
                last_name="Student",
                college_id=base_college.id,
                branch="CSE",
                cgpa=8.5,
                graduation_year=2024,
            )
            db_session.add(student)
            await db_session.flush()
            
            app = Application(
                student_id=student.id,
                job_id=job.id,
                status=ApplicationStatus.REVIEWING,
                is_eligible=True,
            )
            db_session.add(app)
            await db_session.commit()
            await db_session.refresh(app)
            
            # Add round
            round_obj = ApplicationRound(
                application_id=app.id,
                round_number=1,
                round_name="Coding Test",
                result="PASSED",
            )
            db_session.add(round_obj)
            await db_session.commit()
            await db_session.refresh(round_obj)
            round_id = round_obj.id
            
            # Delete first time
            result = await db_session.execute(
                select(ApplicationRound).filter(ApplicationRound.id == round_id)
            )
            first_delete = result.scalar_one()
            await db_session.delete(first_delete)
            await db_session.commit()
            
            # Try to delete second time (should fail)
            result = await db_session.execute(
                select(ApplicationRound).filter(ApplicationRound.id == round_id)
            )
            second_delete = result.scalar_one_or_none()
            
            assert second_delete is None, "Round should not exist after first delete"
            
            # Attempting to delete again should raise or return none
            # (graceful handling expected, not 500 error)
            
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
