"""
Infrastructure validation tests: Ensure DB connection, server readiness, and baseline metrics.
"""

import pytest
import asyncio
import time
from typing import Optional

import requests
import httpx
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession

from tests.stress_test_utils import (
    TestReporter,
    TestResult,
    assert_eq,
    PerfTracker,
)
from tests.fixtures import (
    db_session,
    base_college,
    admin_user,
    officer_user,
    recruiter_user,
    test_job,
    student_user,
)


BASE_URL = "http://localhost:8000/api/v1"
HEALTH_URL = "http://localhost:8000/health"


class TestInfrastructureSetup:
    """
    Phase 1.3: Validate that the test environment is ready for stress testing.
    Fails early if server is down, DB unreachable, or baseline performance is catastrophic.
    """
    
    @pytest.mark.asyncio
    async def test_db_connection(self, db_session: AsyncSession):
        """Verify database connection and basic query works."""
        start = time.time()
        
        # Execute a simple query
        result = await db_session.execute(text("SELECT 1"))
        count = result.scalar()
        
        duration_ms = (time.time() - start) * 1000
        
        assert count == 1, "DB query failed"
        assert duration_ms < 100, f"DB query too slow: {duration_ms}ms"
    
    @pytest.mark.asyncio
    async def test_server_health(self):
        """Check if server is running and healthy."""
        max_retries = 5
        for i in range(max_retries):
            try:
                resp = requests.get(HEALTH_URL, timeout=5)
                assert resp.status_code == 200, f"Health check failed: {resp.status_code}"
                health_data = resp.json()
                assert health_data.get("status") == "ok", "Server status not ok"
                break
            except requests.exceptions.RequestException as e:
                if i == max_retries - 1:
                    pytest.fail(f"Server is not running: {e}")
                await asyncio.sleep(1)
    
    @pytest.mark.asyncio
    async def test_db_connection_pooling(self, db_session: AsyncSession):
        """
        Verify DB connection pool can handle concurrent connections.
        Fire 10 sequential queries and ensure all succeed quickly.
        """
        perf = PerfTracker()
        
        for i in range(10):
            start = time.time()
            result = await db_session.execute(text(f"SELECT {i}"))
            val = result.scalar()
            duration_ms = (time.time() - start) * 1000
            
            perf.record("db_query", duration_ms)
            assert val == i, f"Query {i} returned wrong value"
        
        stats = perf.stats("db_query")
        assert stats["avg_ms"] < 50, f"DB queries too slow: {stats['avg_ms']}ms avg"
        assert stats["max_ms"] < 100, f"DB query spike: {stats['max_ms']}ms max"
    
    @pytest.mark.asyncio
    async def test_api_endpoint_availability(self):
        """Verify key API endpoints are responding (read-only checks)."""
        endpoints_to_check = [
            ("GET", "/jobs/all"),
            ("GET", "/colleges"),
            ("GET", "/notifications"),
        ]
        
        # Note: These require auth tokens, so expect 401 if not authenticated
        # But endpoint should respond (not 404 or 500)
        for method, endpoint in endpoints_to_check:
            try:
                if method == "GET":
                    resp = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
                else:
                    resp = requests.post(f"{BASE_URL}{endpoint}", json={}, timeout=5)
                
                # Accept 401 (auth required), 200 (ok), or 400 (bad request)
                # But fail on 404 (not found) or 500 (server error)
                assert resp.status_code not in (404, 500), \
                    f"Endpoint {method} {endpoint} returned {resp.status_code}"
            except requests.exceptions.RequestException as e:
                pytest.fail(f"Endpoint {method} {endpoint} failed: {e}")
    
    @pytest.mark.asyncio
    async def test_baseline_response_time(self):
        """
        Measure baseline response time for a simple endpoint (unauthenticated).
        Ensures server isn't already under heavy load.
        """
        perf = PerfTracker()
        
        for _ in range(5):
            start = time.time()
            try:
                resp = requests.get(HEALTH_URL, timeout=5)
                duration_ms = (time.time() - start) * 1000
                perf.record("health_check", duration_ms)
                assert resp.status_code == 200
            except Exception as e:
                pytest.fail(f"Baseline health check failed: {e}")
        
        stats = perf.stats("health_check")
        assert stats["avg_ms"] < 100, f"Baseline health check too slow: {stats['avg_ms']}ms"
    
    @pytest.mark.asyncio
    async def test_fixture_setup(
        self,
        base_college,
        admin_user,
        officer_user,
        recruiter_user,
        test_job,
        student_user,
    ):
        """
        Verify that all test fixtures created without errors.
        This ensures the test data generation pipeline works.
        """
        assert base_college.id > 0, "College not created"
        assert admin_user.id > 0, "Admin user not created"
        assert officer_user[0].id > 0, "Officer user not created"
        assert recruiter_user[0].id > 0, "Recruiter user not created"
        assert test_job.id > 0, "Test job not created"
        assert student_user[0].id > 0, "Student user not created"


