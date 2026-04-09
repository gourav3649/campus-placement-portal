#!/usr/bin/env python3
"""
Reset database by dropping all tables and recreating from models.
"""
import asyncio
from sqlalchemy import text, inspect
from app.database import engine, Base

async def reset_database():
    """Drop all tables and recreate from models."""
    print("Dropping all tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    print("✓ All tables dropped")
    
    print("\nCreating new tables from models...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✓ All tables created")
    
    # Verify tables
    print("\nVerifying schema...")
    async with engine.begin() as conn:
        # Get table names
        result = await conn.execute(text("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public' 
            ORDER BY tablename
        """))
        tables = [row[0] for row in result.fetchall()]
        print(f"Tables in database: {tables}")
        
        # Check jobs table columns
        if 'jobs' in tables:
            result = await conn.execute(text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name='jobs' 
                ORDER BY ordinal_position
            """))
            columns = [row[0] for row in result.fetchall()]
            print(f"\nColumns in jobs table: {columns}")
            if 'drive_status' in columns:
                print("✓ drive_status column is present")
            else:
                print("✗ drive_status column is missing")

if __name__ == "__main__":
    print("WARNING: This will DROP all data from the database!")
    asyncio.run(reset_database())
