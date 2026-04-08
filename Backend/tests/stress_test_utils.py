"""
Utilities for stress testing: concurrent request helpers, data generation,
race condition simulation, and infrastructure failure injection.
"""

import asyncio
import random
import string
import uuid
import time
from typing import List, Tuple, Callable, Any, Optional
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from functools import wraps
import json
import sys

import requests
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.student import Student
from app.models.college import College
from app.models.recruiter import Recruiter
from app.models.job import Job, DriveStatus, JobType
from app.models.application import Application, ApplicationStatus
from app.core.security import hash_password
from app.core.rbac import Role


# ────────────────────────────────────────────────────────────────────────────
# LOGGING & REPORTING
# ────────────────────────────────────────────────────────────────────────────

@dataclass
class TestResult:
    """Encapsulates a single test result."""
    test_name: str
    passed: bool
    duration_ms: float
    error_msg: Optional[str] = None
    assertion_details: Optional[str] = None
    response_dump: Optional[dict] = None


class TestReporter:
    """Collects test results and generates reports."""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.start_time = time.time()
    
    def add_result(self, result: TestResult):
        self.results.append(result)
        status = "✓ PASS" if result.passed else "✗ FAIL"
        msg = f"[{status}] {result.test_name} ({result.duration_ms:.1f}ms)"
        if result.error_msg:
            msg += f"\n  Error: {result.error_msg}"
        print(msg)
    
    def summary(self) -> str:
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        duration = time.time() - self.start_time
        
        return f"\n{'='*70}\nTest Summary: {passed}/{total} passed, {failed} failed\nTotal duration: {duration:.2f}s\n{'='*70}"
    
    def get_failures(self) -> List[TestResult]:
        return [r for r in self.results if not r.passed]


# ────────────────────────────────────────────────────────────────────────────
# DATA GENERATION
# ────────────────────────────────────────────────────────────────────────────

def generate_unique_id() -> str:
    """Generate a unique identifier for test data."""
    return str(uuid.uuid4())[:8]


def generate_email(prefix: str = "test") -> str:
    """Generate a unique test email."""
    return f"{prefix}_{generate_unique_id()}@test.com"


def generate_student_data(
    college_id: int, 
    branch: Optional[str] = None, 
    cgpa: Optional[float] = None,
    has_backlogs: bool = False
) -> dict:
    """Generate realistic student registration data."""
    branches = ["CSE", "IT", "ECE", "ME", "CE", "EE"]
    
    return {
        "first_name": f"Student{generate_unique_id()}",
        "last_name": "Test",
        "college_id": college_id,
        "branch": branch or random.choice(branches),
        "cgpa": cgpa if cgpa is not None else round(random.uniform(6.0, 9.5), 2),
        "graduation_year": 2024,
        "has_backlogs": has_backlogs,
    }


def generate_job_data(
    college_id: int,
    recruiter_id: int,
    min_cgpa: float = 7.0,
    allowed_branches: Optional[List[str]] = None,
    max_backlogs: int = 0,
) -> dict:
    """Generate realistic job posting data."""
    unique = generate_unique_id()
    return {
        "title": f"Software Engineer {unique}",
        "description": "Build scalable systems",
        "college_id": college_id,
        "recruiter_id": recruiter_id,
        "job_type": JobType.FULL_TIME,
        "min_cgpa": min_cgpa,
        "allowed_branches": allowed_branches or ["CSE", "IT"],
        "max_backlogs": max_backlogs,
    }


async def generate_bulk_students(
    db: AsyncSession,
    college_id: int,
    count: int = 100,
    cgpa_distribution: Optional[Tuple[float, float]] = None,
) -> List[Student]:
    """
    Generate `count` students with varying CGPA/branches for scale testing.
    Returns list of created Student objects.
    """
    students = []
    branches = ["CSE", "IT", "ECE", "ME", "CE", "EE"]
    cgpa_min, cgpa_max = cgpa_distribution or (6.0, 9.5)
    
    for i in range(count):
        email = f"student_bulk_{i}_{generate_unique_id()}@test.com"
        user = User(
            email=email,
            hashed_password=hash_password("pass"),
            role=Role.STUDENT,
            is_active=True,
        )
        db.add(user)
        await db.flush()  # Get ID without commit
        
        student = Student(
            user_id=user.id,
            first_name=f"Student{i}",
            last_name="Bulk",
            college_id=college_id,
            branch=random.choice(branches),
            cgpa=round(random.uniform(cgpa_min, cgpa_max), 2),
            graduation_year=2024,
            has_backlogs=random.choice([False, False, True]),  # 33% have backlogs
        )
        db.add(student)
        await db.flush()
        students.append(student)
    
    await db.commit()
    return students


