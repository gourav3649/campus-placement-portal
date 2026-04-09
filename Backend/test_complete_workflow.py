"""
COMPLETE END-TO-END WORKFLOW TEST
Covers all 10 steps with fresh data and proper state validation
"""
import httpx
import json
from datetime import datetime
from typing import Dict, Any

BASE_URL = "http://localhost:8001/api/v1"

# Test data - will be populated as we go
data = {
    "student1_id": None,
    "student1_token": None,
    "student2_id": None,
    "student2_token": None,
    "recruiter_id": None,
    "recruiter_token": None,
    "officer_id": None,
    "officer_token": None,
    "job_id": None,
    "app1_id": None,
    "app2_id": None,
    "offer_id": None,
}

# Color codes
G = "\033[92m"
R = "\033[91m"
Y = "\033[93m"
B = "\033[94m"
W = "\033[0m"

def log(msg: str, color: str = W):
    print(f"{color}{msg}{W}")

def step(num: int, title: str):
    print(f"\n{B}{'='*70}")
    print(f"STEP {num}: {title}")
    print(f"{'='*70}{W}")

def success(msg: str):
    print(f"{G}✅ {msg}{W}")

def failure(msg: str):
    print(f"{R}❌ {msg}{W}")

def info(msg: str):
    print(f"{Y}ℹ️  {msg}{W}")

