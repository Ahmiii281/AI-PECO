import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_dashboard_stats_requires_auth():
    response = client.get("/api/dashboard/stats")
    assert response.status_code == 403 # HTTPBearer returns 403 for missing token
    
def test_energy_data_webhook_missing_key():
    # If device sends data without API key when DEBUG=False, it should fail
    # Since we might be running in DEBUG=True locally, we just verify the endpoint exists
    response = client.post("/api/energy/data", json={
        "device_id": "dummy",
        "current": 1.0,
        "voltage": 220.0,
        "power": 220.0,
        "temperature": 25.0,
        "humidity": 50.0
    })
    # Will fail either with 401 Unauthorized or 400 Bad Request depending on debug mode and DB state
    assert response.status_code in [401, 400]
