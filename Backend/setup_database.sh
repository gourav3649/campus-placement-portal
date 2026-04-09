#!/bin/bash
# Database Setup Script - Run this to initialize PostgreSQL for the project
# Usage: bash setup_database.sh

set -e

echo "=== Campus Placement Portal - Database Setup ==="
echo ""

# Step 1: Check PostgreSQL status
echo "1. Checking PostgreSQL service..."
if command -v psql &> /dev/null; then
    echo "✅ PostgreSQL command-line client found"
    psql --version
else
    echo "❌ PostgreSQL client not found in PATH"
    echo "   Windows: Add PostgreSQL bin directory to PATH or use pgAdmin GUI"
    exit 1
fi

# Step 2: Create database and user
echo ""
echo "2. Creating database user and database..."
echo "   (Enter PostgreSQL superuser password when prompted)"

# Try to create user and database
PGPASSWORD=postgres psql -U postgres -h localhost -c "
    -- Create user if not exists
    DO \$do\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'user') THEN
            CREATE USER \"user\" WITH PASSWORD 'password';
        END IF;
    END
    \$do\$;
    
    -- Grant privileges
    ALTER USER \"user\" CREATEDB;
    
    -- Create database if not exists
    SELECT 'CREATE DATABASE campus_placement_db OWNER \"user\"'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'campus_placement_db');
" 2>/dev/null && echo "✅ User and database setup complete" || echo "⚠️  Check credentials"

# Step 3: Test connection
echo ""
echo "3. Testing connection with new credentials..."
PGPASSWORD=password psql -U user -h localhost -d campus_placement_db -c "SELECT 1;" && \
    echo "✅ Connection successful!" || \
    echo "❌ Connection failed - check credentials"

echo ""
echo "4. Ready for Python migrations..."
echo ""
echo "Next steps:"
echo "  cd Backend"
echo "  python -c \"import asyncio; from app.database import engine; print(asyncio.run(engine.connect()))\"" 
echo "  alembic upgrade head"
