"""Debug registration endpoint to capture full traceback"""
import asyncio
import json
import sys
from datetime import datetime

# Set up path
sys.path.insert(0, 'd:\\Gourav\\Project 1\\Backend')

# Import after path setup
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_register_student():
    """Call register_student endpoint and capture response"""
    email = f"debug_student_{datetime.now().timestamp()}@example.com"
    
    payload = {
        "user_data": {
            "email": email,
            "password": "TestPass123!",
            "role": "student",
        },
        "student_data": {
            "first_name": "Debug",
            "last_name": "Student",
            "branch": "CS",
            "graduation_year": 2024,
            "cgpa": 8.5,
            "college_id": 1,
        }
    }
    
    print("=" * 70)
    print("CALLING /api/v1/auth/register/student")
    print("=" * 70)
    print(f"\nPayload: {json.dumps(payload, indent=2)}\n")
    
    try:
        response = client.post("/api/v1/auth/register/student", json=payload)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"\nResponse Body:\n{response.text}")
        
        if response.status_code == 500:
            print("\n" + "=" * 70)
            print("500 ERROR DETECTED - See server output for full traceback")
            print("=" * 70)
        
        return response
        
    except Exception as e:
        print(f"Exception: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_register_student()
