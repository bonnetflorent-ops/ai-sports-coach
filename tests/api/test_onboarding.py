# -*- coding: utf-8 -*-
"""Tests for src/api/onboarding.py"""
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.onboarding import router as onboarding_router
from src.api.dependencies import get_current_user

# Create test app
app = FastAPI()
app.include_router(onboarding_router)

# Default user fixture
TEST_USER = {
    "id": "test-user-id",
    "email": "test@example.com",
    "first_name": "Test",
}

client = TestClient(app)


class TestPhase1:
    def test_phase1_no_auth(self):
        """POST /api/onboarding/phase1 without auth should return 401."""
        response = client.post(
            "/api/onboarding/phase1",
            json={
                "sport": "running",
                "level": "intermediaire",
                "goal": "amelioration",
                "injuries": "aucune",
                "equipment": "baskets",
                "slots": "3",
            },
        )
        assert response.status_code == 401


class TestPhase2:
    def test_phase2_no_auth(self):
        """POST /api/onboarding/phase2 without auth should return 401."""
        response = client.post(
            "/api/onboarding/phase2",
            json={"weight": 70.0, "height": 175.0, "age": 30, "gender": "homme"},
        )
        assert response.status_code == 401


class TestParq:
    def test_parq_no_auth(self):
        """POST /api/onboarding/parq without auth should return 401."""
        response = client.post(
            "/api/onboarding/parq",
            json={
                "items": [
                    {"question": "Q1", "answer": False},
                    {"question": "Q2", "answer": False},
                    {"question": "Q3", "answer": False},
                    {"question": "Q4", "answer": False},
                    {"question": "Q5", "answer": False},
                    {"question": "Q6", "answer": False},
                    {"question": "Q7", "answer": False},
                ]
            },
        )
        assert response.status_code == 401
