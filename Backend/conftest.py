"""
Pytest configuration and shared fixtures for stress test suite.
"""

import pytest
import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import NullPool

from app.database import Base, AsyncSessionLocal


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests (session-scoped)."""
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def reset_db_between_tests():
    """
    Optional: Reset DB between tests if needed.
    Currently disabled to allow data accumulation for scale tests.
    """
    yield
    # Optional cleanup here


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as an asyncio test"
    )


def pytest_collection_modifyitems(config, items):
    """
    Auto-add asyncio marker to all async test functions.
    """
    for item in items:
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)
