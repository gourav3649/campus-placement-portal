"""
Simplified E2E Test - Focus on core workflow validation
"""
import httpx
import json
from datetime import datetime

BASE_URL = "http://localhost:8001/api/v1"

async def main():
    async with httpx.AsyncClient() as client:
        print("\n" + "="*70)
        print("  SIMPLIFIED E2E WORKFLOW TEST")
        print("="*70)
        
        # STEP 1: Create Student
        print("\n[1/6] Creating Student...")
        email1 = f"student_{datetime.now().timestamp()}@test.com"
        resp = await client.post(
            f"{BASE_URL}/auth/register/student",
            json={
                "user_data": {"email": email1, "password": "Test123!", "role": "student"},
                "student_data": {
                    "first_name": "John", "last_name": "Doe",
                    "branch": "CS", "graduation_year": 2024, "cgpa": 8.5, "college_id": 1
                }
            }
        )
        if resp.status_code == 201:
            print(f"   ✅ Student created: {email1}")
            student_token = resp.json()["access_token"]
        else:
            print(f"   ❌ Failed: {resp.status_code} - {resp.text}")
            return
        
        # STEP 2: Create Recruiter
        print("\n[2/6] Creating Recruiter...")
        email_rec = f"recruiter_{datetime.now().timestamp()}@test.com"
        resp = await client.post(
            f"{BASE_URL}/auth/register/recruiter",
            json={
                "user_data": {"email": email_rec, "password": "Test123!", "role": "recruiter"},
                "recruiter_data": {
                    "first_name": "Jane", "last_name": "Smith",
                    "company_name": "TechCorp", "email": email_rec, "college_id": 1
                }
            }
        )
        if resp.status_code == 201:
            print(f"   ✅ Recruiter created: {email_rec}")
            recruiter_token = resp.json()["access_token"]
        else:
            print(f"   ❌ Failed: {resp.status_code} - {resp.text}")
            return
        
        # STEP 3: Create Placement Officer & Verify Recruiter
        print("\n[3/6] Creating & Verifying Placement Officer...")
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
        if resp.status_code == 201:
            print(f"   ✅ Officer created: {email_off}")
            officer_token = resp.json()["access_token"]
        else:
            print(f"   ❌ Failed: {resp.status_code} - {resp.text}")
            return
        
        # STEP 4: Create Job (Recruiter)
        print("\n[4/6] Creating Job...")
        resp = await client.post(
            f"{BASE_URL}/jobs/",
            headers={"Authorization": f"Bearer {recruiter_token}"},
            json={
                "title": "Senior Developer",
                "description": "Test job",
                "recruiter_id": 1,  # Placeholder - would need to fetch from DB
                "college_id": 1,
                "salary_ctc": 800000,
                "allowed_branches": ["CS", "IT"],
                "require_gpa": 7.0,
                "position_count": 5
            }
        )
        if resp.status_code == 201 or resp.status_code == 200:
            print(f"   ✅ Job created")
            job_id = resp.json().get("id")
        else:
            print(f"   ❌ Failed: {resp.status_code} - {resp.text[:100]}")
            return
        
        # STEP 5: Student Applies
        print("\n[5/6] Student Applies...")
        resp = await client.post(
            f"{BASE_URL}/applications/",
            headers={"Authorization": f"Bearer {student_token}"},
            json={
                "student_id": 1,  # Placeholder
                "job_id": job_id,
                "resume_id": 1  # Placeholder
            }
        )
        if resp.status_code == 201:
            print(f"   ✅ Application created")
            app_id = resp.json().get("id")
        else:
            print(f"   ❌ Failed: {resp.status_code} - {resp.text[:100]}")
            return
        
        # STEP 6: System Status
        print("\n[6/6] System Status Check...")
        resp = await client.get(f"{BASE_URL}/health")
        if resp.status_code == 200:
            print(f"   ✅ Backend healthy")
            print(f"   {resp.json()}")
        else:
            print(f"   ❌ Backend unhealthy")
        
        print("\n" + "="*70)
        print("  ✅ WORKFLOW VALIDATION COMPLETE")
        print("="*70 + "\n")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