class TestBaselinePerformance:
    """
    Capture baseline performance metrics for comparison during stress testing.
    """
    
    @pytest.mark.asyncio
    async def test_single_application_fetch(
        self,
        db_session: AsyncSession,
        test_job,
        student_user,
    ):
        """Measure response time for fetching a single application."""
        from app.models.application import Application
        from sqlalchemy.orm import selectinload
        
        # Create an application
        _, student = student_user
        app = Application(
            student_id=student.id,
            job_id=test_job.id,
            status="PENDING",
            is_eligible=True,
        )
        db_session.add(app)
        await db_session.commit()
        await db_session.refresh(app)
        
        # Measure fetch
        perf = PerfTracker()
        for _ in range(5):
            start = time.time()
            result = await db_session.execute(
                select(Application)
                .options(
                    selectinload(Application.student),
                    selectinload(Application.job),
                    selectinload(Application.rounds),
                )
                .filter(Application.id == app.id)
            )
            _ = result.scalar_one()
            duration_ms = (time.time() - start) * 1000
            perf.record("fetch_single_app", duration_ms)
        
        stats = perf.stats("fetch_single_app")
        print(f"\nBaseline: Single application fetch: avg={stats['avg_ms']:.2f}ms")
        
        # Should be very fast
        assert stats["avg_ms"] < 10, f"Single app fetch baseline too slow: {stats['avg_ms']}ms"
    
    @pytest.mark.asyncio
    async def test_bulk_application_fetch_variance(
        self,
        db_session: AsyncSession,
        test_job,
        bulk_students_100,
    ):
        """
        Create 10 applications and measure fetch time as we increase count.
        This shows the variance in response time with data volume.
        """
        from app.models.application import Application
        from sqlalchemy.orm import selectinload
        
        # Create applications
        for i, student in enumerate(bulk_students_100[:10]):
            app = Application(
                student_id=student.id,
                job_id=test_job.id,
                status="PENDING",
                is_eligible=True,
            )
            db_session.add(app)
        
        await db_session.commit()
        
        # Measure fetch of all 10
        perf = PerfTracker()
        for _ in range(3):
            start = time.time()
            result = await db_session.execute(
                select(Application)
                .options(
                    selectinload(Application.student),
                    selectinload(Application.job),
                    selectinload(Application.rounds),
                )
                .filter(Application.job_id == test_job.id)
            )
            _ = result.scalars().unique().all()
            duration_ms = (time.time() - start) * 1000
            perf.record("fetch_bulk_apps", duration_ms)
        
        stats = perf.stats("fetch_bulk_apps")
        print(f"\nBaseline: 10 applications fetch: avg={stats['avg_ms']:.2f}ms")
        
        # Should still be fast with proper joins
        assert stats["avg_ms"] < 50, f"Bulk app fetch baseline concerning: {stats['avg_ms']}ms"
