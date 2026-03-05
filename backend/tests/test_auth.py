import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "app": "AI-PECO API"}

def test_register_user_validation():
    # Test invalid registration (missing fields)
    response = client.post("/api/auth/register", json={"email": "test@example.com"})
    assert response.status_code == 422 # Unprocessable Entity
    
def test_login_invalid_credentials():
    response = client.post("/api/auth/login", json={"email": "wrong@test.com", "password": "bad"})
    # It might be 401 or 404 depending on auth service
    assert response.status_code in [401, 404]
