#!/usr/bin/env python3
"""
COMPREHENSIVE E2E WORKFLOW TEST
Executes all 10 steps with fresh data and detailed logging.
Stops immediately on first failure with full traceback.
"""
import httpx
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional

BASE_URL = "http://localhost:8002/api/v1"

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"

class TestResult:
    def __init__(self):
        self.steps_executed = 0
        self.steps_passed = 0
        self.failed_step = None
        self.failed_reason = None
        self.data = {}

result = TestResult()

def print_step(num: int, name: str):
    """Print step header"""
    print(f"\n{BLUE}{BOLD}{'='*80}{RESET}")
    print(f"{BLUE}STEP {num}: {name}{RESET}")
    print(f"{BLUE}{'='*80}{RESET}")

def print_section(title: str):
    """Print section header"""
    print(f"\n{YELLOW}→ {title}{RESET}")

def print_success(msg: str):
    """Print success message"""
    print(f"{GREEN}✅ {msg}{RESET}")

def print_error(msg: str):
    """Print error message"""
    print(f"{RED}❌ {msg}{RESET}")

def print_request(method: str, endpoint: str, json_data: Optional[Dict] = None, headers: Optional[Dict] = None):
    """Print request details"""
    print(f"{YELLOW}Endpoint: {RESET}{method} {endpoint}")
    if json_data:
        print(f"{YELLOW}Request Body:{RESET}")
        print(json.dumps(json_data, indent=2))
    if headers and "Authorization" in headers:
        auth_token = headers["Authorization"][:50] + "..." if len(headers.get("Authorization", "")) > 50 else headers["Authorization"]
        print(f"{YELLOW}Headers:{RESET} Authorization: {auth_token}")

def print_response(status_code: int, body: Any):
    """Print response details"""
    color = GREEN if status_code < 400 else RED
    print(f"{color}Status: {status_code}{RESET}")
    print(f"{YELLOW}Response Body:{RESET}")
    if isinstance(body, dict):
        print(json.dumps(body, indent=2))
    else:
        print(body)

