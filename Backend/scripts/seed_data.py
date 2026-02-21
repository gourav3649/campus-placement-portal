"""
Seed data script for Campus Placement Portal.
Creates initial college, admin user, and placement officer.
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal
from app.models.college import College
from app.models.user import User
from app.models.placement_officer import PlacementOfficer
from app.schemas.user import Role
from app.core.security import get_password_hash
from app.core.config import get_settings

settings = get_settings()


async def seed_database():
    """Seed the database with initial data."""
    async with AsyncSessionLocal() as session:
        try:
            # Check if college already exists
            from sqlalchemy import select
            result = await session.execute(
                select(College).where(College.id == settings.COLLEGE_ID)
            )
            existing_college = result.scalar_one_or_none()
            
            if existing_college:
                print(f"✓ College '{existing_college.name}' already exists")
            else:
                # Create College X
                college = College(
                    id=settings.COLLEGE_ID,
                    name=settings.COLLEGE_NAME,
                    location="City, State, India",
                    contact_email="placements@collegex.edu",
                    contact_phone="+91-XXX-XXXXXXX",
                    website="https://collegex.edu",
                    accreditation="NAAC A++",
                    established_year=2000
                )
                session.add(college)
                await session.flush()
                print(f"✓ Created college: {college.name}")

            # Check if admin user already exists
            result = await session.execute(
                select(User).where(User.email == "admin@collegex.edu")
            )
            existing_admin = result.scalar_one_or_none()
            
            if existing_admin:
                print(f"✓ Admin user already exists: {existing_admin.email}")
            else:
                # Create admin user
                admin_user = User(
                    email="admin@collegex.edu",
                    hashed_password=get_password_hash("admin123"),  # Change in production!
                    role=Role.ADMIN,
                    is_active=True
                )
                session.add(admin_user)
                await session.flush()
                print(f"✓ Created admin user: {admin_user.email} (password: admin123)")

            # Check if placement officer already exists
            result = await session.execute(
                select(User).where(User.email == "placement@collegex.edu")
            )
            existing_po_user = result.scalar_one_or_none()
            
            if existing_po_user:
                print(f"✓ Placement officer user already exists: {existing_po_user.email}")
            else:
                # Create placement officer user
                po_user = User(
                    email="placement@collegex.edu",
                    hashed_password=get_password_hash("placement123"),  # Change in production!
                    role=Role.PLACEMENT_OFFICER,
                    is_active=True
                )
                session.add(po_user)
                await session.flush()
                
                # Create placement officer profile
                placement_officer = PlacementOfficer(
                    user_id=po_user.id,
                    college_id=settings.COLLEGE_ID,
                    name="Placement Officer",
                    email="placement@collegex.edu",
                    department="Training & Placement Cell",
                    designation="Training & Placement Officer",
                    phone="+91-XXX-XXXXXXX"
                )
                session.add(placement_officer)
                print(f"✓ Created placement officer: {po_user.email} (password: placement123)")

            # Commit all changes
            await session.commit()
            print("\n✅ Database seeding completed successfully!")
            print(f"\nLogin credentials:")
            print(f"  Admin: admin@collegex.edu / admin123")
            print(f"  Placement Officer: placement@collegex.edu / placement123")
            print(f"\n⚠️  Remember to change these passwords in production!")

        except Exception as e:
            await session.rollback()
            print(f"❌ Error seeding database: {e}")
            raise


if __name__ == "__main__":
    print("🌱 Seeding database...\n")
    asyncio.run(seed_database())