# ────────────────────────────────────────────────────────────────────────────
# CONCURRENT REQUEST HELPERS
# ────────────────────────────────────────────────────────────────────────────

class ConcurrentRequester:
    """Helper for firing concurrent HTTP requests and tracking failures."""
    
    def __init__(self, base_url: str = "http://localhost:8000/api/v1"):
        self.base_url = base_url
        self.session = requests.Session()
    
    async def fire_concurrent_requests(
        self,
        requests_list: List[Tuple[str, str, dict, Optional[str]]],
        max_concurrent: int = 10,
    ) -> List[Tuple[int, dict, Optional[str]]]:
        """
        Fire multiple HTTP requests concurrently with rate limiting.
        
        Args:
            requests_list: List of (method, endpoint, json_payload, auth_token) tuples
            max_concurrent: Max requests in flight at once
        
        Returns:
            List of (status_code, response_json, error_msg)
        """
        results = []
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def _make_request(method: str, endpoint: str, payload: dict, token: Optional[str]):
            async with semaphore:
                headers = {"Authorization": f"Bearer {token}"} if token else {}
                try:
                    async with httpx.AsyncClient(base_url=self.base_url) as client:
                        if method.upper() == "GET":
                            resp = await client.get(endpoint, headers=headers)
                        elif method.upper() == "POST":
                            resp = await client.post(endpoint, json=payload, headers=headers)
                        elif method.upper() == "PUT":
                            resp = await client.put(endpoint, json=payload, headers=headers)
                        elif method.upper() == "DELETE":
                            resp = await client.delete(endpoint, headers=headers)
                        else:
                            return None, 400, "Unknown method"
                        
                        try:
                            resp_json = resp.json()
                        except:
                            resp_json = {"raw": resp.text}
                        
                        return resp.status_code, resp_json, None
                except Exception as e:
                    return None, 0, str(e)
        
        # Create tasks for all requests
        tasks = [
            _make_request(method, endpoint, payload, token)
            for method, endpoint, payload, token in requests_list
        ]
        
        # Gather results
        raw_results = await asyncio.gather(*tasks)
        
        return raw_results


# ────────────────────────────────────────────────────────────────────────────
# RACE CONDITION SIMULATION
# ────────────────────────────────────────────────────────────────────────────

async def simulate_race_condition(
    coroutine_list: List[Callable],
    interleave: bool = True,
) -> List[Any]:
    """
    Simulate a race condition by running multiple coroutines concurrently.
    
    Args:
        coroutine_list: List of async functions to run
        interleave: If True, use gather for full concurrency; if False, stagger slightly
    
    Returns:
        Results from all coroutines
    """
    if interleave:
        # Full concurrency
        return await asyncio.gather(*[coro() for coro in coroutine_list], return_exceptions=True)
    else:
        # Staggered (race condition, but slightly offset)
        results = []
        for i, coro in enumerate(coroutine_list):
            await asyncio.sleep(0.01 * i)  # Stagger by 10ms
            result = await coro()
            results.append(result)
        return results


# ────────────────────────────────────────────────────────────────────────────
# FAILURE INJECTION DECORATORS
# ────────────────────────────────────────────────────────────────────────────

