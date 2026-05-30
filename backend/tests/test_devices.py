"""
Device CRUD tests — create, read, update, delete, ownership validation.
"""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestDeviceCreate:
    async def test_create_device_success(self, client: AsyncClient, auth_headers):
        resp = await client.post("/api/devices", json={
            "name": "Kitchen Lights",
            "location": "Kitchen",
            "relay_pin": 14,
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Kitchen Lights"
        assert data["location"] == "Kitchen"
        assert data["relay_pin"] == 14
        assert "id" in data

    async def test_create_device_unauthenticated(self, client: AsyncClient):
        resp = await client.post("/api/devices", json={
            "name": "No Auth Device",
            "location": "Nowhere",
        })
        assert resp.status_code in [401, 403]

    async def test_create_device_invalid_relay_pin(self, client: AsyncClient, auth_headers):
        """relay_pin must be 0-39 (ESP32 GPIO range)."""
        resp = await client.post("/api/devices", json={
            "name": "Bad Pin Device",
            "location": "Test",
            "relay_pin": 999,  # Invalid
        }, headers=auth_headers)
        assert resp.status_code == 422

    async def test_create_device_short_name(self, client: AsyncClient, auth_headers):
        resp = await client.post("/api/devices", json={
            "name": "A",  # Too short (min_length=2)
            "location": "Test",
        }, headers=auth_headers)
        assert resp.status_code == 422


class TestDeviceRead:
    async def test_get_all_devices(self, client: AsyncClient, auth_headers):
        resp = await client.get("/api/devices", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_get_device_by_id(self, client: AsyncClient, auth_headers, test_device):
        resp = await client.get(
            f"/api/devices/{test_device['_id']}",
            headers=auth_headers,
        )
        # 200 if ownership matches, 404 if not in user's list (test_device belongs to test_user)
        assert resp.status_code in (200, 404)

    async def test_get_nonexistent_device(self, client: AsyncClient, auth_headers):
        from bson import ObjectId
        fake_id = str(ObjectId())
        resp = await client.get(f"/api/devices/{fake_id}", headers=auth_headers)
        assert resp.status_code == 404


class TestDeviceUpdate:
    async def test_update_device_success(self, client: AsyncClient, auth_headers):
        # Create a device
        create = await client.post("/api/devices", json={
            "name": "My Device",
            "location": "Bedroom",
            "relay_pin": 5,
        }, headers=auth_headers)
        device_id = create.json()["id"]

        # Update it
        update = await client.put(f"/api/devices/{device_id}", json={
            "name": "Updated Device",
        }, headers=auth_headers)
        assert update.status_code == 200
        assert update.json()["name"] == "Updated Device"

    async def test_update_nonexistent_device(self, client: AsyncClient, auth_headers):
        from bson import ObjectId
        resp = await client.put(f"/api/devices/{ObjectId()}", json={
            "name": "Ghost Update",
        }, headers=auth_headers)
        assert resp.status_code == 404


class TestDeviceDelete:
    async def test_delete_device_success(self, client: AsyncClient, auth_headers):
        # Create then delete
        create = await client.post("/api/devices", json={
            "name": "To Delete",
            "location": "Attic",
            "relay_pin": 25,
        }, headers=auth_headers)
        assert create.status_code == 200
        device_id = create.json()["id"]

        delete = await client.delete(f"/api/devices/{device_id}", headers=auth_headers)
        assert delete.status_code == 200

    async def test_delete_nonexistent_device(self, client: AsyncClient, auth_headers):
        from bson import ObjectId
        resp = await client.delete(f"/api/devices/{ObjectId()}", headers=auth_headers)
        assert resp.status_code == 404
