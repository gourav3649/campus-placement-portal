import asyncio
from sqlalchemy import text
from app.database import AsyncSessionLocal

async def check_all_recruiters():
    async with AsyncSessionLocal() as db:
        result = await db.execute(text("SELECT n.nspname, t.relname FROM pg_class t JOIN pg_namespace n ON n.oid = t.relnamespace WHERE t.relname = 'recruiters'"))
        rows = result.fetchall()
        for row in rows:
            print(f"Schema: {row[0]}, Table: {row[1]}")

if __name__ == "__main__":
    asyncio.run(check_all_recruiters())
