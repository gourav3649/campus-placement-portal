"""Quick test for placement officer registration"""
import httpx
from datetime import datetime

BASE_URL = "http://localhost:8001/api/v1"

async def test_placement_officer():
    async with httpx.AsyncClient() as client:
        # Register placement officer
        email = f"officer_test_{datetime.now().timestamp()}@example.com"
        payload = {
            "user_data": {
                "email": email,
                "password": "TestPass123!",
                "role": "placement_officer",
            },
            "officer_data": {
                "name": "TestOfficer",
                "email": email,
                "designation": "Placement Officer",
                "department": "Placement",
                "college_id": 1,
            }
        }
        
        response = await client.post(f"{BASE_URL}/auth/register/placement_officer", json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 201

if __name__ == "__main__":
    import asyncio
    result = asyncio.run(test_placement_officer())
    print(f"Success: {result}")
