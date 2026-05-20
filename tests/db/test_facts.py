# -*- coding: utf-8 -*-
"""Tests for src/db/facts.py"""

import pytest
from unittest.mock import MagicMock, patch

from src.db.facts import (
    add_fact,
    get_facts_by_user,
    get_relevant_facts,
    deduplicate_facts,
    update_fact,
    bump_importance,
    get_fact_by_id,
)


def test_add_fact_basic():
    """add_fact should insert and return a fact dict."""
    mock_admin = MagicMock()
    mock_admin.table().insert().execute.return_value = MagicMock(
        data=[{"id": "fact-1", "fact": "Test fact", "category": "test", "importance": 0.5}]
    )

    with patch("src.db.facts.get_supabase_admin", return_value=mock_admin):
        result = add_fact(
            user_id="user-1",
            fact="Test fact",
            category="test",
            importance=0.5,
        )

    assert result["id"] == "fact-1"
    assert result["fact"] == "Test fact"


def test_add_fact_with_embedding():
    """add_fact should accept an embedding vector."""
    mock_admin = MagicMock()
    mock_admin.table().insert().execute.return_value = MagicMock(
        data=[{"id": "fact-2", "fact": "Emb fact", "embedding": [0.1, 0.2, 0.3]}]
    )

    with patch("src.db.facts.get_supabase_admin", return_value=mock_admin):
        result = add_fact(
            user_id="user-1",
            fact="Emb fact",
            category="profile",
            embedding=[0.1, 0.2, 0.3],
        )

    assert result["id"] == "fact-2"


def test_get_facts_by_user():
    """get_facts_by_user should return facts ordered by importance."""
    mock_admin = MagicMock()
    mock_admin.table().select().eq().order().limit().execute.return_value = MagicMock(
        data=[
            {"id": "f1", "fact": "Important", "importance": 1.0},
            {"id": "f2", "fact": "Less important", "importance": 0.3},
        ]
    )

    with patch("src.db.facts.get_supabase_admin", return_value=mock_admin):
        facts = get_facts_by_user("user-1")

    assert len(facts) == 2
    assert facts[0]["importance"] == 1.0
    assert facts[1]["importance"] == 0.3


def test_get_relevant_facts():
    """get_relevant_facts should call RPC with correct params."""
    mock_admin = MagicMock()
    mock_admin.rpc().execute.return_value = MagicMock(
        data=[
            {"id": "f1", "fact": "Related", "distance": 0.3},
            {"id": "f2", "fact": "Somewhat related", "distance": 0.8},
        ]
    )

    query_emb = [0.1] * 768

    with patch("src.db.facts.get_supabase_admin", return_value=mock_admin):
        facts = get_relevant_facts("user-1", query_emb, limit=2)

    assert len(facts) == 2
    assert facts[0]["distance"] == 0.3
    # Verify RPC was called with correct parameters
    # Note: mock chaining (rpc() in setup) causes an extra initial call,
    # so we use assert_called_with instead of assert_called_once_with
    mock_admin.rpc.assert_called_with(
        "match_user_facts",
        {
            "query_embedding": query_emb,
            "match_user_id": "user-1",
            "match_limit": 2,
        },
    )


def test_deduplicate_facts_finds_duplicate():
    """deduplicate_facts should return True when similar fact exists."""
    mock_admin = MagicMock()
    mock_admin.rpc().execute.return_value = MagicMock(
        data=[
            {"id": "f1", "fact": "I love running", "distance": 0.1},
        ]
    )

    with patch("src.db.facts.get_supabase_admin", return_value=mock_admin), \
         patch("src.engine.embeddings.embed_text", return_value=[0.5] * 768):
        is_dup, existing = deduplicate_facts("user-1", "I love running", threshold=0.85)

    assert is_dup is True
    assert existing["id"] == "f1"


