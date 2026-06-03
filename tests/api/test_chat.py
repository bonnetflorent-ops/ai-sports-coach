# -*- coding: utf-8 -*-
"""Tests for src/api/chat.py"""
from unittest.mock import patch, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.chat import router as chat_router

# Create test app with auth dependency override
app = FastAPI()
app.include_router(chat_router)

# We don't override auth for these tests — they test the 401 behavior
client = TestClient(app)


class TestChatMessageNoAuth:
    """Tests for chat endpoints without authentication."""

    def test_chat_message_no_auth(self):
        """POST /api/chat/message without auth should return 401."""
        response = client.post(
            "/api/chat/message",
            json={"message": "Hello"},
        )
        assert response.status_code == 401

    def test_chat_history_no_auth(self):
        """GET /api/chat/history without auth should return 401."""
        response = client.get("/api/chat/history")
        assert response.status_code == 401

    def test_chat_sessions_no_auth(self):
        """GET /api/chat/sessions without auth should return 401."""
        response = client.get("/api/chat/sessions")
        assert response.status_code == 401
