# -*- coding: utf-8 -*-
"""Tests for session summarization (B2-B5)."""

import pytest
from unittest.mock import MagicMock, patch

from src.db.sessions import get_recent_summaries


def test_get_recent_summaries_returns_summaries():
    """get_recent_summaries should return session summaries."""
    mock_admin = MagicMock()

    # First call: user lookup
    mock_admin.table().select().eq().execute.return_value = MagicMock(
        data=[{"id": "user-1"}]
    )

    # Second call: session summaries
    mock_admin.table().select().eq().not_.is_().order().limit().execute.return_value = MagicMock(
        data=[
            {"started_at": "2026-05-20T10:00:00Z", "session_summary": "Summary 1"},
            {"started_at": "2026-05-19T10:00:00Z", "session_summary": "Summary 2"},
        ]
    )

    with patch("src.db.sessions.get_supabase_admin", return_value=mock_admin):
        summaries = get_recent_summaries(123456)

    assert len(summaries) == 2
    assert summaries[0]["session_summary"] == "Summary 1"
    assert summaries[1]["session_summary"] == "Summary 2"


def test_get_recent_summaries_user_not_found():
    """Should return empty list if user not found."""
    mock_admin = MagicMock()
    mock_admin.table().select().eq().execute.return_value = MagicMock(data=[])

    with patch("src.db.sessions.get_supabase_admin", return_value=mock_admin):
        summaries = get_recent_summaries(999999)

    assert summaries == []


def test_get_recent_summaries_no_summaries():
    """Should return empty list if no sessions have summaries."""
    mock_admin = MagicMock()

    mock_admin.table().select().eq().execute.return_value = MagicMock(
        data=[{"id": "user-1"}]
    )
    mock_admin.table().select().eq().not_.is_().order().limit().execute.return_value = MagicMock(
        data=[]
    )

    with patch("src.db.sessions.get_supabase_admin", return_value=mock_admin):
        summaries = get_recent_summaries(123456)

    assert summaries == []