def test_deduplicate_facts_no_duplicate():
    """deduplicate_facts should return False when no similar fact exists."""
    mock_admin = MagicMock()
    mock_admin.rpc().execute.return_value = MagicMock(
        data=[
            {"id": "f1", "fact": "Different", "distance": 0.6},
        ]
    )

    with patch("src.db.facts.get_supabase_admin", return_value=mock_admin), \
         patch("src.engine.embeddings.embed_text", return_value=[0.5] * 768):
        is_dup, existing = deduplicate_facts("user-1", "Completely different", threshold=0.85)

    assert is_dup is False
    assert existing is None


def test_deduplicate_facts_embedding_failed():
    """deduplicate_facts should return False if embedding is all zeros."""
    mock_admin = MagicMock()

    with patch("src.db.facts.get_supabase_admin", return_value=mock_admin), \
         patch("src.engine.embeddings.embed_text", return_value=[0.0] * 768):
        is_dup, existing = deduplicate_facts("user-1", "Some text")

    assert is_dup is False
    assert existing is None
    # RPC should not be called when embedding fails
    mock_admin.rpc.assert_not_called()


def test_update_fact():
    """update_fact should update and return the fact."""
    mock_admin = MagicMock()
    mock_admin.table().update().eq().execute.return_value = MagicMock(
        data=[{"id": "f1", "fact": "Updated fact", "importance": 0.8}]
    )

    with patch("src.db.facts.get_supabase_admin", return_value=mock_admin):
        result = update_fact("f1", {"fact": "Updated fact", "importance": 0.8})

    assert result["fact"] == "Updated fact"
    assert result["importance"] == 0.8


def test_bump_importance():
    """bump_importance should increase importance by increment."""
    mock_admin = MagicMock()
    # First call: get_fact_by_id
    mock_admin.table().select().eq().execute.return_value = MagicMock(
        data=[{"id": "f1", "importance": 0.5, "fact": "test"}]
    )
    # Second call: update_fact
    mock_admin.table().update().eq().execute.return_value = MagicMock(
        data=[{"id": "f1", "importance": 0.6}]
    )

    with patch("src.db.facts.get_supabase_admin", return_value=mock_admin):
        result = bump_importance("f1", increment=0.1)

    assert result["importance"] == 0.6


def test_bump_importance_caps_at_1():
    """bump_importance should not exceed 1.0."""
    mock_admin = MagicMock()
    mock_admin.table().select().eq().execute.return_value = MagicMock(
        data=[{"id": "f1", "importance": 0.95, "fact": "test"}]
    )
    mock_admin.table().update().eq().execute.return_value = MagicMock(
        data=[{"id": "f1", "importance": 1.0}]
    )

    with patch("src.db.facts.get_supabase_admin", return_value=mock_admin):
        result = bump_importance("f1", increment=0.2)

    assert result["importance"] == 1.0


def test_bump_importance_nonexistent():
    """bump_importance should return empty dict for nonexistent fact."""
    mock_admin = MagicMock()
    mock_admin.table().select().eq().execute.return_value = MagicMock(
        data=[]
    )

    with patch("src.db.facts.get_supabase_admin", return_value=mock_admin):
        result = bump_importance("nonexistent")

    assert result == {}


def test_get_fact_by_id_exists():
    """get_fact_by_id should return the fact dict."""
    mock_admin = MagicMock()
    mock_admin.table().select().eq().execute.return_value = MagicMock(
        data=[{"id": "f1", "fact": "Found", "category": "test"}]
    )

    with patch("src.db.facts.get_supabase_admin", return_value=mock_admin):
        result = get_fact_by_id("f1")

    assert result is not None
    assert result["id"] == "f1"


def test_get_fact_by_id_missing():
    """get_fact_by_id should return None for missing fact."""
    mock_admin = MagicMock()
    mock_admin.table().select().eq().execute.return_value = MagicMock(
        data=[]
    )

    with patch("src.db.facts.get_supabase_admin", return_value=mock_admin):
        result = get_fact_by_id("missing")

    assert result is None
