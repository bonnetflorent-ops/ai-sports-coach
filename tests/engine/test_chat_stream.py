# -*- coding: utf-8 -*-
"""Tests for src/engine/chat_stream.py"""
import json

from src.engine.chat_stream import format_sse_event


def test_format_sse_event_token():
    """format_sse_event should produce a valid SSE token event."""
    result = format_sse_event("token", {"token": "Hello"})
    assert result.startswith("event: token")
    assert "data: " in result
    assert result.endswith("\n\n")

    # Parse the data portion
    data_line = result.split("data: ", 1)[1].strip()
    data = json.loads(data_line)
    assert data["token"] == "Hello"


def test_format_sse_event_complete():
    """format_sse_event should produce a valid message_complete event."""
    result = format_sse_event("message_complete", {"content": "Full response"})
    assert result.startswith("event: message_complete")

    data_line = result.split("data: ", 1)[1].strip()
    data = json.loads(data_line)
    assert data["content"] == "Full response"


def test_format_sse_event_error():
    """format_sse_event should produce a valid error event."""
    result = format_sse_event("error", {"detail": "Something went wrong"})
    assert result.startswith("event: error")

    data_line = result.split("data: ", 1)[1].strip()
    data = json.loads(data_line)
    assert data["detail"] == "Something went wrong"


def test_format_sse_event_with_unicode():
    """format_sse_event should handle Unicode characters."""
    result = format_sse_event("token", {"token": "Bonjour l'athlète"})
    assert "Bonjour l'athlète" in result


def test_format_sse_event_with_empty_data():
    """format_sse_event should handle empty data dict."""
    result = format_sse_event("test", {})
    assert result.startswith("event: test")
    data_line = result.split("data: ", 1)[1].strip()
    assert json.loads(data_line) == {}