async def test_workflow():
    """Execute complete workflow"""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # ==================== STEP 1: REGISTER STUDENT ====================
            print_step(1, "Register Student → Capture User ID & Token")
            result.steps_executed += 1
            
            timestamp = datetime.now().timestamp()
            student1_email = f"student1_{timestamp}@test.com"
            student1_password = "Test123!@"
            
            print_section("Create Student Account")
            payload = {
                "user_data": {
                    "email": student1_email,
                    "password": student1_password,
                    "role": "student"
                },
                "student_data": {
                    "first_name": "Alice",
                    "last_name": "Johnson",
                    "branch": "CS",
                    "graduation_year": 2024,
                    "cgpa": 8.5,
                    "college_id": 1
                }
            }
            print_request("POST", f"{BASE_URL}/auth/register/student", payload)
            
            resp = await client.post(f"{BASE_URL}/auth/register/student", json=payload)
            print_response(resp.status_code, resp.json())
            
            if resp.status_code != 201:
                result.failed_step = 1
                result.failed_reason = f"Expected 201, got {resp.status_code}"
                return False
            
            student1_data = resp.json()
            result.data["student1_id"] = student1_data["user"]["id"]
            result.data["student1_profile_id"] = student1_data["user"]["profile_id"]
            result.data["student1_token"] = student1_data["access_token"]
            result.steps_passed += 1
            print_success(f"Student 1 registered - ID: {result.data['student1_id']}, Profile ID: {result.data['student1_profile_id']}")

            # ==================== STEP 2: REGISTER RECRUITER ====================
            print_step(2, "Register Recruiter → Capture User ID & Token")
            result.steps_executed += 1
            
            recruiter_email = f"recruiter_{datetime.now().timestamp()}@test.com"
            recruiter_password = "Test123!@"
            
            print_section("Create Recruiter Account")
            payload = {
                "user_data": {
                    "email": recruiter_email,
                    "password": recruiter_password,
                    "role": "recruiter"
                },
                "recruiter_data": {
                    "first_name": "Bob",
                    "last_name": "Smith",
                    "company_name": "TechCorp Inc",
                    "email": recruiter_email,
                    "college_id": 1
                }
            }
            print_request("POST", f"{BASE_URL}/auth/register/recruiter", payload)
            
            resp = await client.post(f"{BASE_URL}/auth/register/recruiter", json=payload)
            print_response(resp.status_code, resp.json())
            
            if resp.status_code != 201:
                result.failed_step = 2
                result.failed_reason = f"Expected 201, got {resp.status_code}"
                return False
            
            recruiter_data = resp.json()
            result.data["recruiter_id"] = recruiter_data["user"]["id"]
            result.data["recruiter_profile_id"] = recruiter_data["user"]["profile_id"]
            result.data["recruiter_token"] = recruiter_data["access_token"]
            result.steps_passed += 1
            print_success(f"Recruiter registered - ID: {result.data['recruiter_id']}, Profile ID: {result.data['recruiter_profile_id']}")

            # ==================== STEP 3: REGISTER PLACEMENT OFFICER ====================
            print_step(3, "Register Placement Officer → Capture User ID & Token")
            result.steps_executed += 1
            
            officer_email = f"officer_{datetime.now().timestamp()}@test.com"
            officer_password = "Test123!@"
            
            print_section("Create Placement Officer Account")
            payload = {
                "user_data": {
                    "email": officer_email,
                    "password": officer_password,
                    "role": "placement_officer"
                },
                "officer_data": {
                    "name": "Charlie Brown",
                    "email": officer_email,
                    "designation": "TPO",
                    "department": "Admin",
                    "college_id": 1
                }
            }
            print_request("POST", f"{BASE_URL}/auth/register/placement_officer", payload)
            
            resp = await client.post(f"{BASE_URL}/auth/register/placement_officer", json=payload)
            print_response(resp.status_code, resp.json())
            
            if resp.status_code != 201:
                result.failed_step = 3
                result.failed_reason = f"Expected 201, got {resp.status_code}"
                return False
            
            officer_data = resp.json()
            result.data["officer_id"] = officer_data["user"]["id"]
            result.data["officer_profile_id"] = officer_data["user"]["profile_id"]
            result.data["officer_token"] = officer_data["access_token"]
            result.steps_passed += 1
            print_success(f"Officer registered - ID: {result.data['officer_id']}, Profile ID: {result.data['officer_profile_id']}")

            # ==================== STEP 3.5: VERIFY RECRUITER ====================
            print_step("3.5", "Officer Verifies Recruiter Account")
            result.steps_executed += 1
            
            print_section("Verify Recruiter")
            headers = {"Authorization": f"Bearer {result.data['officer_token']}"}
            endpoint = f"{BASE_URL}/recruiters/{result.data['recruiter_profile_id']}/verify?is_verified=true"
            print_request("PUT", endpoint, headers=headers)
            
            resp = await client.put(endpoint, headers=headers)
            print_response(resp.status_code, resp.json())
            
            if resp.status_code != 200:
                result.failed_step = "3.5"
                result.failed_reason = f"Expected 200, got {resp.status_code}"
                return False
            
            result.steps_passed += 1
            print_success("Recruiter verified by officer")

            # ==================== STEP 4: CREATE JOB ====================
            print_step(4, "Recruiter Creates Job")
            result.steps_executed += 1
            
            print_section("Create Job Posting")
            payload = {
                "title": "Senior Software Engineer",
                "description": "We are hiring experienced software engineers",
                "job_type": "full_time",
                "location": "San Francisco, CA",
                "is_remote": False,
                "salary_min": 120000,
                "salary_max": 160000,
                "positions_available": 5,
                "college_id": 1,
                "min_cgpa": 7.0,
                "allowed_branches": ["CS", "IT"],
                "max_backlogs": 0
            }
            headers = {"Authorization": f"Bearer {result.data['recruiter_token']}"}
            print_request("POST", f"{BASE_URL}/jobs/", payload, headers)
            
            resp = await client.post(f"{BASE_URL}/jobs/", json=payload, headers=headers)
            print_response(resp.status_code, resp.json() if resp.status_code < 400 else resp.text)
            
            if resp.status_code != 201:
                result.failed_step = 4
                result.failed_reason = f"Expected 201, got {resp.status_code}: {resp.text}"
                return False
            
            job_data = resp.json()
            result.data["job_id"] = job_data["id"]
            result.steps_passed += 1
            print_success(f"Job created - ID: {result.data['job_id']}")

            # ==================== STEP 5: APPROVE JOB ====================
            print_step(5, "Officer Approves Job")
            result.steps_executed += 1
            
            print_section("Approve Job for Placement Drive")
            headers = {"Authorization": f"Bearer {result.data['officer_token']}"}
            endpoint = f"{BASE_URL}/jobs/{result.data['job_id']}/approve"
            print_request("PUT", endpoint, headers=headers)
            
            resp = await client.put(endpoint, headers=headers)
            print_response(resp.status_code, resp.json())
            
            if resp.status_code != 200:
                result.failed_step = 5
                result.failed_reason = f"Expected 200, got {resp.status_code}"
                return False
            
            result.steps_passed += 1
            print_success("Job approved for placement drive")

            # ==================== STEP 6: STUDENT APPLIES ====================
            print_step(6, "Student Applies to Job")
            result.steps_executed += 1
            
            print_section("Submit Job Application")
            payload = {
                "job_id": result.data["job_id"],
                "cover_letter": "I am interested in this position"
            }
            headers = {"Authorization": f"Bearer {result.data['student1_token']}"}
            print_request("POST", f"{BASE_URL}/applications/", payload, headers)
            
            resp = await client.post(f"{BASE_URL}/applications/", json=payload, headers=headers)
            print_response(resp.status_code, resp.json() if resp.status_code < 400 else resp.text)
            
            if resp.status_code != 201:
                result.failed_step = 6
                result.failed_reason = f"Expected 201, got {resp.status_code}: {resp.text}"
                return False
            
            app_data = resp.json()
            result.data["app1_id"] = app_data["id"]
            result.steps_passed += 1
            print_success(f"Application submitted - ID: {result.data['app1_id']}")

            # ==================== STEP 7: ROUND WORKFLOW ====================
            print_step(7, "Round Workflow: 2 PASS, 1 FAIL → Application REJECTED")
            result.steps_executed += 1
            
            print_section("Add Round 1 (PASSED)")
            payload = {
                "round_name": "Online Test",
                "round_type": "TEST"
            }
            headers = {"Authorization": f"Bearer {result.data['recruiter_token']}"}
            endpoint = f"{BASE_URL}/applications/{result.data['app1_id']}/add-round"
            print_request("POST", endpoint, payload, headers)
            
            resp = await client.post(endpoint, json=payload, headers=headers)
            print_response(resp.status_code, resp.json())
            
            if resp.status_code != 201:
                result.failed_step = "7a"
                result.failed_reason = f"Round 1 failed - Expected 201, got {resp.status_code}"
                return False
            
            round1_id = resp.json()["id"]
            print_success(f"Round 1 added - ID: {round1_id}")
            
            print_section("Set Round 1 Result (PASSED)")
            payload = {"result": "PASSED"}
            print_request("PUT", f"{BASE_URL}/rounds/{round1_id}", payload, headers)
            
            resp = await client.put(f"{BASE_URL}/rounds/{round1_id}", json=payload, headers=headers)
            print_response(resp.status_code, resp.json())
            
            if resp.status_code != 200:
                result.failed_step = "7b"
                result.failed_reason = f"Round 1 result update failed - Expected 200, got {resp.status_code}"
                return False
            
            print_success("Round 1 marked PASSED")
            
            print_section("Add Round 2 (PASSED)")
            payload = {
                "round_name": "Technical Interview",
                "round_type": "INTERVIEW"
            }
            endpoint = f"{BASE_URL}/applications/{result.data['app1_id']}/add-round"
            print_request("POST", endpoint, payload, headers)
            
            resp = await client.post(endpoint, json=payload, headers=headers)
            print_response(resp.status_code, resp.json())
            
            if resp.status_code != 201:
                result.failed_step = "7c"
                result.failed_reason = f"Round 2 failed - Expected 201, got {resp.status_code}"
                return False
            
            round2_id = resp.json()["id"]
            print_success(f"Round 2 added - ID: {round2_id}")
            
            print_section("Set Round 2 Result (PASSED)")
            payload = {"result": "PASSED"}
            print_request("PUT", f"{BASE_URL}/rounds/{round2_id}", payload, headers)
            
            resp = await client.put(f"{BASE_URL}/rounds/{round2_id}", json=payload, headers=headers)
            print_response(resp.status_code, resp.json())
            
            if resp.status_code != 200:
                result.failed_step = "7d"
                result.failed_reason = f"Round 2 result update failed - Expected 200, got {resp.status_code}"
                return False
            
            print_success("Round 2 marked PASSED")
            
            print_section("Add Round 3 (FAILED)")
            payload = {
                "round_name": "Final Round",
                "round_type": "INTERVIEW"
            }
            endpoint = f"{BASE_URL}/applications/{result.data['app1_id']}/add-round"
            print_request("POST", endpoint, payload, headers)
            
            resp = await client.post(endpoint, json=payload, headers=headers)
            print_response(resp.status_code, resp.json())
            
            if resp.status_code != 201:
                result.failed_step = "7e"
                result.failed_reason = f"Round 3 failed - Expected 201, got {resp.status_code}"
                return False
            
            round3_id = resp.json()["id"]
            print_success(f"Round 3 added - ID: {round3_id}")
            
            print_section("Set Round 3 Result (FAILED)")
            payload = {"result": "FAILED"}
            print_request("PUT", f"{BASE_URL}/rounds/{round3_id}", payload, headers)
            
            resp = await client.put(f"{BASE_URL}/rounds/{round3_id}", json=payload, headers=headers)
            print_response(resp.status_code, resp.json())
            
            if resp.status_code != 200:
                result.failed_step = "7f"
                result.failed_reason = f"Round 3 result update failed - Expected 200, got {resp.status_code}"
                return False
            
            print_success("Round 3 marked FAILED")
            
            print_section("Verify Application Status = REJECTED")
            headers = {"Authorization": f"Bearer {result.data['student1_token']}"}
            endpoint = f"{BASE_URL}/applications/{result.data['app1_id']}"
            print_request("GET", endpoint, headers=headers)
            
            resp = await client.get(endpoint, headers=headers)
            print_response(resp.status_code, resp.json())
            
            if resp.status_code != 200:
                result.failed_step = "7g"
                result.failed_reason = f"Get application failed - Expected 200, got {resp.status_code}"
                return False
            
            app_status = resp.json()["status"]
            if app_status != "REJECTED":
                result.failed_step = "7g"
                result.failed_reason = f"Expected application status REJECTED, got {app_status}"
                return False
            
            result.steps_passed += 1
            print_success("Application correctly marked REJECTED after failing round 3")

            # ==================== STEP 8: SUCCESSFUL CANDIDATE ====================
            print_step(8, "New Student → Pass All Rounds → Accept Offer")
            result.steps_executed += 1
            
            print_section("Register New Student")
            timestamp = datetime.now().timestamp()
            student2_email = f"student2_{timestamp}@test.com"
            student2_password = "Test123!@"
            
            payload = {
                "user_data": {
                    "email": student2_email,
                    "password": student2_password,
                    "role": "student"
                },
                "student_data": {
                    "first_name": "Diana",
                    "last_name": "Prince",
                    "branch": "CS",
                    "graduation_year": 2024,
                    "cgpa": 9.2,
                    "college_id": 1
                }
            }
            print_request("POST", f"{BASE_URL}/auth/register/student", payload)
            
            resp = await client.post(f"{BASE_URL}/auth/register/student", json=payload)
            print_response(resp.status_code, resp.json())
            
            if resp.status_code != 201:
                result.failed_step = "8a"
                result.failed_reason = f"Student 2 registration failed"
                return False
            
            student2_data = resp.json()
            result.data["student2_id"] = student2_data["user"]["id"]
            result.data["student2_profile_id"] = student2_data["user"]["profile_id"]
            result.data["student2_token"] = student2_data["access_token"]
            print_success(f"Student 2 registered - ID: {result.data['student2_id']}")
            
            print_section("Student 2 Applies to Same Job")
            payload = {
                "job_id": result.data["job_id"],
                "cover_letter": "I am very interested"
            }
            headers = {"Authorization": f"Bearer {result.data['student2_token']}"}
            print_request("POST", f"{BASE_URL}/applications/", payload, headers)
            
            resp = await client.post(f"{BASE_URL}/applications/", json=payload, headers=headers)
            print_response(resp.status_code, resp.json())
            
            if resp.status_code != 201:
                result.failed_step = "8b"
                result.failed_reason = f"Student 2 application failed"
                return False
            
            app2_data = resp.json()
            result.data["app2_id"] = app2_data["id"]
            print_success(f"Student 2 application submitted - ID: {result.data['app2_id']}")
            
            print_section("Pass All Rounds for Student 2")
            headers = {"Authorization": f"Bearer {result.data['recruiter_token']}"}
            
            for i, (round_name, round_type) in enumerate([
                ("Online Test", "TEST"),
                ("Technical Interview", "INTERVIEW"),
                ("Final Round", "INTERVIEW")
            ], 1):
                payload = {"round_name": round_name, "round_type": round_type}
                endpoint = f"{BASE_URL}/applications/{result.data['app2_id']}/add-round"
                resp = await client.post(endpoint, json=payload, headers=headers)
                
                if resp.status_code != 201:
                    result.failed_step = f"8c{i}"
                    result.failed_reason = f"Add round {i} failed"
                    return False
                
                round_id = resp.json()["id"]
                payload = {"result": "PASSED"}
                resp = await client.put(f"{BASE_URL}/rounds/{round_id}", json=payload, headers=headers)
                
                if resp.status_code != 200:
                    result.failed_step = f"8c{i}b"
                    result.failed_reason = f"Update round {i} result failed"
                    return False
                
                print(f"  Round {i}: {round_name} ✓")
            
            print_success("All 3 rounds PASSED for Student 2")
            
            print_section("Create Offer")
            payload = {
                "offer_letter": "We are pleased to extend an offer"
            }
            endpoint = f"{BASE_URL}/applications/{result.data['app2_id']}/offer"
            print_request("POST", endpoint, payload, headers)
            
            resp = await client.post(endpoint, json=payload, headers=headers)
            print_response(resp.status_code, resp.json() if resp.status_code < 400 else resp.text)
            
            if resp.status_code != 201:
                result.failed_step = "8d"
                result.failed_reason = f"Create offer failed - Expected 201, got {resp.status_code}: {resp.text}"
                return False
            
            offer_data = resp.json()
            result.data["offer_id"] = offer_data["id"]
            print_success(f"Offer created - ID: {result.data['offer_id']}")
            
            print_section("Student 2 Accepts Offer")
            headers = {"Authorization": f"Bearer {result.data['student2_token']}"}
            endpoint = f"{BASE_URL}/offers/{result.data['offer_id']}/accept"
            print_request("PUT", endpoint, headers=headers)
            
            resp = await client.put(endpoint, headers=headers)
            print_response(resp.status_code, resp.json())
            
            if resp.status_code != 200:
                result.failed_step = "8e"
                result.failed_reason = f"Accept offer failed"
                return False
            
            result.steps_passed += 1
            print_success("Offer accepted - Student 2 marked as PLACED")

            # ==================== STEP 9: NOTIFICATIONS ====================
            print_step(9, "Verify Notifications")
            result.steps_executed += 1
            
            print_section("Get Student 2 Notifications")
            headers = {"Authorization": f"Bearer {result.data['student2_token']}"}
            print_request("GET", f"{BASE_URL}/notifications/", headers=headers)
            
            resp = await client.get(f"{BASE_URL}/notifications/", headers=headers)
            print_response(resp.status_code, resp.json())
            
            if resp.status_code != 200:
                result.failed_step = 9
                result.failed_reason = f"Get notifications failed"
                return False
            
            notifications = resp.json()
            if not isinstance(notifications, list) or len(notifications) == 0:
                result.failed_step = 9
                result.failed_reason = f"Expected notifications, got empty list"
                return False
            
            result.steps_passed += 1
            print_success(f"Notifications retrieved - {len(notifications)} notifications")

            # ==================== STEP 10: ANALYTICS ====================
            print_step(10, "Test Analytics Endpoints")
            result.steps_executed += 1
            
            print_section("Get Top Candidates")
            headers = {"Authorization": f"Bearer {result.data['officer_token']}"}
            print_request("GET", f"{BASE_URL}/analytics/top-candidates?limit=10", headers=headers)
            
            resp = await client.get(f"{BASE_URL}/analytics/top-candidates?limit=10", headers=headers)
            print_response(resp.status_code, resp.json() if resp.status_code < 400 else resp.text)
            
            if resp.status_code != 200:
                result.failed_step = "10a"
                result.failed_reason = f"Top candidates failed - Expected 200, got {resp.status_code}"
                return False
            
            print_success("Top candidates fetched")
            
            print_section("Get Student Insights")
            headers = {"Authorization": f"Bearer {result.data['student2_token']}"}
            print_request("GET", f"{BASE_URL}/analytics/student-insights", headers=headers)
            
            resp = await client.get(f"{BASE_URL}/analytics/student-insights", headers=headers)
            print_response(resp.status_code, resp.json() if resp.status_code < 400 else resp.text)
            
            if resp.status_code != 200:
                result.failed_step = "10b"
                result.failed_reason = f"Student insights failed - Expected 200, got {resp.status_code}"
                return False
            
            print_success("Student insights fetched")
            
            print_section("Get Drive Summary")
            headers = {"Authorization": f"Bearer {result.data['officer_token']}"}
            endpoint = f"{BASE_URL}/analytics/placement-drive/{result.data['job_id']}"
            print_request("GET", endpoint, headers=headers)
            
            resp = await client.get(endpoint, headers=headers)
            print_response(resp.status_code, resp.json() if resp.status_code < 400 else resp.text)
            
            if resp.status_code != 200:
                result.failed_step = "10c"
                result.failed_reason = f"Drive summary failed - Expected 200, got {resp.status_code}"
                return False
            
            result.steps_passed += 1
            print_success("Drive summary fetched")
            
            return True

    except Exception as e:
        print(f"\n{RED}EXCEPTION: {str(e)}{RESET}")
        import traceback
        print(traceback.format_exc())
        return False


