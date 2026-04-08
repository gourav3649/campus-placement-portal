"""
Pytest fixtures for stress testing: database setup, async client, test data generation.
"""

import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, List, Tuple
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.database import AsyncSessionLocal, Base, get_db
from app.models.user import User
from app.models.college import College
from app.models.recruiter import Recruiter
from app.models.student import Student
from app.models.job import Job, DriveStatus, JobType
from app.models.application import Application
from app.core.security import hash_password
from app.core.rbac import Role
from app.core.config import get_settings

from tests.stress_test_utils import (
    generate_unique_id,
    generate_email,
    generate_student_data,
    generate_job_data,
    generate_bulk_students,
)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide a fresh async database session for each test.
    Rolls back changes after test to maintain isolation.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            # Rollback to isolate tests
            await session.rollback()


@pytest_asyncio.fixture
async def base_college(db_session: AsyncSession) -> College:
    """Create a base test college."""
    college = College(
        name=f"Test College {generate_unique_id()}",
        location="Test City",
        website="example.com"
    )
    db_session.add(college)
    await db_session.commit()
    await db_session.refresh(college)
    return college


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create an admin user."""
    admin = User(
        email=generate_email("admin"),
        hashed_password=hash_password("pass"),
        role=Role.ADMIN,
        is_active=True,
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest_asyncio.fixture
async def officer_user(db_session: AsyncSession, base_college: College) -> Tuple[User, Recruiter]:
    """Create a placement officer user + profile."""
    officer_user_obj = User(
        email=generate_email("officer"),
        hashed_password=hash_password("pass"),
        role=Role.PLACEMENT_OFFICER,
        is_active=True,
    )
    db_session.add(officer_user_obj)
    await db_session.flush()
    
    officer_profile = Recruiter(  # Actually, this should be PlacementOfficer, not Recruiter
        user_id=officer_user_obj.id,
        name="Test Officer",
        email=officer_user_obj.email,
        college_id=base_college.id,
        department="Placement",
    )
    db_session.add(officer_profile)
    await db_session.commit()
    await db_session.refresh(officer_user_obj)
    
    return officer_user_obj, officer_profile


@pytest_asyncio.fixture
async def recruiter_user(db_session: AsyncSession) -> Tuple[User, Recruiter]:
    """Create a verified recruiter user + profile."""
    recruiter_user_obj = User(
        email=generate_email("recruiter"),
        hashed_password=hash_password("pass"),
        role=Role.RECRUITER,
        is_active=True,
    )
    db_session.add(recruiter_user_obj)
    await db_session.flush()
    
    recruiter_profile = Recruiter(
        user_id=recruiter_user_obj.id,
        name="Test Recruiter",
        email=recruiter_user_obj.email,
        company_name="Test Company",
        is_verified=True,  # Pre-verified for testing
    )
    db_session.add(recruiter_profile)
    await db_session.commit()
    await db_session.refresh(recruiter_user_obj)
    
    return recruiter_user_obj, recruiter_profile


@pytest_asyncio.fixture
async def test_job(
    db_session: AsyncSession,
    base_college: College,
    recruiter_user: Tuple[User, Recruiter],
) -> Job:
    """Create a single approved test job."""
    _, recruiter_profile = recruiter_user
    
    job = Job(
        college_id=base_college.id,
        recruiter_id=recruiter_profile.id,
        title=f"Test Job {generate_unique_id()}",
        description="Test job for stress testing",
        job_type=JobType.FULL_TIME,
        min_cgpa=7.0,
        allowed_branches=["CSE", "IT"],
        max_backlogs=0,
        status=DriveStatus.APPROVED,
        deadline=datetime.utcnow() + timedelta(days=7),
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)
    return job


@pytest_asyncio.fixture
async def student_user(db_session: AsyncSession, base_college: College) -> Tuple[User, Student]:
    """Create a single eligible student."""
    student_user_obj = User(
        email=generate_email("student"),
        hashed_password=hash_password("pass"),
        role=Role.STUDENT,
        is_active=True,
    )
    db_session.add(student_user_obj)
    await db_session.flush()
    
    student_profile = Student(
        user_id=student_user_obj.id,
        first_name="Test",
        last_name="Student",
        college_id=base_college.id,
        branch="CSE",
        cgpa=8.5,
        graduation_year=2024,
        has_backlogs=False,
    )
    db_session.add(student_profile)
    await db_session.commit()
    await db_session.refresh(student_user_obj)
    
    return student_user_obj, student_profile


@pytest_asyncio.fixture
async def bulk_students_100(
    db_session: AsyncSession,
    base_college: College,
) -> List[Student]:
    """Generate 100 students with varying CGPA/branches for scale testing."""
    return await generate_bulk_students(
        db_session,
        college_id=base_college.id,
        count=100,
        cgpa_distribution=(6.0, 9.5)
    )


@pytest_asyncio.fixture
async def bulk_students_300(
    db_session: AsyncSession,
    base_college: College,
) -> List[Student]:
    """Generate 300 students with varying CGPA/branches for scale testing."""
    return await generate_bulk_students(
        db_session,
        college_id=base_college.id,
        count=300,
        cgpa_distribution=(6.0, 9.5)
    )


@pytest_asyncio.fixture
async def multiple_jobs(
    db_session: AsyncSession,
    base_college: College,
    recruiter_user: Tuple[User, Recruiter],
    count: int = 10,
) -> List[Job]:
    """Create multiple approved jobs for stress testing."""
    _, recruiter_profile = recruiter_user
    
    jobs = []
    for i in range(count):
        job = Job(
            college_id=base_college.id,
            recruiter_id=recruiter_profile.id,
            title=f"Test Job {i} {generate_unique_id()}",
            description="Test job for stress testing",
            job_type=JobType.FULL_TIME,
            min_cgpa=7.0,
            allowed_branches=["CSE", "IT"],
            max_backlogs=0,
            status=DriveStatus.APPROVED,
            deadline=datetime.utcnow() + timedelta(days=7),
        )
        db_session.add(job)
        await db_session.flush()
        jobs.append(job)
    
    await db_session.commit()
    for job in jobs:
        await db_session.refresh(job)
    
    return jobs


@pytest_asyncio.fixture
async def event_loop():
    """
    Create event loop with function scope to allow running async tests.
    """
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ────────────────────────────────────────────────────────────────────────────
# OVERRIDE FastAPI dependency for testing
# ────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def override_get_db(db_session: AsyncSession):
    """Override FastAPI's get_db dependency for testing."""
    async def _override_get_db():
        yield db_session
    return _override_get_db
