"""
Auth route tests — covers registration, login, profile, and password reset.
"""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestRegister:
    async def test_register_success(self, client: AsyncClient):
        resp = await client.post("/api/auth/register", json={
            "name": "New User",
            "email": "newuser@test.com",
            "password": "NewPass123!",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "newuser@test.com"
        assert data["role"] == "user"
        assert "id" in data

    async def test_register_duplicate_email(self, client: AsyncClient, test_user):
        resp = await client.post("/api/auth/register", json={
            "name": "Duplicate",
            "email": test_user["email"],
            "password": "AnotherPass123!",
        })
        assert resp.status_code == 400

    async def test_register_weak_password(self, client: AsyncClient):
        resp = await client.post("/api/auth/register", json={
            "name": "Weak",
            "email": "weak@test.com",
            "password": "short",  # Too short
        })
        assert resp.status_code == 422

    async def test_register_invalid_email(self, client: AsyncClient):
        resp = await client.post("/api/auth/register", json={
            "name": "Bad Email",
            "email": "not-an-email",
            "password": "GoodPass123!",
        })
        assert resp.status_code == 422


class TestLogin:
    async def test_login_success(self, client: AsyncClient, test_user):
        resp = await client.post("/api/auth/login", json={
            "email": test_user["email"],
            "password": "TestPass123!",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client: AsyncClient, test_user):
        resp = await client.post("/api/auth/login", json={
            "email": test_user["email"],
            "password": "WrongPassword1!",
        })
        assert resp.status_code == 401

    async def test_login_unknown_email(self, client: AsyncClient):
        resp = await client.post("/api/auth/login", json={
            "email": "nobody@test.com",
            "password": "Whatever123!",
        })
        assert resp.status_code == 401


class TestProfile:
    async def test_get_profile_authenticated(self, client: AsyncClient, auth_headers):
        resp = await client.get("/api/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert "email" in data
        assert "password_hash" not in data  # Never expose hash

    async def test_get_profile_unauthenticated(self, client: AsyncClient):
        resp = await client.get("/api/auth/me")
        assert resp.status_code in [401, 403]  # Missing credentials → HTTPBearer returns 403

    async def test_get_profile_invalid_token(self, client: AsyncClient):
        resp = await client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert resp.status_code == 401


class TestForgotPassword:
    async def test_forgot_password_existing_email(self, client: AsyncClient, test_user):
        """Always returns 200 to prevent email enumeration."""
        resp = await client.post(
            "/api/auth/forgot-password",
            json={"email": test_user["email"]},
        )
        assert resp.status_code == 200
        # Token must NOT be in response body
        assert "token" not in resp.json()
        assert "reset" not in resp.text.lower().replace("reset link", "")

    async def test_forgot_password_nonexistent_email(self, client: AsyncClient):
        """Must return 200 for non-existing email too (anti-enumeration)."""
        resp = await client.post(
            "/api/auth/forgot-password",
            json={"email": "ghost@test.com"},
        )
        assert resp.status_code == 200

    async def test_forgot_password_token_not_in_response(self, client: AsyncClient, test_user, mock_db):
        """Ensure the reset token is not returned via API."""
        resp = await client.post(
            "/api/auth/forgot-password",
            json={"email": test_user["email"]},
        )
        response_text = resp.text
        # Fetch the token from DB to make sure it's NOT in the response
        from bson import ObjectId
        updated_user = await mock_db.users.find_one({"_id": test_user["_id"]})
        if updated_user and updated_user.get("reset_token"):
            assert updated_user["reset_token"] not in response_text


class TestResetPassword:
    async def test_reset_password_invalid_token(self, client: AsyncClient):
        resp = await client.post("/api/auth/reset-password", json={
            "token": "this-is-not-a-valid-token",
            "new_password": "NewPass123!",
        })
        assert resp.status_code == 400

    async def test_reset_password_weak_password(self, client: AsyncClient):
        resp = await client.post("/api/auth/reset-password", json={
            "token": "anytoken",
            "new_password": "nouppercase1",  # No uppercase
        })
        assert resp.status_code == 422

    async def test_reset_password_no_digit(self, client: AsyncClient):
        resp = await client.post("/api/auth/reset-password", json={
            "token": "anytoken",
            "new_password": "NoDigitHere!",  # No digit
        })
        assert resp.status_code == 422


class TestAdminProtection:
    async def test_admin_route_rejected_for_regular_user(self, client: AsyncClient, auth_headers):
        resp = await client.get("/api/auth/users", headers=auth_headers)
        assert resp.status_code in [401, 403]

    async def test_admin_route_accessible_for_admin(self, client: AsyncClient, admin_headers):
        resp = await client.get("/api/auth/users", headers=admin_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
