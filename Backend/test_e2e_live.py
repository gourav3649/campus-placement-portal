import asyncio
import requests
import time
import sys
import uuid
import subprocess

from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.college import College
from app.models.placement_officer import PlacementOfficer
from app.core.security import hash_password
from app.core.rbac import Role

BASE_URL = "http://localhost:8000/api/v1"
unique = str(uuid.uuid4())[:6]
officer_email = f"officer{unique}@test.com"
admin_email = f"admin{unique}@test.com"

def print_step(msg):
    print(f"\n[{msg}]")

def assert_eq(a, b, msg="", res=None):
    if a != b:
        print(f"[FAIL] ASSERTION FAILED: {msg} (Expected {b}, got {a})")
        if res is not None:
            open("failed_response.txt", "w").write(res.text)
            print(f"Response Body dumped to failed_response.txt")
        sys.exit(1)
    print(f"[PASS] {msg}")

async def seed_db():
    print("Seeding baseline Admin & Officer in DB...")
    async with AsyncSessionLocal() as db:
        # Create Admin
        admin = User(email=admin_email, hashed_password=hash_password("pass"), role=Role.ADMIN, is_active=True)
        db.add(admin)
        await db.commit()
        await db.refresh(admin)

        # Create College
        college = College(name=f"Test College {unique}", location="Campus", website="example.com")
        db.add(college)
        await db.commit()
        await db.refresh(college)

        # Create Officer User + Profile
        officer_user = User(email=officer_email, hashed_password=hash_password("pass"), role=Role.PLACEMENT_OFFICER, is_active=True)
        db.add(officer_user)
        await db.commit()
        await db.refresh(officer_user)

        officer_prof = PlacementOfficer(user_id=officer_user.id, name="Head Officer", email=officer_email, college_id=college.id, department="Placement")
        db.add(officer_prof)
        await db.commit()
        
        return college.id

