import requests
import json

# Test admin login
url = "http://localhost:8000/api/admin/login"
data = {
    "username": "admin",
    "password": "admin123"
}

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    if response.status_code == 200:
        print("✅ Login successful!")
        print(f"Token: {response.json()['access_token'][:50]}...")
    else:
        print("❌ Login failed")
except Exception as e:
    print(f"Error: {e}")
