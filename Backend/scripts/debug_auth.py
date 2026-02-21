"""Simple test to verify token authentication."""
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Login
print("1. Testing login...")
login_response = requests.post(
    f"{BASE_URL}/auth/login/json",
    json={"email": "admin@collegex.edu", "password": "admin123"}
)
print(f"   Status: {login_response.status_code}")

if login_response.status_code == 200:
    data = login_response.json()
    token = data["access_token"]
    print(f"   ✓ Got token: {token[:30]}...")
    
    # Test health endpoint (no auth required)
    print("\n2. Testing health endpoint (no auth)...")
    health_response = requests.get("http://localhost:8000/health")
    print(f"   Status: {health_response.status_code}")
    print(f"   Response: {health_response.json()}")
    
    # Test colleges endpoint with auth
    print("\n3. Testing colleges endpoint (with auth)...")
    colleges_response = requests.get(
        f"{BASE_URL}/colleges",
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"   Status: {colleges_response.status_code}")
    print(f"   Response: {colleges_response.text[:200]}")
    print(f"   Headers sent: Authorization=Bearer {token[:30]}...")
else:
    print("   ✗ Login failed")
    print(f"   Error: {login_response.text}")
