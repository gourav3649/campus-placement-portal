import asyncio
from sqlalchemy import text
from app.database import AsyncSessionLocal

async def check_search_path():
    async with AsyncSessionLocal() as db:
        res = await db.execute(text("SHOW search_path"))
        print(f"Search Path: {res.scalar()}")
        
        res = await db.execute(text("SELECT nspname, relname FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE relname = 'recruiters'"))
        for row in res.fetchall():
            print(f"Table Found: {row[0]}.{row[1]}")

if __name__ == "__main__":
    asyncio.run(check_search_path())
