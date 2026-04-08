import asyncio
from sqlalchemy import text
from app.database import AsyncSessionLocal

async def get_version():
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(text("SELECT version_num FROM alembic_version"))
            print(f"Alembic Version: {result.scalar()}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(get_version())
