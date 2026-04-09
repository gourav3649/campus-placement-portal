#!/usr/bin/env python3
"""
Setup initial colleges for testing.
"""
import asyncio
from app.models import College
from app.database import AsyncSessionLocal, engine, Base

async def setup_colleges():
    """Create test colleges in the database."""
    # First ensure all tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create test college
    async with AsyncSessionLocal() as session:
        # Check if college already exists
        from sqlalchemy import select
        result = await session.execute(select(College).filter(College.name == "Test Institute of Technology"))
        existing = result.scalar_one_or_none()
        
        if not existing:
            college = College(
                name="Test Institute of Technology",
                location="Test City",
                website="https://test-college.edu",
                is_active=True
            )
            session.add(college)
            await session.commit()
            await session.refresh(college)
            print(f"✓ Created college: ID={college.id}, Name={college.name}")
        else:
            print(f"✓ College already exists: ID={existing.id}, Name={existing.name}")

if __name__ == "__main__":
    asyncio.run(setup_colleges())
