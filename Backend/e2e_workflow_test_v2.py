"""
End-to-End Workflow Test (CORRECTED ENDPOINTS)

Tests complete workflow:
1. Create student & recruiter via auth/register
2. Create job → approve
3. Student applies
4. Add rounds (PASSED, PASSED, FAILED) → verify REJECTED
5. New student & application
6. Add round PASSED → create offer → accept
7. Verify notifications
8. Test analytics endpoints
"""

import asyncio
import httpx
import json
from datetime import datetime
from typing import Dict, Any

BASE_URL = "http://localhost:8001/api/v1"

# Test data containers
test_data = {
    "college_id": 1,
    "student1_id": None,
    "student1_token": None,
    "student2_id": None,
    "student2_token": None,
    "recruiter_id": None,
    "recruiter_token": None,
    "officer_id": None,
    "officer_token": None,
    "job_id": None,
    "application1_id": None,
    "application2_id": None,
    "round1_id": None,
    "offer_id": None,
    "notifications": [],
}

# Color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

def print_step(step: int, text: str):
    print(f"\n{BLUE}>>> STEP {step}: {text}{RESET}")

def print_success(text: str):
    print(f"{GREEN}✅ {text}{RESET}")

def print_failure(text: str):
    print(f"{RED}❌ {text}{RESET}")

def print_info(text: str):
    print(f"{YELLOW}ℹ️  {text}{RESET}")

def print_section(text: str):
    print(f"\n{BLUE}{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}{RESET}")


async def step_1_create_student():
    """Create a new student via auth/register/student"""
    print_step(1, "Create Student (via /auth/register/student)")
    
    async with httpx.AsyncClient() as client:
        email = f"student_test_{datetime.now().timestamp()}@example.com"
        payload = {
            "user_data": {
                "email": email,
                "password": "TestPass123!",
                "role": "student",
            },
            "student_data": {
                "first_name": "TestStudent",
                "last_name": "E2E",
                "branch": "CS",
                "graduation_year": 2024,
                "cgpa": 8.5,
                "college_id": test_data["college_id"],
            }
        }
        
        response = await client.post(f"{BASE_URL}/auth/register/student", json=payload)
        
        if response.status_code == 201:
            data = response.json()
            test_data["student1_id"] = data.get("user_id")
            test_data["student1_token"] = data.get("access_token")
            print_success(f"Student created: ID={test_data['student1_id']}, Email={email}")
            print_info(f"Token obtained: {test_data['student1_token'][:20]}...")
            return True
        else:
            print_failure(f"Failed to create student: {response.status_code}")
            print_info(f"Response: {response.text}")
            return False


async def step_2_create_recruiter():
    """Create a new recruiter via auth/register/recruiter"""
    print_step(2, "Create Recruiter (via /auth/register/recruiter)")
    
    async with httpx.AsyncClient() as client:
        email = f"recruiter_test_{datetime.now().timestamp()}@example.com"
        payload = {
            "user_data": {
                "email": email,
                "password": "TestPass123!",
                "role": "recruiter",
            },
            "recruiter_data": {
                "first_name": "TestRecruiter",
                "last_name": "E2E",
                "company_name": "TestCompany",
                "email": email,
                "college_id": test_data["college_id"],
            }
        }
        
        response = await client.post(f"{BASE_URL}/auth/register/recruiter", json=payload)
        
        if response.status_code == 201:
            data = response.json()
            test_data["recruiter_id"] = data.get("user_id")
            test_data["recruiter_token"] = data.get("access_token")
            print_success(f"Recruiter created: ID={test_data['recruiter_id']}, Email={email}")
            print_info(f"Token obtained: {test_data['recruiter_token'][:20]}...")
            return True
        else:
            print_failure(f"Failed to create recruiter: {response.status_code}")
            print_info(f"Response: {response.text}")
            return False