async def main():
    print(f"\n{BOLD}{BLUE}{'='*80}{RESET}")
    print(f"{BOLD}{BLUE}COMPREHENSIVE E2E WORKFLOW TEST{RESET}")
    print(f"{BOLD}{BLUE}Started: {datetime.now().isoformat()}{RESET}")
    print(f"{BOLD}{BLUE}{'='*80}{RESET}\n")
    
    success = await test_workflow()
    
    # ==================== FINAL VERDICT ====================
    print(f"\n{BOLD}{BLUE}{'='*80}{RESET}")
    print(f"{BOLD}{BLUE}TEST SUMMARY{RESET}")
    print(f"{BOLD}{BLUE}{'='*80}{RESET}")
    print(f"Steps Executed: {result.steps_executed}")
    print(f"Steps Passed: {result.steps_passed}")
    
    if success:
        print(f"\n{GREEN}{BOLD}✅ SYSTEM FULLY WORKING{RESET}")
        print(f"{GREEN}All 10 steps completed successfully{RESET}")
    else:
        print(f"\n{RED}{BOLD}❌ SYSTEM NOT READY{RESET}")
        print(f"{RED}Failed at Step: {result.failed_step}{RESET}")
        print(f"{RED}Reason: {result.failed_reason}{RESET}")
    
    print(f"\n{BOLD}{BLUE}{'='*80}{RESET}\n")


if __name__ == "__main__":
    asyncio.run(main())
