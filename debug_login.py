import requests
import sys

def test_login():
    url = "http://localhost:8000/api/admin/login"
    payload = {
        "username": "admin",
        "password": "admin123"
    }
    
    print(f"Attempting login to {url}...")
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 500:
            print("❌ Server returned 500 Internal Server Error")
        elif response.status_code == 200:
            print("✅ Login successful!")
        else:
            print(f"⚠️ Unexpected status code: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    test_login()