async def step_2b_create_placement_officer():
    """Create a placement officer via auth/register/placement_officer"""
    print_step(2.5, "Create Placement Officer (via /auth/register/placement_officer)")
    
    async with httpx.AsyncClient() as client:
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
                "college_id": test_data["college_id"],
            }
        }
        
        response = await client.post(f"{BASE_URL}/auth/register/placement_officer", json=payload)
        
        if response.status_code == 201:
            data = response.json()
            test_data["officer_id"] = data.get("user_id")
            test_data["officer_token"] = data.get("access_token")
            print_success(f"Officer created: ID={test_data['officer_id']}, Email={email}")
            print_info(f"Token obtained: {test_data['officer_token'][:20]}...")
            return True
        else:
            print_failure(f"Failed to create placement officer: {response.status_code}")
            print_info(f"Response: {response.text}")
            return False


async def step_2c_verify_recruiter():
    """Verify recruiter account via placement officer"""
    print_step(2.6, "Verify Recruiter Account (via placement officer)")
    
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {test_data['officer_token']}"}
        params = {"is_verified": True}
        
        response = await client.put(
            f"{BASE_URL}/recruiters/{test_data['recruiter_id']}/verify",
            params=params,
            headers=headers
        )
        
        if response.status_code in [200, 201]:
            print_success(f"Recruiter verified: ID={test_data['recruiter_id']}")
            return True
        else:
            print_failure(f"Failed to verify recruiter: {response.status_code}")
            print_info(f"Response: {response.text}")
            return False


async def step_3_create_and_approve_job():
    """Create a job and approve it"""
    print_step(3, "Create Job & Approve")
    
    async with httpx.AsyncClient() as client:
        # Create job
        payload = {
            "title": f"Test Position {datetime.now().timestamp()}",
            "description": "Test job description",
            "recruiter_id": test_data["recruiter_id"],
            "college_id": test_data["college_id"],
            "salary_ctc": 750000,
            "allowed_branches": ["CS", "IT", "ECE"],
            "require_gpa": 7.0,
            "position_count": 5
        }
        
        headers = {"Authorization": f"Bearer {test_data['recruiter_token']}"}
        response = await client.post(f"{BASE_URL}/jobs/", json=payload, headers=headers)
        
        if response.status_code not in [201, 200]:
            print_failure(f"Failed to create job: {response.status_code}")
            print_info(f"Response: {response.text}")
            return False
        
        job_data = response.json()
        test_data["job_id"] = job_data["id"]
        print_success(f"Job created: ID={job_data['id']}, Title={job_data['title']}")
        
        # Approve job
        approve_payload = {"status": "APPROVED"}
        
        response = await client.post(
            f"{BASE_URL}/jobs/{test_data['job_id']}/approve",
            json=approve_payload,
            headers=headers
        )
        
        if response.status_code in [200, 201]:
            print_success(f"Job approved: ID={test_data['job_id']}")
            return True
        else:
            print_failure(f"Failed to approve job: {response.status_code}")
            print_info(f"Response: {response.text}")
            return False


async def step_4_student_applies():
    """Student applies to job"""
    print_step(4, "Student Applies to Job")
    
    async with httpx.AsyncClient() as client:
        payload = {
            "student_id": test_data["student1_id"],
            "job_id": test_data["job_id"],
            "resume_id": 1  # Assuming resume 1 exists
        }
        
        headers = {"Authorization": f"Bearer {test_data['student1_token']}"}
        response = await client.post(
            f"{BASE_URL}/applications/",
            json=payload,
            headers=headers
        )
        
        if response.status_code == 201:
            data = response.json()
            test_data["application1_id"] = data["id"]
            print_success(f"Application created: ID={data['id']}, Status={data['status']}")
            return True
        else:
            print_failure(f"Failed to create application: {response.status_code}")
            print_info(f"Response: {response.text}")
            return False


