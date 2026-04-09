"""Database schema verification - check all tables exist"""
import asyncio
import sys
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Required tables for the application
REQUIRED_TABLES = [
    'users',
    'students',
    'recruiters',
    'placement_officers',
    'colleges',
    'jobs',
    'applications',
    'application_rounds',
    'offers',
    'notifications',
    'placement_policies',
    'resumes',
]

async def check_schema():
    print("=" * 70)
    print("DATABASE SCHEMA VERIFICATION")
    print("=" * 70)
    
    # Import engine
    from app.database import engine
    from sqlalchemy import text, inspect
    
    try:
        # 1. Connect and check tables
        print("\n1. CONNECTING TO DATABASE:")
        async with engine.connect() as conn:
            print("   ✅ Connected successfully")
            
            # Get all tables in public schema
            print("\n2. CHECKING TABLES IN PUBLIC SCHEMA:")
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            
            existing_tables = [row[0] for row in result.fetchall()]
            
            if existing_tables:
                print(f"   Found {len(existing_tables)} tables:")
                for table in existing_tables:
                    print(f"      • {table}")
            else:
                print("   ❌ No tables found in public schema!")
                print("   Schema is empty - migrations may need to run")
            
            # 3. Check for required tables
            print("\n3. CHECKING REQUIRED TABLES:")
            missing = []
            found = []
            
            for table in REQUIRED_TABLES:
                if table in existing_tables:
                    print(f"   ✅ {table}")
                    found.append(table)
                else:
                    print(f"   ❌ {table} (MISSING)")
                    missing.append(table)
            
            # 4. Summary
            print("\n" + "=" * 70)
            print("SCHEMA STATUS SUMMARY")
            print("=" * 70)
            print(f"Total tables found: {len(existing_tables)}")
            print(f"Required tables found: {len(found)}/{len(REQUIRED_TABLES)}")
            
            if missing:
                print(f"\n❌ MISSING TABLES ({len(missing)}):")
                for table in missing:
                    print(f"   • {table}")
                print("\n⚠️  SCHEMA NOT READY - Run migrations:")
                print("   alembic upgrade head")
                return False
            else:
                print("\n✅ ALL REQUIRED TABLES EXIST")
                print("✅ SCHEMA IS READY")
                
                # Show table row counts
                print("\n4. TABLE ROW COUNTS:")
                for table in found:
                    result = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    print(f"   {table}: {count} rows")
                
                return True
    
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}")
        print(f"   {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(check_schema())
    sys.exit(0 if success else 1)
