#!/usr/bin/env python3
"""
Completely reset the database by dropping and recreating it.
"""
import asyncio
import subprocess
import sys
from sqlalchemy import text, create_engine
from sqlalchemy.pool import StaticPool

async def reset_database_complete():
    """Drop and recreate the entire database."""
    
    # Connection to postgres default database (not campus_placement_db)
    postgres_url = "postgresql://postgres:gourav@localhost:5432/postgres"
    
    # Use regular synchronous engine for dropdb/createdb
    print("Dropping database 'campus_placement_db'...")
    try:
        result = subprocess.run(
            ["dropdb", "-U", "postgres", "--if-exists", "campus_placement_db"],
            capture_output=True,
            text=True,
            env={"PGPASSWORD": "gourav"}
        )
        if result.returncode == 0:
            print("✓ Database dropped")
        else:
            print(f"Note: {result.stderr.strip()}")
    except Exception as e:
        print(f"✗ Error dropping database: {e}")
        return
    
    print("\nCreating new database 'campus_placement_db'...")
    try:
        result = subprocess.run(
            ["createdb", "-U", "postgres", "campus_placement_db"],
            capture_output=True,
            text=True,
            env={"PGPASSWORD": "gourav"}
        )
        if result.returncode == 0:
            print("✓ Database created")
        else:
            print(f"✗ Error: {result.stderr}")
            return
    except Exception as e:
        print(f"✗ Error creating database: {e}")
        return
    
    # Now create all tables from models
    print("\nCreating tables from models...")
    try:
        from app.database import engine, Base
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✓ All tables created from models")
        
        # Verify
        async with engine.begin() as conn:
            result = await conn.execute(text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name='jobs' 
                ORDER BY ordinal_position
            """))
            columns = [row[0] for row in result.fetchall()]
            print(f"\nColumns in jobs table: {len(columns)} columns")
            print(f"Has 'currency': {'currency' in columns}")
            print(f"Has 'drive_status': {'drive_status' in columns}")
            
    except Exception as e:
        print(f"✗ Error creating tables: {e}")

if __name__ == "__main__":
    asyncio.run(reset_database_complete())