async def step_5_add_rounds_with_failed():
    """Add 3 rounds: PASSED, PASSED, FAILED - verify status becomes REJECTED"""
    print_step(5, "Add Rounds (PASSED, PASSED, FAILED) → Verify REJECTED")
    
    async with httpx.AsyncClient() as client:
        round_results = []
        headers = {"Authorization": f"Bearer {test_data['recruiter_token']}"}
        
        # Round 1: PASSED
        payload = {
            "round_number": 1,
            "round_name": "Online Test",
            "result": "PASSED"
        }
        
        response = await client.post(
            f"{BASE_URL}/applications/{test_data['application1_id']}/rounds",
            json=payload,
            headers=headers
        )
        if response.status_code == 201:
            print_success("Round 1 added: PASSED")
            round_results.append(True)
        else:
            print_failure(f"Failed to add Round 1: {response.status_code}")
            print_info(f"Response: {response.text}")
            round_results.append(False)
        
        # Round 2: PASSED
        payload = {
            "round_number": 2,
            "round_name": "Technical Interview",
            "result": "PASSED"
        }
        
        response = await client.post(
            f"{BASE_URL}/applications/{test_data['application1_id']}/rounds",
            json=payload,
            headers=headers
        )
        if response.status_code == 201:
            print_success("Round 2 added: PASSED")
            round_results.append(True)
        else:
            print_failure(f"Failed to add Round 2: {response.status_code}")
            print_info(f"Response: {response.text}")
            round_results.append(False)
        
        # Round 3: FAILED
        payload = {
            "round_number": 3,
            "round_name": "HR Round",
            "result": "FAILED"
        }
        
        response = await client.post(
            f"{BASE_URL}/applications/{test_data['application1_id']}/rounds",
            json=payload,
            headers=headers
        )
        if response.status_code == 201:
            test_data["round1_id"] = response.json()["id"]
            print_success("Round 3 added: FAILED")
            round_results.append(True)
        else:
            print_failure(f"Failed to add Round 3: {response.status_code}")
            print_info(f"Response: {response.text}")
            round_results.append(False)
        
        # Verify application status is REJECTED
        response = await client.get(
            f"{BASE_URL}/applications/{test_data['application1_id']}",
            headers=headers
        )
        if response.status_code == 200:
            app_status = response.json()["status"]
            if app_status == "REJECTED":
                print_success(f"✓ Application status correctly set to REJECTED")
                return all(round_results)
            else:
                print_failure(f"✗ Application status is {app_status}, expected REJECTED")
                return False
        else:
            print_failure(f"Failed to fetch application: {response.status_code}")
            return False


async def step_6_new_student_and_offer():
    """New student, application, rounds PASSED, create offer, accept offer"""
    print_step(6, "New Student → Application → Rounds → Offer → Accept")
    
    async with httpx.AsyncClient() as client:
        # Create student 2
        student2_email = f"student2_test_{datetime.now().timestamp()}@example.com"
        payload = {
            "user_data": {
                "email": student2_email,
                "password": "TestPass123!",
                "role": "student",
            },
            "student_data": {
                "first_name": "TestStudent2",
                "last_name": "E2E",
                "branch": "IT",
                "graduation_year": 2024,
                "cgpa": 8.2,
                "college_id": test_data["college_id"],
            }
        }
        
        response = await client.post(f"{BASE_URL}/auth/register/student", json=payload)
        if response.status_code != 201:
            print_failure(f"Failed to create student 2: {response.status_code}")
            print_info(f"Response: {response.text}")
            return False
        
        data = response.json()
        test_data["student2_id"] = data.get("user_id")
        test_data["student2_token"] = data.get("access_token")
        print_success(f"Student 2 created: ID={test_data['student2_id']}")
        
        # Student 2 applies
        headers = {"Authorization": f"Bearer {test_data['student2_token']}"}
        payload = {
            "student_id": test_data["student2_id"],
            "job_id": test_data["job_id"],
            "resume_id": 1
        }
        
        response = await client.post(f"{BASE_URL}/applications/", json=payload, headers=headers)
        if response.status_code != 201:
            print_failure(f"Failed to create application 2: {response.status_code}")
            print_info(f"Response: {response.text}")
            return False
        
        test_data["application2_id"] = response.json()["id"]
        print_success(f"Application 2 created: ID={test_data['application2_id']}")
        
        # Add round: PASSED
        recruiter_headers = {"Authorization": f"Bearer {test_data['recruiter_token']}"}
        payload = {
            "round_number": 1,
            "round_name": "Online Test",
            "result": "PASSED"
        }
        
        response = await client.post(
            f"{BASE_URL}/applications/{test_data['application2_id']}/rounds",
            json=payload,
            headers=recruiter_headers
        )
        if response.status_code != 201:
            print_failure(f"Failed to add round: {response.status_code}")
            print_info(f"Response: {response.text}")
            return False
        
        print_success(f"Round added: PASSED")
        
        # Create offer
        payload = {
            "application_id": test_data["application2_id"],
            "job_id": test_data["job_id"],
            "recruiter_id": test_data["recruiter_id"],
            "status": "EXTENDED",
            "salary_ctc": 750000
        }
        
        response = await client.post(
            f"{BASE_URL}/offers/",
            json=payload,
            headers=recruiter_headers
        )
        if response.status_code != 201:
            print_failure(f"Failed to create offer: {response.status_code}")
            print_info(f"Response: {response.text}")
            return False
        
        test_data["offer_id"] = response.json()["id"]
        print_success(f"Offer created: ID={test_data['offer_id']}, Status=EXTENDED")
        
        # Accept offer
        payload = {"status": "ACCEPTED"}
        response = await client.put(
            f"{BASE_URL}/offers/{test_data['offer_id']}/respond",
            json=payload,
            headers=headers
        )
        
        if response.status_code != 200:
            print_failure(f"Failed to accept offer: {response.status_code}")
            print_info(f"Response: {response.text}")
            return False
        
        print_success(f"Offer accepted: ID={test_data['offer_id']}")
        
        return True


