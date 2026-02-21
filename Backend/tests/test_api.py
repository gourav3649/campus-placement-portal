import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health check endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "app_name" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Test root endpoint."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_register_student(client: AsyncClient, student_data):
    """Test student registration."""
    response = await client.post(
        "/api/v1/auth/register/student",
        json=student_data
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == student_data["user_data"]["email"]
    assert data["role"] == "student"


@pytest.mark.asyncio
async def test_register_recruiter(client: AsyncClient, recruiter_data):
    """Test recruiter registration."""
    response = await client.post(
        "/api/v1/auth/register/recruiter",
        json=recruiter_data
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == recruiter_data["user_data"]["email"]
    assert data["role"] == "recruiter"


@pytest.mark.asyncio
async def test_login(client: AsyncClient, student_data):
    """Test user login."""
    # First register
    await client.post("/api/v1/auth/register/student", json=student_data)
    
    # Then login
    response = await client.post(
        "/api/v1/auth/login/json",
        json={
            "email": student_data["user_data"]["email"],
            "password": student_data["user_data"]["password"]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_get_student_profile(client: AsyncClient, student_data):
    """Test getting student profile."""
    # Register
    await client.post("/api/v1/auth/register/student", json=student_data)
    
    # Login
    login_response = await client.post(
        "/api/v1/auth/login/json",
        json={
            "email": student_data["user_data"]["email"],
            "password": student_data["user_data"]["password"]
        }
    )
    token = login_response.json()["access_token"]
    
    # Get profile
    response = await client.get(
        "/api/v1/students/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == student_data["user_data"]["email"]
    assert data["first_name"] == student_data["student_data"]["first_name"]
