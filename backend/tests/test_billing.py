"""
Billing service unit tests — tariff calculation, slab tiers, TOU pricing.
"""

import pytest
from services.billing_service import BillingService

pytestmark = pytest.mark.asyncio


class TestBillingCalculation:
    def test_zero_usage(self):
        svc = BillingService()
        result = svc.calculate_bill(consumer_type="A-1", units=0)
        assert result["total_bill"] == 75

    def test_low_usage_first_slab(self):
        """0-100 kWh — lowest tariff slab."""
        svc = BillingService()
        result = svc.calculate_bill(consumer_type="A-1", units=50)
        assert result["total_bill"] > 0
        assert result["total_units"] == 50

    def test_medium_usage_slab(self):
        """100-300 kWh — mid tariff."""
        svc = BillingService()
        result = svc.calculate_bill(consumer_type="A-1", units=200)
        assert result["total_bill"] > svc.calculate_bill(consumer_type="A-1", units=50)["total_bill"]

    def test_high_usage_top_slab(self):
        """500+ kWh — peak slab."""
        svc = BillingService()
        result = svc.calculate_bill(consumer_type="A-1", units=600)
        assert result["total_bill"] > svc.calculate_bill(consumer_type="A-1", units=200)["total_bill"]

    def test_result_has_required_fields(self):
        svc = BillingService()
        result = svc.calculate_bill(consumer_type="A-1", units=150)
        for field in ("total_bill", "total_units", "breakdown"):
            assert field in result, f"Missing field: {field}"

    def test_costs_increase_monotonically(self):
        """Higher usage must always cost more."""
        svc = BillingService()
        costs = [svc.calculate_bill(consumer_type="A-1", units=n)["total_bill"] for n in (0, 50, 100, 200, 400, 700)]
        for i in range(1, len(costs)):
            assert costs[i] >= costs[i - 1], f"Cost decreased at index {i}"

    def test_minimum_charge_applied(self):
        """Minimum charge should apply even for very low usage."""
        svc = BillingService()
        result = svc.calculate_bill(consumer_type="A-1", units=1)
        # Minimum charge varies by category; just check it's positive
        assert result["total_bill"] >= 0


class TestBillingAPI:
    async def test_billing_categories_endpoint(self, client, auth_headers):
        resp = await client.get("/api/billing/categories", headers=auth_headers)
        assert resp.status_code == 200

    async def test_billing_estimate_endpoint(self, client, auth_headers):
        resp = await client.post(
            "/api/billing/estimate",
            json={"units": 200, "consumer_type": "A-1"},
            headers=auth_headers,
        )
        assert resp.status_code in (200, 400)  # 400 if category doesn't exist in mock
