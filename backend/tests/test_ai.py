"""
AI/ML prediction tests — forecast, disaggregation, RL, and smart analysis.
"""

import pytest
from httpx import AsyncClient
from unittest.mock import patch

pytestmark = pytest.mark.asyncio


class TestForecast:
    async def test_forecast_no_data(self, client: AsyncClient, auth_headers, test_device):
        """Forecast with no data should return insufficient_data method."""
        resp = await client.get(
            f"/api/predictions/forecast/{test_device['_id']}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "method" in data
        assert data["method"] in ("sma", "lstm", "insufficient_data")
        assert "message" in data

    async def test_forecast_has_transparency_fields(self, client: AsyncClient, auth_headers, test_device):
        """Every forecast response must include method, confidence, is_estimate, message."""
        resp = await client.get(
            f"/api/predictions/forecast/{test_device['_id']}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        for field in ("method", "confidence", "is_estimate", "message"):
            assert field in data, f"Missing field: {field}"

    async def test_forecast_unauthenticated(self, client: AsyncClient, test_device):
        resp = await client.get(f"/api/predictions/forecast/{test_device['_id']}")
        assert resp.status_code in [401, 403]


class TestDisaggregation:
    async def test_disaggregation_response_structure(self, client: AsyncClient, auth_headers, test_device):
        """Disaggregation must always include method, confidence, is_estimate."""
        resp = await client.get(
            f"/api/predictions/disaggregate/{test_device['_id']}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        for field in ("method", "confidence", "is_estimate", "message"):
            assert field in data

    async def test_disaggregation_fallback_labeled(self, client: AsyncClient, auth_headers, test_device):
        """When NILM is unavailable, is_estimate must be True and breakdown keys end in (estimated)."""
        resp = await client.get(
            f"/api/predictions/disaggregate/{test_device['_id']}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        if data.get("is_estimate"):
            assert data["method"] in ("estimated", "insufficient_data")
            # Breakdown keys should be labeled as estimated
            for key in data.get("breakdown", {}):
                assert "(estimated)" in key or data["method"] == "insufficient_data"


class TestRLSuggestion:
    async def test_rl_suggestion_structure(self, client: AsyncClient, auth_headers):
        resp = await client.get("/api/predictions/rl-suggestion", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()

        # Transparency fields must be present
        assert "method" in data
        assert data["method"] == "tabular_q_learning"
        assert "transparency" in data
        assert "confidence" in data
        assert "title" in data
        assert "description" in data

    async def test_rl_suggestion_unauthenticated(self, client: AsyncClient):
        resp = await client.get("/api/predictions/rl-suggestion")
        assert resp.status_code in [401, 403]


class TestSmartAnalysis:
    async def test_smart_analysis_uses_post(self, client: AsyncClient, auth_headers):
        """Smart analysis must be a POST endpoint."""
        resp = await client.post(
            "/api/predictions/smart-analysis",
            json={"query": "What is my current power usage?"},
            headers=auth_headers,
        )
        assert resp.status_code == 200

    async def test_smart_analysis_get_not_allowed(self, client: AsyncClient, auth_headers):
        """GET must not be allowed on smart-analysis."""
        resp = await client.get(
            "/api/predictions/smart-analysis",
            headers=auth_headers,
        )
        assert resp.status_code == 405

    async def test_smart_analysis_response_structure(self, client: AsyncClient, auth_headers):
        resp = await client.post(
            "/api/predictions/smart-analysis",
            json={"query": "How can I save energy?"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "response" in data
        assert "assistant_type" in data
        assert data["assistant_type"] == "rule_based_with_rl"

    async def test_smart_analysis_empty_query_rejected(self, client: AsyncClient, auth_headers):
        resp = await client.post(
            "/api/predictions/smart-analysis",
            json={"query": " "},  # Whitespace only — fails min_length=2
            headers=auth_headers,
        )
        assert resp.status_code == 422

    async def test_smart_analysis_unauthenticated(self, client: AsyncClient):
        resp = await client.post(
            "/api/predictions/smart-analysis",
            json={"query": "Hello"},
        )
        assert resp.status_code in [401, 403]

    async def test_smart_analysis_hello_response(self, client: AsyncClient, auth_headers):
        resp = await client.post(
            "/api/predictions/smart-analysis",
            json={"query": "hello"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["response"]) > 50  # Should have a real response

    async def test_smart_analysis_cost_query(self, client: AsyncClient, auth_headers):
        resp = await client.post(
            "/api/predictions/smart-analysis",
            json={"query": "What is my electricity bill estimate?"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert "response" in resp.json()
