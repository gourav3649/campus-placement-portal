"""
End-to-End Workflow Test

Tests complete workflow:
1. Create student & recruiter
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

BASE_URL = "http://localhost:8000/api/v1"

# Test data containers
test_data = {
    "college_id": 1,
    "student1_id": None,
    "student2_id": None,
    "recruiter_id": None,
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
    """Create a new student"""
    print_step(1, "Create Student")
    
    async with httpx.AsyncClient() as client:
        payload = {
            "email": f"student_test_{datetime.now().timestamp()}@example.com",
            "first_name": "TestStudent",
            "last_name": "E2E",
            "password": "TestPass123!",
            "college_id": test_data["college_id"],
            "enrollment_date": "2023-09-01"
        }
        
        response = await client.post(f"{BASE_URL}/students/create", json=payload)
        
        if response.status_code == 201:
            data = response.json()
            test_data["student1_id"] = data["id"]
            print_success(f"Student created: ID={data['id']}, Email={data['email']}")
            return True
        else:
            print_failure(f"Failed to create student: {response.status_code}")
            print_info(f"Response: {response.text}")
            return False


async def step_2_create_recruiter():
    """Create a new recruiter"""
    print_step(2, "Create Recruiter")
    
    async with httpx.AsyncClient() as client:
        payload = {
            "email": f"recruiter_test_{datetime.now().timestamp()}@example.com",
            "first_name": "TestRecruiter",
            "last_name": "E2E",
            "password": "TestPass123!",
            "college_id": test_data["college_id"],
            "company_name": "TestCompany"
        }
        
        response = await client.post(f"{BASE_URL}/recruiters/create", json=payload)
        
        if response.status_code == 201:
            data = response.json()
            test_data["recruiter_id"] = data["id"]
            print_success(f"Recruiter created: ID={data['id']}, Email={data['email']}")
            return True
        else:
            print_failure(f"Failed to create recruiter: {response.status_code}")
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
        
        response = await client.post(f"{BASE_URL}/jobs/create", json=payload)
        
        if response.status_code != 201:
            print_failure(f"Failed to create job: {response.status_code}")
            print_info(f"Response: {response.text}")
            return False
        
        job_data = response.json()
        test_data["job_id"] = job_data["id"]
        print_success(f"Job created: ID={job_data['id']}, Title={job_data['title']}")
        
        # Approve job (as recruiter)
        headers = {"Authorization": f"Bearer recruiter_{test_data['recruiter_id']}"}
        approve_payload = {"status": "APPROVED"}
        
        response = await client.put(
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
        
        response = await client.post(
            f"{BASE_URL}/applications/create",
            json=payload
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
        
        # Round 1: PASSED
        payload = {
            "application_id": test_data["application1_id"],
            "round_number": 1,
            "round_name": "Online Test",
            "result": "PASSED"
        }
        
        response = await client.post(f"{BASE_URL}/rounds/add", json=payload)
        if response.status_code == 201:
            print_success("Round 1 added: PASSED")
            round_results.append(True)
        else:
            print_failure(f"Failed to add Round 1: {response.status_code}")
            round_results.append(False)
        
        # Round 2: PASSED
        payload = {
            "application_id": test_data["application1_id"],
            "round_number": 2,
            "round_name": "Technical Interview",
            "result": "PASSED"
        }
        
        response = await client.post(f"{BASE_URL}/rounds/add", json=payload)
        if response.status_code == 201:
            print_success("Round 2 added: PASSED")
            round_results.append(True)
        else:
            print_failure(f"Failed to add Round 2: {response.status_code}")
            round_results.append(False)
        
        # Round 3: FAILED
        payload = {
            "application_id": test_data["application1_id"],
            "round_number": 3,
            "round_name": "HR Round",
            "result": "FAILED"
        }
        
        response = await client.post(f"{BASE_URL}/rounds/add", json=payload)
        if response.status_code == 201:
            test_data["round1_id"] = response.json()["id"]
            print_success("Round 3 added: FAILED")
            round_results.append(True)
        else:
            print_failure(f"Failed to add Round 3: {response.status_code}")
            round_results.append(False)
        
        # Verify application status is REJECTED
        response = await client.get(f"{BASE_URL}/applications/{test_data['application1_id']}")
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
        payload = {
            "email": f"student2_test_{datetime.now().timestamp()}@example.com",
            "first_name": "TestStudent2",
            "last_name": "E2E",
            "password": "TestPass123!",
            "college_id": test_data["college_id"],
            "enrollment_date": "2023-09-01"
        }
        
        response = await client.post(f"{BASE_URL}/students/create", json=payload)
        if response.status_code != 201:
            print_failure(f"Failed to create student 2: {response.status_code}")
            return False
        
        test_data["student2_id"] = response.json()["id"]
        print_success(f"Student 2 created: ID={test_data['student2_id']}")
        
        # Student 2 applies
        payload = {
            "student_id": test_data["student2_id"],
            "job_id": test_data["job_id"],
            "resume_id": 1
        }
        
        response = await client.post(f"{BASE_URL}/applications/create", json=payload)
        if response.status_code != 201:
            print_failure(f"Failed to create application 2: {response.status_code}")
            return False
        
        test_data["application2_id"] = response.json()["id"]
        print_success(f"Application 2 created: ID={test_data['application2_id']}")
        
        # Add round: PASSED
        payload = {
            "application_id": test_data["application2_id"],
            "round_number": 1,
            "round_name": "Online Test",
            "result": "PASSED"
        }
        
        response = await client.post(f"{BASE_URL}/rounds/add", json=payload)
        if response.status_code != 201:
            print_failure(f"Failed to add round: {response.status_code}")
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
        
        response = await client.post(f"{BASE_URL}/offers/create", json=payload)
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
            json=payload
        )
        
        if response.status_code != 200:
            print_failure(f"Failed to accept offer: {response.status_code}")
            print_info(f"Response: {response.text}")
            return False
        
        print_success(f"Offer accepted: ID={test_data['offer_id']}")
        
        # Verify student marked placed
        response = await client.get(f"{BASE_URL}/students/{test_data['student2_id']}")
        if response.status_code == 200:
            student_data = response.json()
            if student_data.get("is_placed"):
                print_success(f"✓ Student 2 marked as placed")
            else:
                print_failure(f"✗ Student 2 not marked as placed")
                return False
        else:
            print_failure(f"Failed to fetch student 2: {response.status_code}")
            return False
        
        # Verify application status is ACCEPTED
        response = await client.get(f"{BASE_URL}/applications/{test_data['application2_id']}")
        if response.status_code == 200:
            app_status = response.json()["status"]
            if app_status == "ACCEPTED":
                print_success(f"✓ Application 2 status is ACCEPTED")
            else:
                print_failure(f"✗ Application 2 status is {app_status}, expected ACCEPTED")
                return False
        else:
            print_failure(f"Failed to fetch application 2: {response.status_code}")
            return False
        
        return True


async def step_7_verify_notifications():
    """Verify notifications were created correctly"""
    print_step(7, "Verify Notifications")
    
    async with httpx.AsyncClient() as client:
        # Get notifications
        response = await client.get(f"{BASE_URL}/notifications")
        
        if response.status_code != 200:
            print_failure(f"Failed to fetch notifications: {response.status_code}")
            return False
        
        notifications = response.json()
        test_data["notifications"] = notifications
        
        # Count notification types
        type_counts = {}
        for notif in notifications:
            notif_type = notif.get("notification_type", "UNKNOWN")
            type_counts[notif_type] = type_counts.get(notif_type, 0) + 1
        
        print_info(f"Total notifications: {len(notifications)}")
        for notif_type, count in type_counts.items():
            print_info(f"  • {notif_type}: {count}")
        
        # Verify we have key notification types
        has_application = any(n.get("notification_type") == "APPLICATION_SUBMITTED" for n in notifications)
        has_round = any(n.get("notification_type") == "ROUND_RESULT" for n in notifications)
        has_offer = any(n.get("notification_type") in ["OFFER_EXTENDED", "OFFER_ACCEPTED"] for n in notifications)
        
        success = True
        if has_application:
            print_success("✓ APPLICATION_SUBMITTED notifications found")
        else:
            print_failure("✗ No APPLICATION_SUBMITTED notifications")
            success = False
        
        if has_round:
            print_success("✓ ROUND_RESULT notifications found")
        else:
            print_failure("✗ No ROUND_RESULT notifications")
            success = False
        
        if has_offer:
            print_success("✓ OFFER notifications found")
        else:
            print_failure("✗ No OFFER notifications")
            success = False
        
        return success


async def step_8_test_analytics():
    """Test analytics endpoints"""
    print_step(8, "Test Analytics Endpoints")
    
    async with httpx.AsyncClient() as client:
        success = True
        
        # Endpoint 1: Top candidates
        print_info("Testing: GET /analytics/top-candidates")
        response = await client.get(f"{BASE_URL}/analytics/top-candidates?job_id={test_data['job_id']}")
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"✓ Top candidates endpoint works")
            print_info(f"  Returned {len(data)} candidates")
            for candidate in data:
                print_info(f"    • ID: {candidate.get('student_id')}, Score: {candidate.get('avg_score')}, Rounds: {candidate.get('rounds_cleared')}")
        else:
            print_failure(f"✗ Top candidates failed: {response.status_code}")
            success = False
        
        # Endpoint 2: Student insight
        print_info("Testing: GET /analytics/insight")
        response = await client.get(f"{BASE_URL}/analytics/insight?student_id={test_data['student2_id']}")
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"✓ Student insight endpoint works")
            print_info(f"  Performance Label: {data.get('performance_label')}")
            print_info(f"  Avg Score: {data.get('avg_score')}")
            print_info(f"  Rounds Cleared: {data.get('rounds_cleared')}")
        else:
            print_failure(f"✗ Student insight failed: {response.status_code}")
            success = False
        
        # Endpoint 3: Drive summary
        print_info("Testing: GET /analytics/drive-summary")
        response = await client.get(f"{BASE_URL}/analytics/drive-summary?job_id={test_data['job_id']}")
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"✓ Drive summary endpoint works")
            print_info(f"  Total Applicants: {data.get('total_applicants')}")
            print_info(f"  In Progress: {data.get('in_progress')}")
            print_info(f"  Accepted: {data.get('accepted')}")
            print_info(f"  Rejected: {data.get('rejected')}")
        else:
            print_failure(f"✗ Drive summary failed: {response.status_code}")
            success = False
        
        return success


async def main():
    """Run complete E2E workflow"""
    
    print_section("END-TO-END WORKFLOW TEST")
    print_info(f"Started at: {datetime.now().isoformat()}")
    print_info(f"Base URL: {BASE_URL}")
    print_info(f"Database: PostgreSQL (campus_placement_db)")
    
    results = {}
    
    # Execute steps
    print_section("EXECUTION PHASE")
    
    results["step_1"] = await step_1_create_student()
    results["step_2"] = await step_2_create_recruiter()
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
        print(f"{RED}System requires attention{RESET}")
    
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
