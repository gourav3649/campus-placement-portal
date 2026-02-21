"""Interactive database viewer for Campus Placement Portal."""
import asyncio
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import select, text
from app.database import AsyncSessionLocal
from app.models.college import College
from app.models.user import User
from app.models.student import Student
from app.models.recruiter import Recruiter
from app.models.placement_officer import PlacementOfficer
from app.models.job import Job
from app.models.application import Application
from app.models.resume import Resume


async def show_database_overview():
    """Display comprehensive database overview."""
    async with AsyncSessionLocal() as session:
        print("="*70)
        print("📊 CAMPUS PLACEMENT DATABASE - OVERVIEW")
        print("="*70)
        
        # Get table counts
        print("\n📈 Table Statistics:")
        print("-"*70)
        
        tables = [
            ("Colleges", College),
            ("Users", User),
            ("Students", Student),
            ("Recruiters", Recruiter),
            ("Placement Officers", PlacementOfficer),
            ("Jobs", Job),
            ("Applications", Application),
            ("Resumes", Resume)
        ]
        
        for name, model in tables:
            result = await session.execute(select(model))
            count = len(result.scalars().all())
            print(f"  {name:<25} {count:>5} records")
        
        # Show colleges in detail
        print("\n" + "="*70)
        print("🏛️  COLLEGES")
        print("-"*70)
        colleges = (await session.execute(select(College))).scalars().all()
        for college in colleges:
            print(f"\nID: {college.id}")
            print(f"Name: {college.name}")
            print(f"Location: {college.location}")
            print(f"Accreditation: {college.accreditation}")
            print(f"Website: {college.website}")
            print(f"Contact: {college.contact_email} | {college.contact_phone}")
            print(f"Established: {college.established_year}")
            print(f"Active: {'Yes' if college.is_active else 'No'}")
        
        # Show users in detail
        print("\n" + "="*70)
        print("👥 USERS")
        print("-"*70)
        users = (await session.execute(select(User))).scalars().all()
        for user in users:
            print(f"\nID: {user.id}")
            print(f"Email: {user.email}")
            print(f"Role: {user.role.value}")
            print(f"Active: {'Yes' if user.is_active else 'No'}")
            print(f"Verified: {'Yes' if user.is_verified else 'No'}")
            print(f"Created: {user.created_at}")
        
        # Show placement officers
        print("\n" + "="*70)
        print("👔 PLACEMENT OFFICERS")
        print("-"*70)
        officers = (await session.execute(select(PlacementOfficer))).scalars().all()
        for officer in officers:
            print(f"\nID: {officer.id}")
            print(f"Name: {officer.name}")
            print(f"Email: {officer.email}")
            print(f"Department: {officer.department}")
            print(f"Designation: {officer.designation}")
            print(f"Phone: {officer.phone}")
            print(f"College ID: {officer.college_id}")
            print(f"User ID: {officer.user_id}")
        
        print("\n" + "="*70)
        print("✅ Database Overview Complete")
        print("="*70)


async def show_connection_info():
    """Display database connection information."""
    async with AsyncSessionLocal() as session:
        # Get PostgreSQL version
        result = await session.execute(text("SELECT version()"))
        version = result.scalar()
        
        # Get current database
        result = await session.execute(text("SELECT current_database()"))
        db_name = result.scalar()
        
        # Get current user
        result = await session.execute(text("SELECT current_user"))
        db_user = result.scalar()
        
        print("\n🔌 Database Connection Info:")
        print("-"*70)
        print(f"Database: {db_name}")
        print(f"User: {db_user}")
        print(f"PostgreSQL Version: {version}")


if __name__ == "__main__":
    print("\n")
    asyncio.run(show_connection_info())
    print("\n")
    asyncio.run(show_database_overview())
    print("\n")