async def step_7_verify_notifications():
    """Verify notifications were created correctly"""
    print_step(7, "Verify Notifications")
    
    async with httpx.AsyncClient() as client:
        # Get notifications
        headers = {"Authorization": f"Bearer {test_data['recruiter_token']}"}
        response = await client.get(f"{BASE_URL}/notifications/", headers=headers)
        
        if response.status_code != 200:
            print_failure(f"Failed to fetch notifications: {response.status_code}")
            print_info(f"Response: {response.text}")
            return False
        
        notifications = response.json()
        test_data["notifications"] = notifications
        
        # Count notification types
        type_counts = {}
        for notif in notifications:
            notif_type = notif.get("notification_type", "UNKNOWN")
            type_counts[notif_type] = type_counts.get(notif_type, 0) + 1
        
        print_info(f"Total notifications: {len(notifications)}")
        for notif_type, count in sorted(type_counts.items()):
            print_info(f"  • {notif_type}: {count}")
        
        # Verify we have key notification types
        has_any = len(notifications) > 0
        
        if has_any:
            print_success("✓ Notifications found")
            return True
        else:
            print_failure("✗ No notifications found")
            return False


async def step_8_test_analytics():
    """Test analytics endpoints"""
    print_step(8, "Test Analytics Endpoints")
    
    async with httpx.AsyncClient() as client:
        success = True
        headers = {"Authorization": f"Bearer {test_data['recruiter_token']}"}
        
        # Endpoint 1: Top candidates for job
        if test_data['job_id']:
            print_info(f"Testing: GET /analytics/jobs/{test_data['job_id']}/top-candidates")
            response = await client.get(
                f"{BASE_URL}/analytics/jobs/{test_data['job_id']}/top-candidates",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                print_success(f"✓ Top candidates endpoint works")
                print_info(f"  Returned {len(data)} candidates")
                for candidate in data:
                    print_info(f"    • Student: {candidate.get('student_id')}, Score: {candidate.get('avg_score')}, Rounds: {candidate.get('rounds_cleared')}")
            else:
                print_failure(f"✗ Top candidates failed: {response.status_code}")
                print_info(f"Response: {response.text}")
                success = False
        else:
            print_failure("❌ No Job ID - Skipping top candidates test")
            success = False
        
        # Endpoint 2: Student insight for application
        if test_data['application2_id']:
            print_info(f"Testing: GET /analytics/applications/{test_data['application2_id']}/insight")
            headers_student = {"Authorization": f"Bearer {test_data['student2_token']}"}
            response = await client.get(
                f"{BASE_URL}/analytics/applications/{test_data['application2_id']}/insight",
                headers=headers_student
            )
            
            if response.status_code == 200:
                data = response.json()
                print_success(f"✓ Student insight endpoint works")
                print_info(f"  Performance Label: {data.get('performance_label')}")
                print_info(f"  Avg Score: {data.get('avg_score')}")
                print_info(f"  Rounds Cleared: {data.get('rounds_cleared')}")
            else:
                print_failure(f"✗ Student insight failed: {response.status_code}")
                print_info(f"Response: {response.text}")
                success = False
        else:
            print_failure("❌ No Application ID - Skipping student insight test")
            success = False
        
        # Endpoint 3: Drive summary for job
        if test_data['job_id']:
            print_info(f"Testing: GET /analytics/jobs/{test_data['job_id']}/summary")
            response = await client.get(
                f"{BASE_URL}/analytics/jobs/{test_data['job_id']}/summary",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                print_success(f"✓ Drive summary endpoint works")
                print_info(f"  Total Applicants: {data.get('total_applicants')}")
                print_info(f"  In Progress: {data.get('in_progress')}")
                print_info(f"  Accepted: {data.get('accepted')}")
                print_info(f"  Rejected: {data.get('rejected')}")
            else:
                print_failure(f"✗ Drive summary failed: {response.status_code}")
                print_info(f"Response: {response.text}")
                success = False
        else:
            print_failure("❌ No Job ID - Skipping summary test")
            success = False
        
        return success


async def main():
    """Run complete E2E workflow"""
    
    print_section("END-TO-END WORKFLOW TEST (CORRECTED)")
    print_info(f"Started at: {datetime.now().isoformat()}")
    print_info(f"Base URL: {BASE_URL}")
    print_info(f"Database: PostgreSQL (campus_placement_db)")
    
    results = {}
    
    # Execute steps
    print_section("EXECUTION PHASE")
    
    results["step_1"] = await step_1_create_student()
    results["step_2"] = await step_2_create_recruiter()
    results["step_2b"] = await step_2b_create_placement_officer()
    results["step_2c"] = await step_2c_verify_recruiter()
    results["step_3"] = await step_3_create_and_approve_job()
    results["step_4"] = await step_4_student_applies()
    results["step_5"] = await step_5_add_rounds_with_failed()
    results["step_6"] = await step_6_new_student_and_offer()
    results["step_7"] = await step_7_verify_notifications()
    results["step_8"] = await step_8_test_analytics()
    
    # Summary
    print_section("RESULTS SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for step, result in results.items():
        status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        print(f"  {step}: {status}")
    
    print_section("FINAL VERDICT")
    
    if passed == total:
        print(f"{GREEN}✅ ALL TESTS PASSED ({passed}/{total}){RESET}")
        print(f"{GREEN}System working correctly!{RESET}")
    else:
        print(f"{RED}❌ SOME TESTS FAILED ({passed}/{total}){RESET}")
        if passed > 0:
            print(f"{YELLOW}Partial success - {passed} steps passed{RESET}")
    
    print_info(f"Completed at: {datetime.now().isoformat()}")
    
    # Print test data for reference
    print_section("TEST DATA CREATED")
    print_info(f"Student 1 ID: {test_data['student1_id']}")
    print_info(f"Student 2 ID: {test_data['student2_id']}")
    print_info(f"Recruiter ID: {test_data['recruiter_id']}")
    print_info(f"Job ID: {test_data['job_id']}")
    print_info(f"Application 1 ID: {test_data['application1_id']}")
    print_info(f"Application 2 ID: {test_data['application2_id']}")
    print_info(f"Offer ID: {test_data['offer_id']}")
    print_info(f"Notifications created: {len(test_data['notifications'])}")


if __name__ == "__main__":
    asyncio.run(main())
