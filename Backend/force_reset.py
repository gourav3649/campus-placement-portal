import asyncio
from sqlalchemy import text
from app.database import engine

async def force_reset():
    # Use postgres database to drop campus_placement_db
    # But wait, I can just use the current connection to drop all tables in public schema one by one
    async with engine.begin() as conn:
        print("Dropping all tables manually...")
        # Get all table names
        res = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
        tables = [r[0] for r in res.fetchall()]
        for table in tables:
            print(f"Dropping table {table}...")
            await conn.execute(text(f"DROP TABLE IF EXISTS \"{table}\" CASCADE;"))
        
        # Also drop types
        print("Dropping types...")
        # (Optional but good)
        
        print("Done.")

if __name__ == "__main__":
    asyncio.run(force_reset())