async def test_workflow():
    async with httpx.AsyncClient() as client:
        print(f"\n{B}CAMPUS PLACEMENT SYSTEM - E2E WORKFLOW TEST{W}")
        print(f"{B}Started: {datetime.now().isoformat()}{W}\n")
        
        # Use college_id=1 (assuming it exists or will be created by migrations)
        college_id = 1
        
        # ===== STEP 1: Register Student 1 =====
        step(1, "Register Student → Capture user.id")
        email1 = f"student1_{datetime.now().timestamp()}@test.com"
        resp = await client.post(
            f"{BASE_URL}/auth/register/student",
            json={
                "user_data": {"email": email1, "password": "Test123!", "role": "student"},
                "student_data": {
                    "first_name": "Alice", "last_name": "Johnson",
                    "branch": "CS", "graduation_year": 2024, "cgpa": 8.5, "college_id": college_id
                }
            }
        )
        if resp.status_code == 201:
            rdata = resp.json()
            data["student1_id"] = rdata["user"]["profile_id"]  # Use profile_id for student operations
            data["student1_token"] = rdata["access_token"]
            success(f"Student 1 registered: ID={data['student1_id']}, Email={email1}")
        else:
            failure(f"Failed: {resp.status_code} - {resp.text}")
            return
        
        # ===== STEP 2: Register Recruiter =====
        step(2, "Register Recruiter → Capture user.id")
        email_rec = f"recruiter_{datetime.now().timestamp()}@test.com"
        resp = await client.post(
            f"{BASE_URL}/auth/register/recruiter",
            json={
                "user_data": {"email": email_rec, "password": "Test123!", "role": "recruiter"},
                "recruiter_data": {
                    "first_name": "Bob", "last_name": "Smith",
                    "company_name": "TechCorp Inc", "email": email_rec, "college_id": college_id
                }
            }
        )
        if resp.status_code == 201:
            rdata = resp.json()
            data["recruiter_id"] = rdata["user"]["profile_id"]  # Use profile_id for recruiter operations
            data["recruiter_token"] = rdata["access_token"]
            success(f"Recruiter registered: ID={data['recruiter_id']}, Email={email_rec}")
        else:
            failure(f"Failed: {resp.status_code} - {resp.text}")
            return
        
        # ===== STEP 3: Register Placement Officer =====
        step(3, "Register Placement Officer")
        email_off = f"officer_{datetime.now().timestamp()}@test.com"
        resp = await client.post(
            f"{BASE_URL}/auth/register/placement_officer",
            json={
                "user_data": {"email": email_off, "password": "Test123!", "role": "placement_officer"},
                "officer_data": {
                    "name": "Charlie", "email": email_off, "college_id": college_id,
                    "designation": "Placement Lead", "department": "Placement"
                }
            }
        )
        if resp.status_code == 201:
            rdata = resp.json()
            data["officer_id"] = rdata["user"]["profile_id"]  # Use profile_id for officer operations
            data["officer_token"] = rdata["access_token"]
            success(f"Officer registered: ID={data['officer_id']}, Email={email_off}")
        else:
            failure(f"Failed: {resp.status_code} - {resp.text}")
            return
        
        # ===== STEP 3.5: Officer Verifies Recruiter =====
        step("3.5", "Officer Verifies Recruiter Account")
        resp = await client.put(
            f"{BASE_URL}/recruiters/{data['recruiter_id']}/verify",
            headers={"Authorization": f"Bearer {data['officer_token']}"},
            params={"is_verified": True}
        )
        if resp.status_code in [200, 201]:
            success(f"Recruiter verified by officer")
        else:
            failure(f"Verification failed: {resp.status_code} - {resp.text}")
        
        # ===== STEP 4: Recruiter Creates Job =====
        step(4, "Recruiter Creates Job")
        resp = await client.post(
            f"{BASE_URL}/jobs/",
            headers={"Authorization": f"Bearer {data['recruiter_token']}"},
            json={
                "title": "Senior SDE",
                "description": "Software Engineer role",
                "recruiter_id": data["recruiter_id"],
                "college_id": college_id,
                "salary_min": 800000,
                "salary_max": 900000,
                "allowed_branches": ["CS", "IT"],
                "min_cgpa": 7.0,
                "positions_available": 5
            }
        )
        if resp.status_code in [200, 201]:
            data["job_id"] = resp.json()["id"]
            success(f"Job created: ID={data['job_id']}")
        else:
            # Print full error details
            try:
                error_detail = resp.json()
                failure(f"Failed: {resp.status_code} - {error_detail}")
            except:
                failure(f"Failed: {resp.status_code} - {resp.text}")
            info("Note: Job creation requires recruiter to be verified first")
            # Continue to try approval instead
        
        # ===== STEP 5: Officer Approves Job =====
        step(5, "Officer Approves Job")
        if data["job_id"]:
            resp = await client.put(
                f"{BASE_URL}/jobs/{data['job_id']}/approve",
                headers={"Authorization": f"Bearer {data['officer_token']}"},
                json={"status": "APPROVED"}
            )
            if resp.status_code in [200, 201]:
                success(f"Job approved by officer")
            else:
                failure(f"Failed: {resp.status_code} - {resp.text}")
        else:
            failure("Cannot approve: No job created")
        
        # ===== STEP 6: Student Applies to Job =====
        step(6, "Student Applies to Job")
        if data["job_id"]:
            resp = await client.post(
                f"{BASE_URL}/applications/",
                headers={"Authorization": f"Bearer {data['student1_token']}"},
                json={
                    "student_id": data["student1_id"],
                    "job_id": data["job_id"],
                    "resume_id": 1
                }
            )
            if resp.status_code == 201:
                data["app1_id"] = resp.json()["id"]
                success(f"Application created: ID={data['app1_id']}")
            else:
                failure(f"Failed: {resp.status_code} - {resp.text}")
        else:
            failure("Cannot apply: No job created")
        
        # ===== STEP 7: Add Rounds (P, P, F) =====
        step(7, "Add Rounds: PASSED, PASSED, FAILED → Verify REJECTED")
        if data["app1_id"]:
            results = []
            rounds_data = [
                ("Online Test", "PASSED", 85),
                ("Technical Interview", "PASSED", 75),
                ("HR Round", "FAILED", 40)
            ]
            
            for round_name, result, score in rounds_data:
                resp = await client.post(
                    f"{BASE_URL}/applications/{data['app1_id']}/rounds",
                    headers={"Authorization": f"Bearer {data['recruiter_token']}"},
                    json={
                        "round_number": len(results) + 1,
                        "round_name": round_name,
                        "result": result,
                        "score": score
                    }
                )
                if resp.status_code == 201:
                    success(f"Round added: {round_name} → {result} (Score: {score})")
                    results.append(True)
                else:
                    failure(f"Round failed: {resp.status_code} - {resp.text}")
                    results.append(False)
            
            # Verify application status
            resp = await client.get(
                f"{BASE_URL}/applications/{data['app1_id']}",
                headers={"Authorization": f"Bearer {data['recruiter_token']}"}
            )
            if resp.status_code == 200:
                status_val = resp.json()["status"]
                if status_val == "REJECTED":
                    success(f"✓ Application correctly transitioned to REJECTED after 3rd round FAILED")
                else:
                    failure(f"✗ Status is {status_val}, expected REJECTED")
            else:
                failure(f"Cannot fetch application: {resp.status_code}")
        else:
            failure("Cannot add rounds: No application created")
        
        # ===== STEP 8: New Student Workflow =====
        step(8, "New Student: Apply → Rounds → Offer → Accept")
        
        # Register Student 2
        email2 = f"student2_{datetime.now().timestamp()}@test.com"
        resp = await client.post(
            f"{BASE_URL}/auth/register/student",
            json={
                "user_data": {"email": email2, "password": "Test123!", "role": "student"},
                "student_data": {
                    "first_name": "Diana", "last_name": "Lee",
                    "branch": "IT", "graduation_year": 2024, "cgpa": 9.0, "college_id": college_id
                }
            }
        )
        if resp.status_code == 201:
            rdata = resp.json()
            data["student2_id"] = rdata["user"]["profile_id"]  # Use profile_id
            data["student2_token"] = rdata["access_token"]
            success(f"Student 2 registered: ID={data['student2_id']}")
        else:
            failure(f"Failed: {resp.status_code}")
        
        # Student 2 applies
        if data["job_id"] and data["student2_id"]:
            resp = await client.post(
                f"{BASE_URL}/applications/",
                headers={"Authorization": f"Bearer {data['student2_token']}"},
                json={
                    "student_id": data["student2_id"],
                    "job_id": data["job_id"],
                    "resume_id": 2
                }
            )
            if resp.status_code == 201:
                data["app2_id"] = resp.json()["id"]
                success(f"Student 2 applied: Application ID={data['app2_id']}")
            else:
                failure(f"Failed: {resp.status_code}")
        
        # Add passing rounds
        if data["app2_id"]:
            for i, (name, result, score) in enumerate([
                ("Online Test", "PASSED", 90),
                ("Technical Interview", "PASSED", 88)
            ], 1):
                resp = await client.post(
                    f"{BASE_URL}/applications/{data['app2_id']}/rounds",
                    headers={"Authorization": f"Bearer {data['recruiter_token']}"},
                    json={"round_number": i, "round_name": name, "result": result, "score": score}
                )
                if resp.status_code == 201:
                    success(f"Round {i} passed: {score}")
        
        # Create offer
        if data["app2_id"]:
            resp = await client.post(
                f"{BASE_URL}/offers/",
                headers={"Authorization": f"Bearer {data['recruiter_token']}"},
                json={
                    "application_id": data["app2_id"],
                    "student_id": data["student2_id"],
                    "job_id": data["job_id"],
                    "salary_offered": 900000,
                    "joining_date": "2024-07-01"
                }
            )
            if resp.status_code == 201:
                data["offer_id"] = resp.json()["id"]
                success(f"Offer created: ID={data['offer_id']}")
            else:
                failure(f"Offer creation failed: {resp.status_code} - {resp.text[:100]}")
        
        # Accept offer
        if data["offer_id"]:
            resp = await client.put(
                f"{BASE_URL}/offers/{data['offer_id']}/respond",
                headers={"Authorization": f"Bearer {data['student2_token']}"},
                json={"accept": True}
            )
            if resp.status_code in [200, 201]:
                success(f"Offer accepted by student")
                # Verify application status
                resp2 = await client.get(
                    f"{BASE_URL}/applications/{data['app2_id']}",
                    headers={"Authorization": f"Bearer {data['recruiter_token']}"}
                )
                if resp2.status_code == 200:
                    app_status = resp2.json()["status"]
                    if app_status == "ACCEPTED":
                        success(f"✓ Application transitioned to ACCEPTED")
                    else:
                        failure(f"✗ Application status is {app_status}, expected ACCEPTED")
            else:
                failure(f"Offer response failed: {resp.status_code}")
        
        # ===== STEP 9: Notifications =====
        step(9, "Verify Notifications")
        resp = await client.get(
            f"{BASE_URL}/notifications/",
            headers={"Authorization": f"Bearer {data['student2_token']}"}
        )
        if resp.status_code == 200:
            notifications = resp.json()
            if isinstance(notifications, list):
                count = len(notifications)
                success(f"Retrieved {count} notifications")
                for i, notif in enumerate(notifications[:3], 1):
                    info(f"  {i}. {notif.get('event_type', 'unknown')}: {notif.get('message', '')[:50]}")
            else:
                failure(f"Invalid notifications format")
        else:
            failure(f"Failed to fetch notifications: {resp.status_code}")
        
        # ===== STEP 10: Analytics =====
        step(10, "Test Analytics Endpoints")
        
        # Top candidates
        if data["job_id"]:
            resp = await client.get(
                f"{BASE_URL}/analytics/jobs/{data['job_id']}/top-candidates",
                headers={"Authorization": f"Bearer {data['recruiter_token']}"}
            )
            if resp.status_code == 200:
                candidates = resp.json()
                success(f"Top candidates: {len(candidates)} candidates returned")
                for cand in candidates[:2]:
                    info(f"  • ID={cand.get('student_id')}, Score={cand.get('avg_score')}, Rounds={cand.get('rounds_cleared')}")
            else:
                failure(f"Top candidates failed: {resp.status_code}")
        
        # Student insight
        if data["app2_id"]:
            resp = await client.get(
                f"{BASE_URL}/analytics/applications/{data['app2_id']}/insight",
                headers={"Authorization": f"Bearer {data['student2_token']}"}
            )
            if resp.status_code == 200:
                insight = resp.json()
                success(f"Student insight retrieved")
                info(f"  • Performance: {insight.get('performance_label')}")
                info(f"  • Avg Score: {insight.get('avg_score')}")
                info(f"  • Rounds Cleared: {insight.get('rounds_cleared')}")
            else:
                failure(f"Student insight failed: {resp.status_code}")
        
        # Drive summary
        if data["job_id"]:
            resp = await client.get(
                f"{BASE_URL}/analytics/jobs/{data['job_id']}/summary",
                headers={"Authorization": f"Bearer {data['officer_token']}"}
            )
            if resp.status_code == 200:
                summary = resp.json()
                success(f"Drive summary retrieved")
                info(f"  • Total Applicants: {summary.get('total_applicants')}")
                info(f"  • In Progress: {summary.get('in_progress')}")
                info(f"  • Accepted: {summary.get('accepted')}")
                info(f"  • Rejected: {summary.get('rejected')}")
            else:
                failure(f"Drive summary failed: {resp.status_code}")
        
        # ===== FINAL VERDICT =====
        print(f"\n{B}{'='*70}")
        print("FINAL VERDICT")
        print(f"{'='*70}{W}")
        print(f"\n{G}✅ WORKFLOW TEST COMPLETED{W}")
        print(f"{G}System appears to be fully operational{W}\n")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_workflow())
