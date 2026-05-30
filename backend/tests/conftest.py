"""
Shared pytest fixtures for AI-PECO backend tests.
Uses mongomock-motor for an in-memory database that doesn't require
a real MongoDB connection.
"""

import pytest
import pytest_asyncio
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from bson import ObjectId
from datetime import datetime

# ── Test event loop ────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def event_loop():
    """Create a session-scoped event loop."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ── In-memory database ─────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def mock_db():
    """Provide an in-memory MongoDB instance for testing."""
    from mongomock_motor import AsyncMongoMockClient
    client = AsyncMongoMockClient()
    db = client["test_db"]

    # Create indexes
    await db.users.create_index("email", unique=True)
    await db.devices.create_index("user_id")
    await db.energy_data.create_index([("device_id", 1), ("timestamp", -1)])

    yield db

    # Cleanup
    client.close()


# ── Test application ───────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def app(mock_db):
    """Create a FastAPI test application with mock DB injected."""
    import database

    # Patch the module-level DB instance
    with patch.object(database, "_db", mock_db):
        with patch.object(database, "_client", AsyncMock()):
            from main import app as fastapi_app
            from utils.rate_limit import limiter
            limiter.enabled = False
            yield fastapi_app


@pytest_asyncio.fixture
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


# ── Test data ──────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def test_user(mock_db) -> dict:
    """Create and return a test user document."""
    from utils.password import hash_password

    user_doc = {
        "_id": ObjectId(),
        "name": "Test User",
        "email": "test@aipeco.com",
        "password_hash": hash_password("TestPass123!"),
        "role": "user",
        "energy_limit": 50.0,
        "is_active": True,
        "created_at": datetime.utcnow(),
    }
    await mock_db.users.insert_one(user_doc)
    return user_doc


@pytest_asyncio.fixture
async def test_admin(mock_db) -> dict:
    """Create and return a test admin document."""
    from utils.password import hash_password

    admin_doc = {
        "_id": ObjectId(),
        "name": "Test Admin",
        "email": "admin@aipeco.com",
        "password_hash": hash_password("AdminPass123!"),
        "role": "admin",
        "energy_limit": 100.0,
        "is_active": True,
        "created_at": datetime.utcnow(),
    }
    await mock_db.users.insert_one(admin_doc)
    return admin_doc


@pytest_asyncio.fixture
async def test_device(mock_db, test_user) -> dict:
    """Create and return a test device belonging to test_user."""
    device_doc = {
        "_id": ObjectId(),
        "user_id": test_user["_id"],
        "name": "Test AC Unit",
        "location": "Living Room",
        "relay_pin": 14,
        "status": "online",
        "is_relay_on": False,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    await mock_db.devices.insert_one(device_doc)
    return device_doc


@pytest_asyncio.fixture
async def auth_headers(client, test_user) -> dict:
    """Return Authorization headers for test_user."""
    response = await client.post(
        "/api/auth/login",
        json={"email": test_user["email"], "password": "TestPass123!"},
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def admin_headers(client, test_admin) -> dict:
    """Return Authorization headers for test_admin."""
    response = await client.post(
        "/api/auth/login",
        json={"email": test_admin["email"], "password": "AdminPass123!"},
    )
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
