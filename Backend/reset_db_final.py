#!/usr/bin/env python3
"""
Reset the database by terminating connections and recreating.
"""
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def reset_database():
    """Drop and recreate database."""
    
    # Create async engine for postgres default DB
    admin_engine = create_async_engine(
        "postgresql+asyncpg://postgres:gourav@localhost/postgres",
        echo=False,
        isolation_level="AUTOCOMMIT"  # Required for DROP/CREATE DATABASE
    )
    
    async with admin_engine.begin() as conn:
        try:
            print("Terminating all connections to 'campus_placement_db'...")
            await conn.execute(text("""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = 'campus_placement_db'
                AND pid <> pg_backend_pid()
            """))
            print("✓ Connections terminated")
        except Exception as e:
            print(f"Note: {e}")
        
        try:
            print("Dropping database 'campus_placement_db'...")
            await conn.execute(text("DROP DATABASE IF EXISTS campus_placement_db"))
            print("✓ Database dropped")
        except Exception as e:
            print(f"✗ Error dropping: {e}")
            return
        
        try:
            print("Creating database 'campus_placement_db'...")
            await conn.execute(text("CREATE DATABASE campus_placement_db"))
            print("✓ Database created")
        except Exception as e:
            print(f"✗ Error creating: {e}")
            return
    
    await admin_engine.dispose()
    
    # Step 2: Create all tables
    print("\nCreating tables from models...")
    try:
        # IMPORTANT: Import models to register them with Base
        from app import models  # This registers all models with Base
        from app.database import engine, Base
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✓ All tables created")
        
        # Verify
        async with engine.begin() as conn:
            result = await conn.execute(text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name='jobs' 
                ORDER BY ordinal_position
            """))
            columns = [row[0] for row in result.fetchall()]
            print(f"\n✓ Jobs table: {len(columns)} columns")
            if columns:
                print(f"  - currency: {'currency' in columns}")
                print(f"  - drive_status: {'drive_status' in columns}")
            else:
                print(f"  WARNING: No columns found!")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(reset_database())
