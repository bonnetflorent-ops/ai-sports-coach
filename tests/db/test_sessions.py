# -*- coding: utf-8 -*-
"""Tests for src/db/sessions.py"""

from unittest.mock import MagicMock, patch

from src.db.sessions import get_session_messages


def test_get_session_messages_returns_full_content():
    """get_session_messages should return full content, not truncated."""
    mock_admin = MagicMock()
    mock_admin.table().select().eq().order().limit().execute.return_value = MagicMock(
        data=[
            {"role": "assistant", "content": "Another long message " * 50, "created_at": "2026-01-01T00:01:00Z"},
            {"role": "user", "content": "Long message " * 50, "created_at": "2026-01-01T00:00:00Z"},
        ]
    )

    with patch("src.db.sessions.get_supabase_admin", return_value=mock_admin):
        messages = get_session_messages("fake-session-id", limit=10)

    assert len(messages) == 2
    # Messages should be in chronological order (oldest first)
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"
    # Content should NOT be truncated (no [:200])
    assert len(messages[0]["content"]) > 200


def test_get_session_messages_chronological():
    """Messages should be returned in chronological order (oldest first)."""
    mock_admin = MagicMock()
    mock_admin.table().select().eq().order().limit().execute.return_value = MagicMock(
        data=[
            {"role": "assistant", "content": "3", "created_at": "2026-01-01T00:03:00Z"},
            {"role": "user", "content": "2", "created_at": "2026-01-01T00:02:00Z"},
            {"role": "assistant", "content": "1", "created_at": "2026-01-01T00:01:00Z"},
        ]
    )

    with patch("src.db.sessions.get_supabase_admin", return_value=mock_admin):
        messages = get_session_messages("fake-session-id", limit=10)

    assert len(messages) == 3
    # Should be reversed: oldest first
    assert messages[0]["content"] == "1"
    assert messages[1]["content"] == "2"
    assert messages[2]["content"] == "3"
