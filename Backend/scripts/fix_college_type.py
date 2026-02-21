"""Fix colleges.is_active column type from INTEGER to BOOLEAN in PostgreSQL."""
import asyncio
import asyncpg

async def fix():
    conn = await asyncpg.connect('postgresql://postgres:gourav@localhost:5432/campus_placement_db')
    try:
        # PostgreSQL won't auto-cast int to bool — use CASE expression
        await conn.execute("""
            ALTER TABLE colleges 
            ALTER COLUMN is_active TYPE boolean 
            USING CASE WHEN is_active = 0 THEN false ELSE true END;
        """)
        print("✅ Successfully changed colleges.is_active from INTEGER to BOOLEAN")
    except Exception as e:
        print(f"⚠️  Error (may already be boolean): {e}")
    finally:
        await conn.close()

asyncio.run(fix())