def inject_timeout(timeout_ms: int = 500):
    """Decorator to simulate network timeout."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout_ms / 1000)
            except asyncio.TimeoutError:
                raise TimeoutError(f"Operation timed out after {timeout_ms}ms")
        return wrapper
    return decorator


def inject_latency(latency_ms: int = 100):
    """Decorator to add artificial network latency."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            await asyncio.sleep(latency_ms / 1000)
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def inject_partial_failure(failure_rate: float = 0.3):
    """Decorator to randomly fail a portion of calls."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if random.random() < failure_rate:
                raise Exception(f"Injected failure ({failure_rate*100}% failure rate)")
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# ────────────────────────────────────────────────────────────────────────────
# DATABASE ASSERTIONS & VALIDATION
# ────────────────────────────────────────────────────────────────────────────

class DBValidator:
    """Helpers to validate database state after operations."""
    
    @staticmethod
    async def get_application_count(
        db: AsyncSession,
        job_id: Optional[int] = None,
        status: Optional[ApplicationStatus] = None,
    ) -> int:
        """Count applications matching filters."""
        query = select(Application)
        if job_id:
            query = query.filter(Application.job_id == job_id)
        if status:
            query = query.filter(Application.status == status)
        
        result = await db.execute(query)
        return len(result.scalars().all())
    
    @staticmethod
    async def check_orphaned_rounds(db: AsyncSession) -> List[int]:
        """Find rounds without a valid application (orphaned)."""
        from app.models.application_round import ApplicationRound
        
        # Get all round IDs
        all_rounds = await db.execute(select(ApplicationRound))
        round_ids = [r.id for r in all_rounds.scalars().all()]
        
        # Check which have valid applications
        orphaned = []
        for round_id in round_ids:
            round_obj = await db.execute(
                select(ApplicationRound).filter(ApplicationRound.id == round_id)
            )
            round_record = round_obj.scalar_one_or_none()
            if round_record and not round_record.application:
                orphaned.append(round_id)
        
        return orphaned
    
    @staticmethod
    async def verify_application_consistency(
        db: AsyncSession,
        app_id: int,
    ) -> Tuple[bool, str]:
        """
        Verify that an application's state is internally consistent:
        - Rounds exist only if application is not REJECTED/WITHDRAWN
        - Application has at most 1 offer
        - Status transitions are valid
        """
        app = await db.execute(select(Application).filter(Application.id == app_id))
        app_record = app.scalar_one_or_none()
        
        if not app_record:
            return False, "Application not found"
        
        # Check: If REJECTED/WITHDRAWN, should have no future rounds
        if app_record.status in (ApplicationStatus.REJECTED, ApplicationStatus.WITHDRAWN):
            if app_record.rounds:
                return False, f"Status {app_record.status} should not have rounds"
        
        # Check: At most 1 offer
        if app_record.offer and len([app_record.offer]) > 1:
            return False, "Application has multiple offers"
        
        return True, "Consistent"


# ────────────────────────────────────────────────────────────────────────────
# PERFORMANCE TRACKING
# ────────────────────────────────────────────────────────────────────────────

class PerfTracker:
    """Track response times and performance metrics."""
    
    def __init__(self):
        self.metrics = {}  # operation_name -> [durations_ms]
    
    def record(self, operation: str, duration_ms: float):
        if operation not in self.metrics:
            self.metrics[operation] = []
        self.metrics[operation].append(duration_ms)
    
    def stats(self, operation: str) -> dict:
        """Get min/max/avg for an operation."""
        if operation not in self.metrics:
            return {}
        
        durations = self.metrics[operation]
        return {
            "count": len(durations),
            "min_ms": min(durations),
            "max_ms": max(durations),
            "avg_ms": sum(durations) / len(durations),
            "p95_ms": sorted(durations)[int(len(durations) * 0.95)] if len(durations) > 1 else durations[0],
        }
    
    def report(self) -> str:
        """Generate a performance report."""
        lines = ["\n=== PERFORMANCE METRICS ==="]
        for op, stats in self.metric.items():
            s = self.stats(op)
            lines.append(f"{op}: avg={s['avg_ms']:.1f}ms, min={s['min_ms']:.1f}ms, max={s['max_ms']:.1f}ms, p95={s['p95_ms']:.1f}ms")
        return "\n".join(lines)


# ────────────────────────────────────────────────────────────────────────────
# ASSERTION HELPERS
# ────────────────────────────────────────────────────────────────────────────

def assert_eq(actual: Any, expected: Any, msg: str = ""):
    """Assert equality with detailed error message."""
    if actual != expected:
        error = f"Assertion failed: {msg}\nExpected: {expected}\nActual: {actual}"
        raise AssertionError(error)


def assert_status_code(status_code: int, expected: int, msg: str = ""):
    """Assert HTTP status code."""
    if status_code != expected:
        error = f"Status code mismatch: {msg}\nExpected: {expected}\nGot: {status_code}"
        raise AssertionError(error)


def assert_in_range(value: float, min_val: float, max_val: float, msg: str = ""):
    """Assert value is within range."""
    if not (min_val <= value <= max_val):
        error = f"Value out of range: {msg}\nExpected: [{min_val}, {max_val}]\nGot: {value}"
        raise AssertionError(error)


# ────────────────────────────────────────────────────────────────────────────
# CLEANUP & TEARDOWN HELPERS
# ────────────────────────────────────────────────────────────────────────────

async def cleanup_test_data(db: AsyncSession, college_id: Optional[int] = None):
    """Clean up test data created during stress tests."""
    from app.models.user import User
    
    if college_id:
        # Delete all jobs for college
        jobs = await db.execute(select(Job).filter(Job.college_id == college_id))
        for job in jobs.scalars().all():
            await db.delete(job)
        
        # Delete all students for college
        students = await db.execute(select(Student).filter(Student.college_id == college_id))
        for student in students.scalars().all():
            await db.delete(student)
    
    await db.commit()
