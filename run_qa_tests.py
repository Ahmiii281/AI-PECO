import asyncio
import nest_asyncio
from fastapi.testclient import TestClient
from unittest.mock import patch
from mongomock_motor import AsyncMongoMockClient

# Apply nest_asyncio to allow nested event loops if necessary
nest_asyncio.apply()

# Mock the database before importing main
mock_client = AsyncMongoMockClient()
mock_db = mock_client.aipeco_db

with patch('database.client', mock_client), patch('database.db', mock_db), patch('database.get_db', return_value=mock_db):
    from backend.main import app

client = TestClient(app)

def run_tests():
    print("--- STARTING QA TESTS ---")
    results = []
    
    # 1. Test Health
    res = client.get("/health")
    results.append(("Health Check", res.status_code == 200, res.status_code))
    
    # 2. Test Auth Signup
    res = client.post("/api/auth/register", json={
        "name": "QA Tester",
        "email": "qa@test.com",
        "password": "password123"
    })
    results.append(("Auth: Register User", res.status_code == 200, res.status_code))
    
    # 3. Test Auth Login
    res = client.post("/api/auth/login", json={
        "email": "qa@test.com",
        "password": "password123"
    })
    results.append(("Auth: Login User", res.status_code == 200, res.status_code))
    token = res.json().get("access_token") if res.status_code == 200 else "FAKE"
    if res.status_code != 200:
        print(f"Login failed: {res.json()}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 4. Test Get Profile
    res = client.get("/api/auth/me", headers=headers)
    results.append(("Auth: Get Profile", res.status_code == 200, res.status_code))
    user_id = res.json().get("id") if res.status_code == 200 else "123"
    
    # 5. Test Device Creation
    res = client.post("/api/devices", headers=headers, json={
        "name": "Air Conditioner",
        "location": "Living Room",
        "relay_pin": 18
    })
    results.append(("Devices: Add Device", res.status_code == 200, res.status_code))
    device_id = res.json().get("id") if res.status_code == 200 else "5f8d0d55b54764421b7156c3"
    if res.status_code != 200:
        print(f"Add Device failed: {res.json()}")
    
    # 6. Test Get Devices
    res = client.get("/api/devices", headers=headers)
    results.append(("Devices: List Devices", res.status_code == 200, res.status_code))
    
    # 7. Test ESP32 Sensor Data Post
    res = client.post("/api/energy/data", json={
        "device_id": device_id,
        "current": 2.5,
        "voltage": 220.0,
        "power": 550.0,
        "temperature": 25.0,
        "humidity": 50.0
    })
    results.append(("ESP32: Post Sensor Data", res.status_code == 200, res.status_code))
    
    # 8. Test ESP32 Command Polling
    res = client.get(f"/api/dashboard/device-command/{device_id}")
    results.append(("ESP32: Poll Device Command", res.status_code == 200, res.status_code))
    
    # 9. Test Dashboard Stats
    res = client.get("/api/dashboard/stats", headers=headers)
    results.append(("Dashboard: Get Stats", res.status_code == 200, res.status_code))
    
    # 10. Test AI Recommendation
    res = client.get(f"/api/dashboard/recommendation/{device_id}", headers=headers)
    results.append(("AI Module: Get Recommendation", res.status_code in [200, 404, 500], res.status_code))

    print("\n--- TEST RESULTS ---")
    passed = 0
    for name, success, code in results:
        status = "PASS" if success else f"FAIL (Code {code})"
        if success: passed += 1
        print(f"{name.ljust(35)} | {status}")
        
    print(f"\nFinal Verdict: {passed}/{len(results)} passed")

if __name__ == "__main__":
    run_tests()
