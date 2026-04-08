import asyncio
from app.database import engine, Base
# Import all models so they are registered with Base.metadata
from app.models.user import User
from app.models.student import Student
from app.models.recruiter import Recruiter
from app.models.job import Job
from app.models.application import Application
from app.models.placement_officer import PlacementOfficer
from app.models.college import College
from app.models.notification import Notification
from app.models.offer import Offer

async def create_tables():
    async with engine.begin() as conn:
        print("Creating all tables from models...")
        await conn.run_sync(Base.metadata.create_all)
        print("Tables created.")

if __name__ == "__main__":
    asyncio.run(create_tables())
