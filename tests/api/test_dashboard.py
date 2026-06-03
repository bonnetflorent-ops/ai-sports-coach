# -*- coding: utf-8 -*-
"""Tests for src/api/dashboard.py"""
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.dashboard import router as dashboard_router
from src.api.dependencies import get_current_user

# Create test app
app = FastAPI()
app.include_router(dashboard_router)

# Default user fixture
TEST_USER = {
    "id": "test-user-id",
    "email": "test@example.com",
    "first_name": "Test",
}

client = TestClient(app)


class TestMetrics:
    def test_metrics_no_auth(self):
        """GET /api/dashboard/metrics without auth should return 401."""
        response = client.get("/api/dashboard/metrics")
        assert response.status_code == 401


class TestChart:
    def test_chart_no_auth(self):
        """GET /api/dashboard/chart without auth should return 401."""
        response = client.get("/api/dashboard/chart?period=7d")
        assert response.status_code == 401


class TestRecap:
    def test_recap_no_auth(self):
        """GET /api/dashboard/recap without auth should return 401."""
        response = client.get("/api/dashboard/recap")
        assert response.status_code == 401
