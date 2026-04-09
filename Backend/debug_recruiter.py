"""Debug recruiter lookup"""
import asyncio
import httpx
from datetime import datetime

BASE_URL = "http://localhost:8001/api/v1"

async def debug():
    async with httpx.AsyncClient() as client:
        email_rec = f"recruiter_{datetime.now().timestamp()}@test.com"
        
        # Register
        resp = await client.post(
            f"{BASE_URL}/auth/register/recruiter",
            json={
                "user_data": {"email": email_rec, "password": "Test123!", "role": "recruiter"},
                "recruiter_data": {
                    "first_name": "Bob", "last_name": "Smith",
                    "company_name": "TechCorp", "email": email_rec, "college_id": 1
                }
            }
        )
        
        rdata = resp.json()
        recruiter_id = rdata["user"]["id"]
        recruiter_token = rdata["access_token"]
        
        print(f"Registered recruiter with user.id={recruiter_id}")
        print(f"Response: {rdata}")
        
        # Now register officer
        email_off = f"officer_{datetime.now().timestamp()}@test.com"
        resp = await client.post(
            f"{BASE_URL}/auth/register/placement_officer",
            json={
                "user_data": {"email": email_off, "password": "Test123!", "role": "placement_officer"},
                "officer_data": {
                    "name": "Officer", "email": email_off, "college_id": 1,
                    "designation": "Officer", "department": "Placement"
                }
            }
        )
        
        officer_data = resp.json()
        officer_token = officer_data["access_token"]
        
        print(f"\nNow verifying recruiter with ID={recruiter_id}")
        
        # Try to verify
        resp = await client.put(
            f"{BASE_URL}/recruiters/{recruiter_id}/verify",
            headers={"Authorization": f"Bearer {officer_token}"},
            params={"is_verified": True}
        )
        
        print(f"Verify response: {resp.status_code}")
        print(f"Response body: {resp.json()}")

if __name__ == "__main__":
    asyncio.run(debug())
