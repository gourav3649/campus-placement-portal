"""Database connection test - verify PostgreSQL connectivity"""
import asyncio
import os
import sys

# Load .env file explicitly
from dotenv import load_dotenv
load_dotenv()

async def test_db_connection():
    print("=" * 60)
    print("DATABASE CONNECTION TEST")
    print("=" * 60)
    
    # 1. Check environment
    print("\n1. ENVIRONMENT CHECK:")
    db_url = os.getenv('DATABASE_URL')
    print(f"   DATABASE_URL: {db_url}")
    if not db_url:
        print("   ❌ DATABASE_URL not found in environment!")
        return False
    
    # Check if using asyncpg
    if 'asyncpg' in db_url:
        print("   ✅ Using asyncpg driver")
    else:
        print("   ⚠️  Not using asyncpg driver!")
    
    # 2. Import and test engine
    print("\n2. IMPORTING DATABASE ENGINE:")
    try:
        from app.database import engine
        print("   ✅ Engine imported successfully")
        print(f"   Engine: {engine}")
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        return False
    
    # 3. Test connection
    print("\n3. TESTING CONNECTION:")
    try:
        async with engine.connect() as conn:
            print("   ✅ Connection opened")
            
            # Execute SELECT 1
            from sqlalchemy import text
            result = await conn.execute(text("SELECT 1"))
            value = result.scalar()
            
            print(f"   ✅ Query executed: SELECT 1")
            print(f"   ✅ Result: {value}")
            
            if value == 1:
                print("\n" + "=" * 60)
                print("✅ CONNECTION SUCCESSFUL")
                print("=" * 60)
                return True
    
    except Exception as e:
        print(f"   ❌ Connection failed: {type(e).__name__}")
        print(f"   Error: {e}")
        print("\n" + "=" * 60)
        print("❌ CONNECTION FAILED")
        print("=" * 60)
        return False

if __name__ == "__main__":
    success = asyncio.run(test_db_connection())
    sys.exit(0 if success else 1)
