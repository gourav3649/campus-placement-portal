"""Test all three registration endpoints with new response format"""
import httpx
from datetime import datetime

BASE_URL = "http://localhost:8001/api/v1"

async def test_all_registrations():
    async with httpx.AsyncClient() as client:
        print("\n" + "="*70)
        print("  REGISTRATION ENDPOINT RESPONSE FORMAT VERIFICATION")
        print("="*70)
        
        # Test Student
        print("\n[1] Student Registration:")
        resp = await client.post(
            f"{BASE_URL}/auth/register/student",
            json={
                "user_data": {"email": f"student_{datetime.now().timestamp()}@test.com", "password": "Test123!", "role": "student"},
                "student_data": {
                    "first_name": "John", "last_name": "Doe",
                    "branch": "CS", "graduation_year": 2024, "cgpa": 8.5, "college_id": 1
                }
            }
        )
        data = resp.json()
        print(f"   Status: {resp.status_code}")
        print(f"   Response keys: {list(data.keys())}")
        print(f"   User ID: {data['user']['id']}")
        print(f"   User Role: {data['user']['role']}")
        print(f"   Token Type: {data['token_type']}")
        print(f"   ✅ Access Token returned: {data['access_token'][:30]}...")
        
        # Test Recruiter
        print("\n[2] Recruiter Registration:")
        resp = await client.post(
            f"{BASE_URL}/auth/register/recruiter",
            json={
                "user_data": {"email": f"recruiter_{datetime.now().timestamp()}@test.com", "password": "Test123!", "role": "recruiter"},
                "recruiter_data": {
                    "first_name": "Jane", "last_name": "Smith",
                    "company_name": "TechCorp", "email": f"recruiter_{datetime.now().timestamp()}@test.com", "college_id": 1
                }
            }
        )
        data = resp.json()
        print(f"   Status: {resp.status_code}")
        print(f"   Response keys: {list(data.keys())}")
        print(f"   User ID: {data['user']['id']}")
        print(f"   User Role: {data['user']['role']}")
        print(f"   Token Type: {data['token_type']}")
        print(f"   ✅ Access Token returned: {data['access_token'][:30]}...")
        
        # Test Placement Officer
        print("\n[3] Placement Officer Registration:")
        resp = await client.post(
            f"{BASE_URL}/auth/register/placement_officer",
            json={
                "user_data": {"email": f"officer_{datetime.now().timestamp()}@test.com", "password": "Test123!", "role": "placement_officer"},
                "officer_data": {
                    "name": "Officer", "email": f"officer_{datetime.now().timestamp()}@test.com", "college_id": 1,
                    "designation": "Officer", "department": "Placement"
                }
            }
        )
        data = resp.json()
        print(f"   Status: {resp.status_code}")
        print(f"   Response keys: {list(data.keys())}")
        print(f"   User ID: {data['user']['id']}")
        print(f"   User Role: {data['user']['role']}")
        print(f"   Token Type: {data['token_type']}")
        print(f"   ✅ Access Token returned: {data['access_token'][:30]}...")
        
        print("\n" + "="*70)
        print("  ✅ ALL ENDPOINTS RETURN CORRECT FORMAT")
        print("  Format: {access_token, token_type, user{id, role}}")
        print("="*70 + "\n")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_all_registrations())
