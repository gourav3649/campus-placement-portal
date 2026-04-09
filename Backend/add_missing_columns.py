#!/usr/bin/env python3
"""
Add all missing columns to the jobs table.
"""
import asyncio
from sqlalchemy import text
from app.database import engine

async def add_missing_columns():
    """Add missing columns to jobs table."""
    columns_to_add = [
        ("currency", "VARCHAR(10) DEFAULT 'USD'"),
        ("experience_years", "INTEGER"),
        ("education_level", "VARCHAR(100)"),
        ("embedding_vector", "VECTOR(384)"),
    ]
    
    async with engine.begin() as conn:
        # Check which columns already exist
        result = await conn.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='jobs'
        """))
        existing_cols = {row[0] for row in result.fetchall()}
        print(f"Existing columns: {existing_cols}")
        
        # Add missing columns
        for col_name, col_def in columns_to_add:
            if col_name not in existing_cols:
                try:
                    await conn.execute(text(f"ALTER TABLE jobs ADD COLUMN {col_name} {col_def}"))
                    print(f"✓ Added column: {col_name}")
                except Exception as e:
                    print(f"✗ Error adding {col_name}: {e}")
            else:
                print(f"✓ Column already exists: {col_name}")

if __name__ == "__main__":
    asyncio.run(add_missing_columns())
