"""Quick script to verify seeded data."""
import asyncio
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.college import College
from app.models.user import User
from app.models.placement_officer import PlacementOfficer


async def verify():
    async with AsyncSessionLocal() as session:
        # Get counts
        colleges = (await session.execute(select(College))).scalars().all()
        users = (await session.execute(select(User))).scalars().all()
        officers = (await session.execute(select(PlacementOfficer))).scalars().all()
        
        print(f"\n📊 Database Contents:")
        print(f"\nColleges: {len(colleges)}")
        for c in colleges:
            print(f"  ✓ {c.name} (ID={c.id})")
        
        print(f"\nUsers: {len(users)}")
        for u in users:
            print(f"  ✓ {u.email} (Role: {u.role.value})")
        
        print(f"\nPlacement Officers: {len(officers)}")
        for o in officers:
            print(f"  ✓ {o.name} - {o.department}")


if __name__ == "__main__":
    asyncio.run(verify())
