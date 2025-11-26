import requests
import sys

BASE_URL = "http://localhost:8000/api"

def test_create_operator():
    # 1. Login
    print("🔑 Logging in as admin...")
    login_payload = {"username": "admin", "password": "admin123"}
    try:
        login_res = requests.post(f"{BASE_URL}/admin/login", json=login_payload)
        if login_res.status_code != 200:
            print(f"❌ Login failed: {login_res.status_code} - {login_res.text}")
            return
        
        token = login_res.json()["access_token"]
        print("✅ Login successful, token received")
        
        # 2. Create Operator
        print("👤 Creating operator...")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create dummy image
        files = {
            'face_image': ('test.jpg', b'fakeimagebytes', 'image/jpeg')
        }
        
        data = {
            'name': 'Test Operator',
            'operator_id': 'TEST001',
            'machine_no': 'M1',
            'shift': 'Day'
        }
        
        res = requests.post(
            f"{BASE_URL}/operators", 
            headers=headers,
            data=data,
            files=files
        )
        
        print(f"Status Code: {res.status_code}")
        print(f"Response: {res.text}")
        
        if res.status_code == 201:
            print("✅ Operator created successfully!")
            
            # Cleanup
            print("🧹 Deleting test operator...")
            del_res = requests.delete(f"{BASE_URL}/operators/TEST001", headers=headers)
            print(f"Delete Status: {del_res.status_code}")
            
        elif res.status_code == 403:
            print("❌ 403 Forbidden - Backend is rejecting the request")
        else:
            print(f"⚠️ Unexpected status: {res.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_create_operator()
