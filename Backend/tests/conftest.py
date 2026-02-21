import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.main import app
from app.database import Base, get_db
from app.core.config import get_settings

settings = get_settings()

# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://test_user:test_password@localhost:5432/test_campus_placement_db"

# Create test engine
test_engine = create_async_engine(TEST_DATABASE_URL, echo=True)
TestAsyncSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@pytest.fixture(scope="session")
async def setup_database():
    """Create test database tables."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session(setup_database):
    """Get test database session."""
    async with TestAsyncSessionLocal() as session:
        yield session


@pytest.fixture
async def client(db_session):
    """Get test client with database override."""
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
def student_data():
    """Sample student registration data."""
    return {
        "user_data": {
            "email": "student@test.com",
            "password": "testpassword123",
            "role": "student"
        },
        "student_data": {
            "first_name": "John",
            "last_name": "Doe",
            "phone": "+1234567890",
            "enrollment_number": "EN123456",
            "university": "Test University",
            "degree": "Bachelor of Science",
            "major": "Computer Science",
            "graduation_year": 2024,
            "cgpa": 8.5,
            "bio": "Passionate software developer",
            "skills": "Python, JavaScript, React"
        }
    }


@pytest.fixture
def recruiter_data():
    """Sample recruiter registration data."""
    return {
        "user_data": {
            "email": "recruiter@test.com",
            "password": "testpassword123",
            "role": "recruiter"
        },
        "recruiter_data": {
            "company_name": "Tech Corp",
            "company_website": "https://techcorp.com",
            "company_description": "Leading tech company",
            "first_name": "Jane",
            "last_name": "Smith",
            "position": "HR Manager",
            "phone": "+1987654321"
        }
    }
