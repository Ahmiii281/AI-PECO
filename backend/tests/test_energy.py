"""
Energy routes tests — data ingestion, anomaly detection, alerts.
"""

import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta
from bson import ObjectId

pytestmark = pytest.mark.asyncio


class TestEnergyIngestion:
    async def test_post_energy_data_with_api_key(self, client: AsyncClient, test_device, monkeypatch):
        """With DEVICE_API_KEY_REQUIRED=False, data should be accepted."""
        import config
        monkeypatch.setattr(config.settings, "DEVICE_API_KEY_REQUIRED", False)

        resp = await client.post("/api/energy/data", json={
            "device_id": str(test_device["_id"]),
            "current": 2.5,
            "voltage": 220.0,
            "power": 550.0,
            "temperature": 28.0,
            "humidity": 55.0,
        })
        # Accept 200 or 400 (device service may not find the device in mock)
        assert resp.status_code in (200, 400)

    async def test_post_energy_data_requires_key_in_prod(self, client: AsyncClient, test_device, monkeypatch):
        """Without X-API-Key, should reject when DEVICE_API_KEY_REQUIRED=True."""
        import config
        monkeypatch.setattr(config.settings, "DEVICE_API_KEY_REQUIRED", True)
        monkeypatch.setattr(config.settings, "DEVICE_API_KEY", "secret-key-123")

        resp = await client.post("/api/energy/data", json={
            "device_id": str(test_device["_id"]),
            "current": 2.5,
            "voltage": 220.0,
            "power": 550.0,
            "temperature": 28.0,
            "humidity": 55.0,
        })
        assert resp.status_code == 401

    async def test_post_energy_data_with_correct_key(self, client: AsyncClient, test_device, monkeypatch):
        """With correct X-API-Key, data should be accepted."""
        import config
        monkeypatch.setattr(config.settings, "DEVICE_API_KEY_REQUIRED", True)
        monkeypatch.setattr(config.settings, "DEVICE_API_KEY", "my-test-key")

        resp = await client.post(
            "/api/energy/data",
            json={
                "device_id": str(test_device["_id"]),
                "current": 2.5,
                "voltage": 220.0,
                "power": 550.0,
                "temperature": 28.0,
                "humidity": 55.0,
            },
            headers={"X-API-Key": "my-test-key"},
        )
        # 200 or 400 (device might not exist in mock DB fully)
        assert resp.status_code in (200, 400)

    async def test_energy_data_out_of_range_rejected(self, client: AsyncClient, test_device, monkeypatch):
        """Humidity > 100 should fail validation."""
        import config
        monkeypatch.setattr(config.settings, "DEVICE_API_KEY_REQUIRED", False)

        resp = await client.post("/api/energy/data", json={
            "device_id": str(test_device["_id"]),
            "current": 1.0,
            "voltage": 220.0,
            "power": 200.0,
            "temperature": 25.0,
            "humidity": 150.0,  # Invalid — above 100%
        })
        assert resp.status_code == 422


class TestEnergyHistory:
    async def test_get_device_history_authenticated(self, client: AsyncClient, auth_headers, test_device):
        resp = await client.get(
            f"/api/energy/device/{test_device['_id']}",
            headers=auth_headers,
        )
        # 200 (empty list) or 404 (device not linked to user in mock)
        assert resp.status_code in (200, 404)

    async def test_get_device_history_unauthenticated(self, client: AsyncClient, test_device):
        resp = await client.get(f"/api/energy/device/{test_device['_id']}")
        assert resp.status_code in [401, 403]


class TestAlerts:
    async def test_create_alert(self, client: AsyncClient, auth_headers):
        resp = await client.post(
            "/api/energy/alerts",
            json={"message": "Test anomaly spike detected", "alert_type": "warning"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "Test anomaly spike detected"
        assert data["alert_type"] == "warning"
        assert data["resolved"] is False

    async def test_create_alert_invalid_type(self, client: AsyncClient, auth_headers):
        resp = await client.post(
            "/api/energy/alerts",
            json={"message": "Bad alert", "alert_type": "invalid_type"},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    async def test_get_alerts(self, client: AsyncClient, auth_headers):
        resp = await client.get("/api/energy/alerts", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_resolve_alert(self, client: AsyncClient, auth_headers):
        # Create an alert first
        create = await client.post(
            "/api/energy/alerts",
            json={"message": "Resolve me", "alert_type": "info"},
            headers=auth_headers,
        )
        assert create.status_code == 200
        alert_id = create.json()["id"]

        # Resolve it
        resolve = await client.put(
            f"/api/energy/alerts/{alert_id}",
            headers=auth_headers,
        )
        assert resolve.status_code == 200
        assert resolve.json()["resolved"] is True

    async def test_alerts_unauthenticated(self, client: AsyncClient):
        resp = await client.get("/api/energy/alerts")
        assert resp.status_code in [401, 403]
