import asyncio
from sqlalchemy import text
from app.database import AsyncSessionLocal

async def check_columns():
    async with AsyncSessionLocal() as db:
        result = await db.execute(text("SELECT table_schema, table_name, column_name FROM information_schema.columns WHERE table_name = 'recruiters'"))
        rows = result.fetchall()
        for row in rows:
            print(f"Schema: {row[0]}, Table: {row[1]}, Column: {row[2]}")

if __name__ == "__main__":
    asyncio.run(check_columns())
