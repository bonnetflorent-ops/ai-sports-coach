# -*- coding: utf-8 -*-
"""Tests for src/api/athlete.py"""
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.athlete import router as athlete_router
from src.api.dependencies import get_current_user

# Create test app
app = FastAPI()
app.include_router(athlete_router)

# Default user fixture
TEST_USER = {
    "id": "test-user-id",
    "email": "test@example.com",
    "first_name": "Test",
}

client = TestClient(app)


@pytest.fixture
def auth_override():
    """Override auth dependency to return TEST_USER."""
    app.dependency_overrides[get_current_user] = lambda: TEST_USER
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def mock_db():
    """Mock athlete_models and athlete_model engine."""
    with (
        patch("src.api.athlete.get_latest_model") as mock_get,
        patch("src.api.athlete.save_model_version") as mock_save,
        patch("src.api.athlete.create_initial_model") as mock_create,
    ):
        yield {
            "get_latest_model": mock_get,
            "save_model_version": mock_save,
            "create_initial_model": mock_create,
        }


class TestGetModel:
    def test_get_model_no_auth(self):
        """GET /api/athlete/model without auth should return 401."""
        response = client.get("/api/athlete/model")
        assert response.status_code == 401

    def test_get_model_creates_default(self, auth_override, mock_db):
        """GET /api/athlete/model when none exists should create and return default."""
        # Model doesn't exist yet
        mock_db["get_latest_model"].return_value = None

        # Simulate create_initial_model
        initial = {
            "physique": {},
            "etat_actuel": {},
            "blessures": [],
            "patterns": [],
            "preferences": {},
            "objectifs": {
                "actuel": None,
                "jalons_atteints": [],
                "prochains_jalons": [],
            },
            "contradictions": [],
            "meta": {
                "derniere_mise_a_jour": "2025-01-01T00:00:00",
                "nb_sessions_totales": 0,
                "date_premiere_session": "2025-01-01T00:00:00",
                "version_modele": 1,
            },
        }
        mock_db["create_initial_model"].return_value = initial

        # save_model_version returns the saved record
        saved = dict(initial)
        saved["user_id"] = TEST_USER["id"]
        saved["version"] = 1
        mock_db["save_model_version"].return_value = saved

        response = client.get("/api/athlete/model")

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == TEST_USER["id"]
        assert data["version"] == 1
        mock_db["create_initial_model"].assert_called_once()
        mock_db["save_model_version"].assert_called_once()


class TestBadge:
    def test_badge_no_auth(self):
        """GET /api/athlete/badge without auth should return 401."""
        response = client.get("/api/athlete/badge")
        assert response.status_code == 401

    def test_badge_with_model(self, auth_override, mock_db):
        """GET /api/athlete/badge should return count and level."""
        mock_db["get_latest_model"].return_value = {
            "user_id": TEST_USER["id"],
            "version": 5,
            "model_json": {
                "meta": {"nb_sessions_totales": 12},
            },
        }

        response = client.get("/api/athlete/badge")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 12
        assert data["level"] == "\U0001f948"  # 🥈 (10-24)

    def test_badge_no_model(self, auth_override, mock_db):
        """GET /api/athlete/badge with no model should return count=0."""
        mock_db["get_latest_model"].return_value = None

        response = client.get("/api/athlete/badge")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["level"] == "\U0001f949"  # 🥉 (<10)
