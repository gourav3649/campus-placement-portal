#!/usr/bin/env python3
"""
Fix the database schema by adding missing columns.
"""
import asyncio
from sqlalchemy import text
from app.database import engine

async def fix_schema():
    async with engine.begin() as conn:
        try:
            # Add drive_status column if it doesn't exist
            await conn.execute(text("""
                ALTER TABLE jobs 
                ADD COLUMN IF NOT EXISTS drive_status VARCHAR DEFAULT 'draft'
            """))
            print("✓ Added drive_status column to jobs table")
        except Exception as e:
            if "already exists" in str(e):
                print("✓ drive_status column already exists")
            else:
                print(f"✗ Error adding drive_status: {e}")
        
        try:
            # Verify the columns
            result = await conn.execute(text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name='jobs' 
                ORDER BY ordinal_position
            """))
            columns = [row[0] for row in result.fetchall()]
            print(f"\nColumns in jobs table: {columns}")
            
            if 'drive_status' in columns:
                print("✓ drive_status column is present in schema")
            else:
                print("✗ drive_status column is still missing")
        except Exception as e:
            print(f"✗ Error verifying schema: {e}")

if __name__ == "__main__":
    asyncio.run(fix_schema())
