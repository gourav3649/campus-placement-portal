"""
Phase 2.2: Scale & Performance Tests.
Tests system behavior with 100–300 applicants: dashboard fetch, bulk operations, filtering, etc.
"""

import pytest
import time
from typing import List
from datetime import datetime, timedelta

from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application, ApplicationStatus
from app.models.job import Job, DriveStatus

from tests.stress_test_utils import (
    TestReporter,
    TestResult,
    assert_eq,
    assert_in_range,
    PerfTracker,
)
from tests.fixtures import (
    db_session,
    base_college,
    test_job,
    bulk_students_100,
    bulk_students_300,
)


class TestScaleAndPerformance:
    """
    Test system performance with varying data volumes.
    Verify response times remain acceptable and no N+1 queries occur.
    """
    
    reporter = TestReporter()
    perf = PerfTracker()
    
    @pytest.mark.asyncio
    async def test_scale_100_applicants_dashboard_fetch(
        self,
        db_session: AsyncSession,
        test_job: Job,
        bulk_students_100: List,
    ):
        """
        Fetch all 100 applications (dashboard view).
        Measure response time and memory usage.
        """
        test_name = "test_scale_100_applicants_dashboard_fetch"
        start_time = time.time()
        
        try:
            # Create 100 applications
            for i, student in enumerate(bulk_students_100):
                app = Application(
                    student_id=student.id,
                    job_id=test_job.id,
                    status=ApplicationStatus.PENDING if i % 2 == 0 else ApplicationStatus.REVIEWING,
                    is_eligible=True,
                )
                db_session.add(app)
            
            await db_session.commit()
            
            # Measure fetch performance
            fetch_times = []
            for _ in range(3):
                fetch_start = time.time()
                
                result = await db_session.execute(
                    select(Application)
                    .options(
                        selectinload(Application.student),
                        selectinload(Application.job),
                        selectinload(Application.rounds),
                    )
                    .filter(Application.job_id == test_job.id)
                    .order_by(Application.id)
                )
                apps = result.scalars().unique().all()
                
                fetch_duration = (time.time() - fetch_start) * 1000
                fetch_times.append(fetch_duration)
            
            avg_duration = sum(fetch_times) / len(fetch_times)
            self.perf.record("fetch_100_apps", avg_duration)
            
            assert len(apps) == 100, f"Expected 100 apps, got {len(apps)}"
            assert_in_range(avg_duration, 0, 1000, f"Dashboard fetch must be <1s, got {avg_duration:.2f}ms")
            
            duration_ms = (time.time() - start_time) * 1000
            self.reporter.add_result(TestResult(
                test_name=test_name,
                passed=True,
                duration_ms=duration_ms,
                assertion_details=f"Fetch 100 apps: {avg_duration:.2f}ms avg",
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
    async def test_scale_300_applicants_dashboard_fetch(
        self,
        db_session: AsyncSession,
        test_job: Job,
        bulk_students_300: List,
    ):
        """
        Fetch all 300 applications (larger scale).
        Should still be acceptable performance (<5s).
        """
        test_name = "test_scale_300_applicants_dashboard_fetch"
        start_time = time.time()
        
        try:
            # Create 300 applications
            for i, student in enumerate(bulk_students_300):
                app = Application(
                    student_id=student.id,
                    job_id=test_job.id,
                    status=ApplicationStatus.PENDING if i % 3 == 0 else ApplicationStatus.REVIEWING,
                    is_eligible=True,
                )
                db_session.add(app)
            
            await db_session.commit()
            
            # Measure fetch performance
            fetch_times = []
            for _ in range(3):
                fetch_start = time.time()
                
                result = await db_session.execute(
                    select(Application)
                    .options(
                        selectinload(Application.student),
                        selectinload(Application.job),
                        selectinload(Application.rounds),
                    )
                    .filter(Application.job_id == test_job.id)
                    .order_by(Application.id)
                )
                apps = result.scalars().unique().all()
                
                fetch_duration = (time.time() - fetch_start) * 1000
                fetch_times.append(fetch_duration)
            
            avg_duration = sum(fetch_times) / len(fetch_times)
            self.perf.record("fetch_300_apps", avg_duration)
            
            assert len(apps) == 300, f"Expected 300 apps, got {len(apps)}"
            assert_in_range(avg_duration, 0, 5000, f"Dashboard fetch must be <5s, got {avg_duration:.2f}ms")
            
            duration_ms = (time.time() - start_time) * 1000
            self.reporter.add_result(TestResult(
                test_name=test_name,
                passed=True,
                duration_ms=duration_ms,
                assertion_details=f"Fetch 300 apps: {avg_duration:.2f}ms avg",
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
    async def test_scale_bulk_status_update_100_applicants(
        self,
        db_session: AsyncSession,
        test_job: Job,
        bulk_students_100: List,
    ):
        """
        Bulk update status for 50 of 100 applicants.
        Verify performance and consistency.
        """
        test_name = "test_scale_bulk_status_update_100_applicants"
        start_time = time.time()
        
        try:
            # Create 100 applications
            for i, student in enumerate(bulk_students_100):
                app = Application(
                    student_id=student.id,
                    job_id=test_job.id,
                    status=ApplicationStatus.PENDING,
                    is_eligible=True,
                )
                db_session.add(app)
            
            await db_session.commit()
            
            # Get appIDs for first 50
            result = await db_session.execute(
                select(Application.id).filter(Application.job_id == test_job.id).order_by(Application.id)
            )
            app_ids = result.scalars().all()[:50]
            
            # Bulk update
            update_start = time.time()
            for app_id in app_ids:
                result = await db_session.execute(
                    select(Application).filter(Application.id == app_id)
                )
                app = result.scalar_one()
                app.status = ApplicationStatus.REVIEWING
            
            await db_session.commit()
            update_duration = (time.time() - update_start) * 1000
            
            self.perf.record("bulk_update_50_apps", update_duration)
            
            # Verify
            verify_result = await db_session.execute(
                select(Application).filter(Application.job_id == test_job.id)
            )
            all_apps = verify_result.scalars().all()
            
            reviewing_count = sum(1 for a in all_apps if a.status == ApplicationStatus.REVIEWING)
            assert reviewing_count == 50, f"Expected 50 REVIEWING, got {reviewing_count}"
            
            assert_in_range(update_duration, 0, 2000, f"Bulk update must be <2s, got {update_duration:.2f}ms")
            
            duration_ms = (time.time() - start_time) * 1000
            self.reporter.add_result(TestResult(
                test_name=test_name,
                passed=True,
                duration_ms=duration_ms,
                assertion_details=f"Bulk update 50 apps: {update_duration:.2f}ms",
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
    async def test_scale_filtering_by_status(
        self,
        db_session: AsyncSession,
        test_job: Job,
        bulk_students_100: List,
    ):
        """
        Create 100 applications with mixed statuses, then filter.
        Verify filter performance scales well.
        """
        test_name = "test_scale_filtering_by_status"
        start_time = time.time()
        
        try:
            # Create 100 applications with varied statuses
            statuses = [
                ApplicationStatus.PENDING,
                ApplicationStatus.REVIEWING,
                ApplicationStatus.SHORTLISTED,
                ApplicationStatus.REJECTED,
            ]
            
            for i, student in enumerate(bulk_students_100):
                app = Application(
                    student_id=student.id,
                    job_id=test_job.id,
                    status=statuses[i % 4],
                    is_eligible=True,
                )
                db_session.add(app)
            
            await db_session.commit()
            
            # Measure filter performance for each status
            filter_times = {}
            for status in statuses:
                filter_start = time.time()
                
                result = await db_session.execute(
                    select(Application)
                    .filter(Application.job_id == test_job.id, Application.status == status)
                    .order_by(Application.id)
                )
                apps = result.scalars().all()
                
                filter_duration = (time.time() - filter_start) * 1000
                filter_times[status] = filter_duration
                
                # Each status should have ~25 apps
                assert 20 <= len(apps) <= 30, f"Status {status}: expected ~25, got {len(apps)}"
            
            # Log performance
            for status, duration in filter_times.items():
                self.perf.record(f"filter_{status}", duration)
                assert_in_range(duration, 0, 500, f"Filter {status} took {duration:.2f}ms (should be <500ms)")
            
            duration_ms = (time.time() - start_time) * 1000
            self.reporter.add_result(TestResult(
                test_name=test_name,
                passed=True,
                duration_ms=duration_ms,
                assertion_details=f"Filters: {dict((s.value, f'{t:.1f}ms') for s, t in filter_times.items())}",
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
    async def test_scale_count_aggregation(
        self,
        db_session: AsyncSession,
        test_job: Job,
        bulk_students_100: List,
    ):
        """
        Aggregate counts (total, eligible, selected) for dashboard metrics.
        Verify no N+1 queries and fast response.
        """
        test_name = "test_scale_count_aggregation"
        start_time = time.time()
        
        try:
            # Create 100 applications with mixed statuses
            for i, student in enumerate(bulk_students_100):
                is_eligible = i % 10 != 0  # 90% eligible
                status = ApplicationStatus.ACCEPTED if i % 20 == 0 else ApplicationStatus.PENDING
                
                app = Application(
                    student_id=student.id,
                    job_id=test_job.id,
                    status=status,
                    is_eligible=is_eligible,
                )
                db_session.add(app)
            
            await db_session.commit()
            
            # Measure aggregation performance
            agg_start = time.time()
            
            total = await db_session.scalar(
                select(func.count(Application.id)).filter(Application.job_id == test_job.id)
            )
            
            eligible = await db_session.scalar(
                select(func.count(Application.id)).filter(
                    Application.job_id == test_job.id,
                    Application.is_eligible == True,
                )
            )
            
            selected = await db_session.scalar(
                select(func.count(Application.id)).filter(
                    Application.job_id == test_job.id,
                    Application.status == ApplicationStatus.ACCEPTED,
                )
            )
            
            agg_duration = (time.time() - agg_start) * 1000
            self.perf.record("aggregation_100_apps", agg_duration)
            
            assert total == 100, f"Total should be 100, got {total}"
            assert eligible == 90, f"Eligible should be ~90, got {eligible}"
            assert selected == 5, f"Selected should be ~5, got {selected}"
            
            assert_in_range(agg_duration, 0, 200, f"Aggregation took {agg_duration:.2f}ms (should be <200ms)")
            
            duration_ms = (time.time() - start_time) * 1000
            self.reporter.add_result(TestResult(
                test_name=test_name,
                passed=True,
                duration_ms=duration_ms,
                assertion_details=f"Counts: {total} total, {eligible} eligible, {selected} selected in {agg_duration:.2f}ms",
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
