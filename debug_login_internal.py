from fastapi.testclient import TestClient
from main import app
import sys
import traceback

try:
    print("Initializing TestClient...")
    client = TestClient(app)
    print("TestClient initialized")
except Exception:
    with open("startup_traceback.txt", "w") as f:
        traceback.print_exc(file=f)
    traceback.print_exc()
    sys.exit(1)

def test_login_internal():
    print("🚀 Testing login internally...")
    try:
        response = client.post(
            "/api/admin/login",
            json={"username": "admin", "password": "admin123"}
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 500:
            print("❌ 500 Error Detected!")
    except Exception:
        with open("traceback.txt", "w") as f:
            traceback.print_exc(file=f)
        traceback.print_exc()

if __name__ == "__main__":
    test_login_internal()
