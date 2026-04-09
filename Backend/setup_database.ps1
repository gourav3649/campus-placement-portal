# Database Setup Script for Windows PowerShell
# Usage: .\setup_database.ps1

Write-Host "=== Campus Placement Portal - Database Setup (Windows) ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Find PostgreSQL installation
Write-Host "1. Looking for PostgreSQL installation..." -ForegroundColor Yellow
$pgPaths = @(
    "C:\Program Files\PostgreSQL\15\bin",
    "C:\Program Files\PostgreSQL\14\bin",
    "C:\Program Files (x86)\PostgreSQL\15\bin",
    "C:\Program Files (x86)\PostgreSQL\14\bin"
)

$psqlPath = $null
foreach ($path in $pgPaths) {
    if (Test-Path "$path\psql.exe") {
        $psqlPath = "$path\psql.exe"
        break
    }
}

if (-not $psqlPath) {
    Write-Host "❌ PostgreSQL not found in standard locations" -ForegroundColor Red
    Write-Host "Please:" -ForegroundColor Yellow
    Write-Host "   1. Install PostgreSQL from https://www.postgresql.org/download/windows/"
    Write-Host "   2. Add bin directory to PATH"
    Write-Host "   3. Run this script again"
    exit 1
}

Write-Host "✅ Found PostgreSQL at: $psqlPath" -ForegroundColor Green

# Step 2: Create database and user
Write-Host ""
Write-Host "2. Creating database user and database..." -ForegroundColor Yellow
Write-Host "   (Enter PostgreSQL superuser password when prompted)" -ForegroundColor Gray

$sqlScript = @"
-- Create user if not exists
DO `$do`$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'user') THEN
        CREATE USER `"user`" WITH PASSWORD 'password';
    END IF;
END
`$do`$;

-- Grant privileges
ALTER USER `"user`" CREATEDB;

-- Create database if not exists
CREATE DATABASE campus_placement_db OWNER `"user`";
"@

# Save SQL script to temp file
$sqlFile = [System.IO.Path]::GetTempFileName()
$sqlScript | Out-File -FilePath $sqlFile -Encoding UTF8

# Execute SQL script
try {
    $env:PGPASSWORD = "postgres"
    & $psqlPath -U postgres -h localhost -f $sqlFile 2>&1 | Write-Host
    Write-Host "✅ User and database setup complete" -ForegroundColor Green
}
catch {
    Write-Host "⚠️  Setup encountered an issue:" -ForegroundColor Yellow
    Write-Host $_.Exception.Message
}
finally {
    Remove-Item $sqlFile -Force
    Remove-Item env:PGPASSWORD
}

# Step 3: Test connection
Write-Host ""
Write-Host "3. Testing connection with new credentials..." -ForegroundColor Yellow

try {
    $env:PGPASSWORD = "password"
    $output = & $psqlPath -U user -h localhost -d campus_placement_db -c "SELECT 1;" 2>&1
    
    if ($output -match "1") {
        Write-Host "✅ Connection successful!" -ForegroundColor Green
    } else {
        Write-Host "Test query output: $output"
    }
}
catch {
    Write-Host "❌ Connection failed:" -ForegroundColor Red
    Write-Host $_.Exception.Message
}
finally {
    Remove-Item env:PGPASSWORD
}

# Step 4: Python verification
Write-Host ""
Write-Host "4. Python verification steps:" -ForegroundColor Yellow
Write-Host "   Run these commands in order:"
Write-Host ""
Write-Host "   cd Backend"
Write-Host "   python -m alembic upgrade head" -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ Database setup complete!" -ForegroundColor Green
