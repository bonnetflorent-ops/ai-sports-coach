# -*- coding: utf-8 -*-
"""Tests for src/api/auth.py"""
import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Need to create a minimal app for testing
from fastapi import FastAPI
from src.api.auth import router as auth_router

# Create test app
app = FastAPI()
app.include_router(auth_router)

client = TestClient(app)


@pytest.fixture
def mock_supabase():
    """Fixture for mocking Supabase clients at all import locations."""
    admin_client = MagicMock()
    anon_client = MagicMock()

    with (
        patch("src.api.auth.get_supabase_admin", return_value=admin_client),
        patch("src.api.auth.get_supabase", return_value=anon_client),
        patch("src.db.users.get_supabase_admin", return_value=admin_client),
    ):
        yield {
            "admin": admin_client,
            "anon": anon_client,
        }


class TestRegister:
    def test_register_success(self, mock_supabase):
        """Register should return 201 with access_token on success."""
        admin = mock_supabase["admin"]
        anon = mock_supabase["anon"]

        # Mock admin.create_user
        mock_user = MagicMock()
        mock_user.user.id = "test-uuid-123"
        mock_user.user.email = "test@example.com"
        admin.auth.admin.create_user.return_value = mock_user

        # Mock users table query (email check returns empty)
        admin.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[]
        )

        # Mock user insert
        admin.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{"id": "test-uuid-123", "email": "test@example.com", "first_name": "Test"}]
        )

        # Mock sign_in after register (supabase-py 2.x: session est imbriqué)
        mock_response = MagicMock()
        mock_response.session.access_token = "access-token-123"
        mock_response.session.refresh_token = "refresh-token-456"
        anon.auth.sign_in_with_password.return_value = mock_response

        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "password123",
                "first_name": "Test",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["access_token"] == "access-token-123"
        assert data["refresh_token"] == "refresh-token-456"
        assert data["user"]["email"] == "test@example.com"

    def test_register_duplicate_email(self, mock_supabase):
        """Register with existing email should return 409."""
        admin = mock_supabase["admin"]

        # Mock users table query (email exists)
        admin.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": "existing-uuid", "email": "existing@example.com", "first_name": "Existing"}]
        )

        response = client.post(
            "/api/auth/register",
            json={
                "email": "existing@example.com",
                "password": "password123",
                "first_name": "Test",
            },
        )

        assert response.status_code == 409

    def test_register_invalid_email(self):
        """Register with invalid email should return 422."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "invalid-email",
                "password": "password123",
                "first_name": "Test",
            },
        )
        assert response.status_code == 422

    def test_register_short_password(self):
        """Register with password < 8 chars should return 422."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "short",
                "first_name": "Test",
            },
        )
        assert response.status_code == 422


class TestLogin:
    def test_login_success(self, mock_supabase):
        """Login with correct credentials should return 200 with tokens."""
        anon = mock_supabase["anon"]
        admin = mock_supabase["admin"]

        # Mock sign_in (supabase-py 2.x: session est imbriqué)
        mock_response = MagicMock()
        mock_response.session.access_token = "access-token-789"
        mock_response.session.refresh_token = "refresh-token-000"
        mock_response.session.user.id = "user-uuid"
        mock_response.session.user.email = "test@example.com"
        anon.auth.sign_in_with_password.return_value = mock_response

        # Mock get_user_by_id (called to get full profile)
        admin.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": "user-uuid", "email": "test@example.com", "first_name": "Test"}]
        )

        response = client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "password123",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "access-token-789"
        assert data["refresh_token"] == "refresh-token-000"

    def test_login_wrong_password(self, mock_supabase):
        """Login with wrong password should return 401."""
        anon = mock_supabase["anon"]

        # Mock sign_in to raise exception
        anon.auth.sign_in_with_password.side_effect = Exception("Invalid login credentials")

        response = client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "wrongpassword",
            },
        )

        assert response.status_code == 401


class TestRefresh:
    def test_refresh_token(self, mock_supabase):
        """Refresh with valid token should return new tokens."""
        anon = mock_supabase["anon"]

        # Mock refresh_session (supabase-py 2.x: session est imbriqué)
        mock_response = MagicMock()
        mock_response.session.access_token = "new-access-token"
        mock_response.session.refresh_token = "new-refresh-token"
        mock_response.session.user.id = "user-uuid"
        mock_response.session.user.email = "test@example.com"
        anon.auth.refresh_session.return_value = mock_response

        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": "valid-refresh-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "new-access-token"

    def test_refresh_invalid_token(self, mock_supabase):
        """Refresh with invalid token should return 401."""
        anon = mock_supabase["anon"]

        anon.auth.refresh_session.side_effect = Exception("Invalid refresh token")

        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": "invalid-token"},
        )

        assert response.status_code == 401
