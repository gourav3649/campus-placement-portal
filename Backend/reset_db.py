import asyncio
from sqlalchemy import text
from app.database import engine

async def reset_db():
    async with engine.begin() as conn:
        print("Dropping all tables in public schema...")
        await conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
        print("Database reset complete.")

if __name__ == "__main__":
    asyncio.run(reset_db())