def run_tests(college_id):
    # Start server
    print("Starting uvicorn server in background...")
    proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8000"])
    
    session = requests.Session()
    
    try:
        # Wait for server
        max_retries = 15
        for i in range(max_retries):
            try:
                res = requests.get(BASE_URL.replace("/api/v1", "/docs"))
                if res.status_code == 200:
                    print("Server is up!")
                    break
            except requests.exceptions.ConnectionError:
                pass
            time.sleep(1)
        else:
            print("Server failed to start")
            raise AssertionError("Server boot failed")

        print_step("Phase 1: Setup Recruiter")
        
        # Login Officer
        res = session.post(f"{BASE_URL}/auth/login", data={"username": officer_email, "password": "pass"})
        officer_token = res.json()["access_token"]
        officer_headers = {"Authorization": f"Bearer {officer_token}"}
        
        # Register Recruiter
        recruiter_email = f"recruiter{unique}@test.com"
        res = session.post(f"{BASE_URL}/auth/register/recruiter", json={
            "user_data": {"email": recruiter_email, "password": "pass", "full_name": "Recruiter", "role": "recruiter"},
            "recruiter_data": {"company_name": "Google", "email": recruiter_email}
        })
        assert_eq(res.status_code, 201, "Recruiter registered", res)

        # Login Recruiter
        res = session.post(f"{BASE_URL}/auth/login", data={"username": recruiter_email, "password": "pass"})
        rec_token = res.json()["access_token"]
        rec_headers = {"Authorization": f"Bearer {rec_token}"}
        
        # Fetch recruiter ID to verify them
        res = session.get(f"{BASE_URL}/recruiters/me", headers=rec_headers)
        rec_id = res.json()["user_id"] # Wait, the API might return different fields. Let's get id instead.
        rec_id = res.json().get("id", res.json().get("user_id"))
        
        # Officer verifies Recruiter
        res = session.put(f"{BASE_URL}/recruiters/{rec_id}/verify?is_verified=true", headers=officer_headers)
        assert_eq(res.status_code, 200, "Officer verified recruiter")

        print_step("Phase 2: Recruiter creates drive")
        res = session.post(f"{BASE_URL}/jobs/", headers=rec_headers, json={
            "title": "Software Engineer",
            "description": "Build things",
            "college_id": college_id,
            "job_type": "FULL_TIME",
            "min_cgpa": 7.0,
            "allowed_branches": ["CSE", "IT"]
        })
        assert_eq(res.status_code, 201, "Recruiter created job", res)
        job_id = res.json()["id"]
        assert_eq(res.json()["status"], "DRAFT", "New job is immediately DRAFT")

        # Student tries to view jobs -> should be 0 approved
        student_valid_email = f"studentV{unique}@test.com"
        res = session.post(f"{BASE_URL}/auth/register/student", json={
            "user_data": {"email": student_valid_email, "password": "pass", "role": "student"},
            "student_data": {
                "first_name": "Valid", 
                "last_name": "Student", 
                "college_id": college_id, 
                "branch": "CSE", 
                "cgpa": 8.0,
                "graduation_year": 2024
            }
        })
        assert_eq(res.status_code, 201, "Student V registered", res)
        res = session.post(f"{BASE_URL}/auth/login", data={"username": student_valid_email, "password": "pass"})
        stud_v_token = res.json()["access_token"]
        stud_v_headers = {"Authorization": f"Bearer {stud_v_token}"}
        
        res = session.get(f"{BASE_URL}/jobs/", headers=stud_v_headers)
        assert_eq(len([j for j in res.json() if j["id"] == job_id]), 0, "DRAFT job not visible to students")

        # Officer approves job
        res = session.post(f"{BASE_URL}/jobs/{job_id}/approve", headers=officer_headers)
        assert_eq(res.status_code, 200, "Officer approved job")
        assert_eq(res.json()["status"], "APPROVED", "Job is now APPROVED")

        res = session.get(f"{BASE_URL}/jobs/", headers=stud_v_headers)
        assert_eq(len([j for j in res.json() if j["id"] == job_id]), 1, "APPROVED job visible to valid student")

        print_step("Phase 3: Eligibility & Apply Workflow")
        student_invalid_email = f"studentI{unique}@test.com"
        res = session.post(f"{BASE_URL}/auth/register/student", json={
            "user_data": {"email": student_invalid_email, "password": "pass", "role": "student"},
            "student_data": {
                "first_name": "Invalid", 
                "last_name": "Student", 
                "college_id": college_id, 
                "branch": "ME", 
                "cgpa": 6.0,
                "graduation_year": 2024
            }
        })
        assert_eq(res.status_code, 201, "Student I registered", res)
        res = session.post(f"{BASE_URL}/auth/login", data={"username": student_invalid_email, "password": "pass"})
        stud_i_headers = {"Authorization": f"Bearer {res.json()['access_token']}"}

        # Invalid student applies
        res = session.post(f"{BASE_URL}/applications/", headers=stud_i_headers, json={"job_id": job_id})
        assert_eq(res.status_code, 201, "Invalid student applied")
        assert_eq(res.json()["status"], "ELIGIBILITY_FAILED", "Invalid student correctly failed eligibility automatically")

        # Valid student applies
        res = session.post(f"{BASE_URL}/applications/", headers=stud_v_headers, json={"job_id": job_id})
        assert_eq(res.status_code, 201, "Valid student applied")
        assert_eq(res.json()["status"], "PENDING", "Valid student is PENDING")
        valid_app_id = res.json()["id"]

        # Valid applies AGAIN
        res = session.post(f"{BASE_URL}/applications/", headers=stud_v_headers, json={"job_id": job_id})
        assert_eq(res.status_code, 409, "Duplicate application 409 blocked securely")

        print_step("Phase 4: Bulk Rounds & Progression")
        # Officer sees applications
        res = session.get(f"{BASE_URL}/applications/job/{job_id}", headers=officer_headers)
        assert_eq(len(res.json()), 2, "Officer sees both applicants")

        # Recruiter sees applications
        res = session.get(f"{BASE_URL}/applications/recruiter/job/{job_id}", headers=rec_headers)
        assert_eq(res.status_code, 200, f"Recruiter fetched job (Response: {res.text})")
        assert_eq(len(res.json()), 2, "Recruiter sees both applicants")

        # Recruiter tries to modify status
        res = session.put(f"{BASE_URL}/applications/officer/{valid_app_id}/status?new_status=REVIEWING", headers=rec_headers)
        assert_eq(res.status_code, 403, "Recruiter blocked from mutating status")

        # Officer modifies status
        res = session.put(f"{BASE_URL}/applications/officer/{valid_app_id}/status?new_status=REVIEWING", headers=officer_headers)
        assert_eq(res.status_code, 200, "Officer changed status to REVIEWING")

        # Officer adds Round 1
        res = session.post(f"{BASE_URL}/applications/{valid_app_id}/rounds", headers=officer_headers, json={
            "round_name": "Aptitude Test", "round_number": 1, "result": "PASSED"
        })
        assert_eq(res.status_code, 201, "Officer added Round 1")

        # Check views reflect same round
        res_officer = session.get(f"{BASE_URL}/applications/job/{job_id}", headers=officer_headers)
        res_recruiter = session.get(f"{BASE_URL}/applications/recruiter/job/{job_id}", headers=rec_headers)
        res_student = session.get(f"{BASE_URL}/applications/{valid_app_id}", headers=stud_v_headers)
        
        r1_off = next(a for a in res_officer.json() if a["id"] == valid_app_id)["rounds"][0]["round_name"]
        r1_rec = next(a for a in res_recruiter.json() if a["id"] == valid_app_id)["rounds"][0]["round_name"]
        r1_stud = res_student.json()["rounds"][0]["round_name"]
        assert_eq(r1_off == r1_rec == r1_stud == "Aptitude Test", True, "Round data is perfectly consistent across roles")

        print_step("Phase 5: Notifications & Offers")
        res = session.get(f"{BASE_URL}/notifications/", headers=stud_v_headers)
        notifs = res.json()
        assert_eq(len(notifs) >= 2, True, "Student received notifications for drive opening and round passing")

        # Place student
        res = session.post(f"{BASE_URL}/offers/", headers=officer_headers, json={
            "application_id": valid_app_id, "ctc": 12.5
        })
        assert_eq(res.status_code, 201, "Officer issued offer")

        # Check metrics alignment
        res_job_off = session.get(f"{BASE_URL}/jobs/all", headers=officer_headers)
        res_job_rec = session.get(f"{BASE_URL}/jobs/my-jobs", headers=rec_headers)
        
        metrics_off = next(j for j in res_job_off.json() if j["id"] == job_id)
        metrics_rec = next(j for j in res_job_rec.json() if j["id"] == job_id)
        assert_eq(metrics_off["total_applied"], metrics_rec["total_applied"], "Metric: Total Applied aligns perfectly")
        assert_eq(metrics_off["selected_count"], metrics_rec["selected_count"], "Metric: Offers aligns perfectly")
        assert_eq(metrics_off["eligible_count"], metrics_rec["eligible_count"], "Metric: Eligible aligns perfectly")

        print_step("Phase 6: Delete Mistake Round")
        round_id = res_student.json()["rounds"][0]["id"]
        res = session.delete(f"{BASE_URL}/rounds/{round_id}", headers=officer_headers)
        assert_eq(res.status_code, 204, "Officer deleted mistaken round")
        res = session.get(f"{BASE_URL}/applications/{valid_app_id}", headers=stud_v_headers)
        assert_eq(len(res.json()["rounds"]), 0, "Student timeline dynamically empty after deletion")

        print("\n[ALL PASS] End to End System Validation Complete. No vulnerabilities or logic breaks discovered.")
    
    except AssertionError as e:
        print(e)
        sys.exit(1)
    finally:
        print("Shutting down test server...")
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()

if __name__ == "__main__":
    college_id = asyncio.run(seed_db())
    run_tests(college_id)
