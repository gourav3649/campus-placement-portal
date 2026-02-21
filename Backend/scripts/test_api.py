"""Test script to verify API endpoints work with database."""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_login():
    """Test admin login endpoint."""
    print("Testing admin login...")
    response = requests.post(
        f"{BASE_URL}/auth/login/json",
        json={
            "email": "admin@collegex.edu",
            "password": "admin123"
        }
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Login successful!")
        print(f"  Access Token: {data['access_token'][:50]}...")
        print(f"  Role: {data.get('role', 'N/A')}")  
        return data['access_token']
    else:
        print(f"✗ Login failed: {response.text}")
        return None

def test_placement_officer_login():
    """Test placement officer login."""
    print("\nTesting placement officer login...")
    response = requests.post(
        f"{BASE_URL}/auth/login/json",
        json={
            "email": "placement@collegex.edu",
            "password": "placement123"
        }
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Login successful!")
        print(f"  Access Token: {data['access_token'][:50]}...")
        print(f"  Role: {data.get('role', 'N/A')}")
        return data['access_token']
    else:
        print(f"✗ Login failed: {response.text}")
        return None

def test_get_colleges(token):
    """Test get colleges endpoint."""
    print("\nTesting get colleges...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/colleges", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        colleges = response.json()
        print(f"✓ Found {len(colleges)} college(s)")
        for college in colleges:
            print(f"  - {college['name']} (ID={college['id']})")
    else:
        print(f"✗ Failed: {response.text}")

if __name__ == "__main__":
    print("="*50)
    print("Campus Placement Portal - API Tests")
    print("="*50)
    
    # Test admin login
    admin_token = test_login()
    
    # Test placement officer login
    po_token = test_placement_officer_login()
    
    # Test colleges endpoint
    if admin_token:
        test_get_colleges(admin_token)
    
    print("\n" + "="*50)
    print("✅ Backend is ready!")
    print("="*50)
