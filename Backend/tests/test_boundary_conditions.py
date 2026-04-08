"""
Phase 2.3: Boundary Condition & Edge Case Tests.
Tests system behavior at limits: CGPA thresholds, deadlines, branch mismatches, round ordering, etc.
"""

import pytest
import time
from typing import Tuple, List
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.student import Student
from app.models.job import Job, JobType, DriveStatus
from app.models.application import Application, ApplicationStatus
from app.models.application_round import ApplicationRound
from app.models.user import User
from app.models.college import College
from app.core.security import hash_password
from app.core.rbac import Role
from app.services.eligibility import check_eligibility

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


class TestBoundaryConditions:
    """
    Test behavior at system boundaries and edge cases.
    """
    
    reporter = TestReporter()
    
    @pytest.mark.asyncio
    async def test_cgpa_exactly_at_threshold_passes(
        self,
        db_session: AsyncSession,
        base_college: College,
        recruiter_user: Tuple[User],
    ):
        """
        Student with CGPA exactly equal to job's min_cgpa should be eligible.
        """
        test_name = "test_cgpa_exactly_at_threshold_passes"
        start_time = time.time()
        
        try:
            _, recruiter = recruiter_user
            
            # Create job with min_cgpa = 7.5
            job = Job(
                college_id=base_college.id,
                recruiter_id=recruiter.id,
                title=f"Job {generate_unique_id()}",
                description="Test job",
                job_type=JobType.FULL_TIME,
                min_cgpa=7.5,
                allowed_branches=["CSE"],
                status=DriveStatus.APPROVED,
            )
            db_session.add(job)
            await db_session.flush()
            
            # Create student with CGPA = 7.5 (exactly at threshold)
            user = User(
                email=generate_email("cgpa_boundary"),
                hashed_password=hash_password("pass"),
                role=Role.STUDENT,
                is_active=True,
            )
            db_session.add(user)
            await db_session.flush()
            
            student = Student(
                user_id=user.id,
                first_name="Boundary",
                last_name="Student",
                college_id=base_college.id,
                branch="CSE",
                cgpa=7.5,  # Exactly at threshold
                graduation_year=2024,
                has_backlogs=False,
            )
            db_session.add(student)
            await db_session.commit()
            
            # Check eligibility
            is_eligible, reasons = check_eligibility(student, job)
            
            assert is_eligible is True, f"CGPA 7.5 should be eligible for min_cgpa 7.5: {reasons}"
            
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
    async def test_cgpa_just_below_threshold_fails(
        self,
        db_session: AsyncSession,
        base_college: College,
        recruiter_user: Tuple[User],
    ):
        """
        Student with CGPA just below threshold should fail eligibility.
        """
        test_name = "test_cgpa_just_below_threshold_fails"
        start_time = time.time()
        
        try:
            _, recruiter = recruiter_user
            
            job = Job(
                college_id=base_college.id,
                recruiter_id=recruiter.id,
                title=f"Job {generate_unique_id()}",
                description="Test job",
                job_type=JobType.FULL_TIME,
                min_cgpa=7.5,
                allowed_branches=["CSE"],
                status=DriveStatus.APPROVED,
            )
            db_session.add(job)
            await db_session.flush()
            
            user = User(
                email=generate_email("cgpa_below"),
                hashed_password=hash_password("pass"),
                role=Role.STUDENT,
                is_active=True,
            )
            db_session.add(user)
            await db_session.flush()
            
            student = Student(
                user_id=user.id,
                first_name="Below",
                last_name="Threshold",
                college_id=base_college.id,
                branch="CSE",
                cgpa=7.49,  # Just below threshold
                graduation_year=2024,
                has_backlogs=False,
            )
            db_session.add(student)
            await db_session.commit()
            
            is_eligible, reasons = check_eligibility(student, job)
            
            assert is_eligible is False, "CGPA 7.49 should fail for min_cgpa 7.5"
            assert any("CGPA" in r for r in reasons), f"Reason should mention CGPA: {reasons}"
            
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
    async def test_branch_not_in_allowed_list_fails(
        self,
        db_session: AsyncSession,
        base_college: College,
        recruiter_user: Tuple[User],
    ):
        """
        Student from branch not in allowed_branches should fail.
        """
        test_name = "test_branch_not_in_allowed_list_fails"
        start_time = time.time()
        
        try:
            _, recruiter = recruiter_user
            
            job = Job(
                college_id=base_college.id,
                recruiter_id=recruiter.id,
                title=f"Job {generate_unique_id()}",
                description="Test job",
                job_type=JobType.FULL_TIME,
                min_cgpa=7.0,
                allowed_branches=["CSE", "IT"],  # Only CSE and IT
                status=DriveStatus.APPROVED,
            )
            db_session.add(job)
            await db_session.flush()
            
            user = User(
                email=generate_email("branch_mismatch"),
                hashed_password=hash_password("pass"),
                role=Role.STUDENT,
                is_active=True,
            )
            db_session.add(user)
            await db_session.flush()
            
            student = Student(
                user_id=user.id,
                first_name="ME",
                last_name="Student",
                college_id=base_college.id,
                branch="ME",  # Mechanical Engineering - not allowed
                cgpa=8.5,
                graduation_year=2024,
                has_backlogs=False,
            )
            db_session.add(student)
            await db_session.commit()
            
            is_eligible, reasons = check_eligibility(student, job)
            
            assert is_eligible is False, "ME branch should not be eligible"
            assert any("branch" in r.lower() for r in reasons), f"Reason should mention branch: {reasons}"
            
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
    async def test_backlog_zero_tolerance(
        self,
        db_session: AsyncSession,
        base_college: College,
        recruiter_user: Tuple[User],
    ):
        """
        Job with max_backlogs=0 should reject students with has_backlogs=True.
        """
        test_name = "test_backlog_zero_tolerance"
        start_time = time.time()
        
        try:
            _, recruiter = recruiter_user
            
            job = Job(
                college_id=base_college.id,
                recruiter_id=recruiter.id,
                title=f"Job {generate_unique_id()}",
                description="No backlogs job",
                job_type=JobType.FULL_TIME,
                min_cgpa=7.0,
                max_backlogs=0,  # Zero tolerance
                allowed_branches=["CSE"],
                status=DriveStatus.APPROVED,
            )
            db_session.add(job)
            await db_session.flush()
            
            # Student WITH backlogs
            user_with = User(
                email=generate_email("with_backlog"),
                hashed_password=hash_password("pass"),
                role=Role.STUDENT,
                is_active=True,
            )
            db_session.add(user_with)
            await db_session.flush()
            
            student_with = Student(
                user_id=user_with.id,
                first_name="With",
                last_name="Backlog",
                college_id=base_college.id,
                branch="CSE",
                cgpa=8.5,
                graduation_year=2024,
                has_backlogs=True,  # Has backlogs
            )
            db_session.add(student_with)
            
            # Student WITHOUT backlogs
            user_without = User(
                email=generate_email("no_backlog"),
                hashed_password=hash_password("pass"),
                role=Role.STUDENT,
                is_active=True,
            )
            db_session.add(user_without)
            await db_session.flush()
            
            student_without = Student(
                user_id=user_without.id,
                first_name="Without",
                last_name="Backlog",
                college_id=base_college.id,
                branch="CSE",
                cgpa=8.5,
                graduation_year=2024,
                has_backlogs=False,  # No backlogs
            )
            db_session.add(student_without)
            await db_session.commit()
            
            # Check eligibility
            eligible_with, reasons_with = check_eligibility(student_with, job)
            eligible_without, reasons_without = check_eligibility(student_without, job)
            
            assert eligible_with is False, "Student with backlog should fail"
            assert eligible_without is True, "Student without backlog should pass"
            
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
    async def test_application_at_deadline_edge(
        self,
        db_session: AsyncSession,
        base_college: College,
        recruiter_user: Tuple[User],
    ):
        """
        Job with deadline NOW should allow applications slightly before deadline.
        Applications after deadline should be blocked (if enforced).
        """
        test_name = "test_application_at_deadline_edge"
        start_time = time.time()
        
        try:
            _, recruiter = recruiter_user
            
            # Create job with deadline 1 hour from now
            deadline = datetime.utcnow() + timedelta(hours=1)
            job = Job(
                college_id=base_college.id,
                recruiter_id=recruiter.id,
                title=f"Job {generate_unique_id()}",
                description="Test job",
                job_type=JobType.FULL_TIME,
                min_cgpa=7.0,
                allowed_branches=["CSE"],
                deadline=deadline,
                status=DriveStatus.APPROVED,
            )
            db_session.add(job)
            await db_session.flush()
            
            user = User(
                email=generate_email("deadline_test"),
                hashed_password=hash_password("pass"),
                role=Role.STUDENT,
                is_active=True,
            )
            db_session.add(user)
            await db_session.flush()
            
            student = Student(
                user_id=user.id,
                first_name="Deadline",
                last_name="Test",
                college_id=base_college.id,
                branch="CSE",
                cgpa=8.5,
                graduation_year=2024,
            )
            db_session.add(student)
            await db_session.commit()
            
            # Create application (should be allowed since deadline hasn't passed)
            app = Application(
                student_id=student.id,
                job_id=job.id,
                status=ApplicationStatus.PENDING,
                is_eligible=True,
            )
            db_session.add(app)
            await db_session.commit()
            await db_session.refresh(app)
            
            # Verify application exists
            assert app.id > 0, "Application should be created"
            assert app.applied_at is not None, "Application should have applied_at timestamp"
            
            duration_ms = (time.time() - start_time) * 1000
            self.reporter.add_result(TestResult(
                test_name=test_name,
                passed=True,
                duration_ms=duration_ms,
                assertion_details="Application created before deadline",
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
    async def test_round_ordering_enforcement(
        self,
        db_session: AsyncSession,
        base_college: College,
        recruiter_user: Tuple[User],
    ):
        """
        Add rounds out of order (e.g., Round 3 before Round 1).
        System should either enforce ordering or allow with warning.
        """
        test_name = "test_round_ordering_enforcement"
        start_time = time.time()
        
        try:
            _, recruiter = recruiter_user
            
            # Create job and student with application
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
            
            user = User(
                email=generate_email("round_order"),
                hashed_password=hash_password("pass"),
                role=Role.STUDENT,
                is_active=True,
            )
            db_session.add(user)
            await db_session.flush()
            
            student = Student(
                user_id=user.id,
                first_name="Round",
                last_name="Test",
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
            
            # Add Round 3 (out of order)
            round_3 = ApplicationRound(
                application_id=app.id,
                round_number=3,
                round_name="Interview",
                result="PENDING",
            )
            db_session.add(round_3)
            await db_session.commit()
            
            # Add Round 1 (after Round 3)
            round_1 = ApplicationRound(
                application_id=app.id,
                round_number=1,
                round_name="Coding Test",
                result="PASSED",
            )
            db_session.add(round_1)
            await db_session.commit()
            
            # Verify both exist
            result = await db_session.execute(
                select(ApplicationRound).filter(ApplicationRound.application_id == app.id)
            )
            rounds = result.scalars().all()
            
            assert len(rounds) == 2, "Both rounds should exist"
            round_numbers = sorted([r.round_number for r in rounds])
            assert round_numbers == [1, 3], "Rounds 1 and 3 should exist (out of order is allowed)"
            
            duration_ms = (time.time() - start_time) * 1000
            self.reporter.add_result(TestResult(
                test_name=test_name,
                passed=True,
                duration_ms=duration_ms,
                assertion_details="Out-of-order rounds allowed (no strict enforcement)",
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
