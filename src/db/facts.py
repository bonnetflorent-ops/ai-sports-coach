# -*- coding: utf-8 -*-
"""
Repository for persistent user facts with pgvector similarity search.
"""

import logging
from datetime import datetime
from typing import Optional

from src.db import get_supabase_admin

logger = logging.getLogger(__name__)


def add_fact(
    user_id: str,
    fact: str,
    category: str,
    importance: float = 0.5,
    source_session_id: Optional[str] = None,
    embedding: Optional[list[float]] = None,
) -> dict:
    """Insert a new fact. Returns the created fact dict."""
    admin = get_supabase_admin()

    data = {
        "user_id": user_id,
        "fact": fact,
        "category": category,
        "importance": importance,
        "source_session_id": source_session_id,
        "embedding": embedding or [],
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }

    result = admin.table("user_facts").insert(data).execute()
    return result.data[0] if result.data else {}


def get_facts_by_user(user_id: str, limit: int = 50) -> list[dict]:
    """Get all facts for a user, ordered by importance DESC."""
    admin = get_supabase_admin()

    result = (
        admin.table("user_facts")
        .select("id, fact, category, importance, source_session_id, created_at")
        .eq("user_id", user_id)
        .order("importance", desc=True)
        .limit(limit)
        .execute()
    )

    return result.data


def get_relevant_facts(
    user_id: str, query_embedding: list[float], limit: int = 5
) -> list[dict]:
    """
    Get top-N facts by cosine similarity using pgvector <=> operator.
    Returns facts with their similarity distance.
    """
    admin = get_supabase_admin()

    # pgvector <=> operator for cosine distance
    # Lower distance = more similar
    result = (
        admin.rpc(
            "match_user_facts",
            {
                "query_embedding": query_embedding,
                "match_user_id": user_id,
                "match_limit": limit,
            },
        )
        .execute()
    )

    return result.data


def deduplicate_facts(
    user_id: str, new_fact: str, threshold: float = 0.85
) -> tuple[bool, Optional[dict]]:
    """
    Check if a similar fact already exists.
    Returns (is_duplicate: bool, existing_fact: dict or None).
    Uses pgvector similarity search.
    """
    from src.engine.embeddings import embed_text

    query_emb = embed_text(new_fact)

    # Check if all zeros (embedding failed)
    if all(v == 0.0 for v in query_emb):
        return False, None

    existing = get_relevant_facts(user_id, query_emb, limit=3)

    for fact in existing:
        # pgvector <=> returns cosine distance (0 = identical, 2 = opposite)
        # similarity = 1 - distance
        similarity = 1.0 - float(fact.get("distance", 1.0))
        if similarity >= threshold:
            return True, fact

    return False, None


def update_fact(fact_id: str, updates: dict) -> dict:
    """Update an existing fact. Returns updated fact dict."""
    admin = get_supabase_admin()

    updates["updated_at"] = datetime.utcnow().isoformat()
    result = (
        admin.table("user_facts")
        .update(updates)
        .eq("id", fact_id)
        .execute()
    )

    return result.data[0] if result.data else {}


def bump_importance(fact_id: str, increment: float = 0.1) -> dict:
    """Increase a fact's importance (cap at 1.0)."""
    existing = get_fact_by_id(fact_id)
    if not existing:
        return {}

    new_importance = min(1.0, float(existing.get("importance", 0.5)) + increment)
    return update_fact(fact_id, {"importance": new_importance})


def get_fact_by_id(fact_id: str) -> Optional[dict]:
    """Get a single fact by ID."""
    admin = get_supabase_admin()

    result = (
        admin.table("user_facts")
        .select("*")
        .eq("id", fact_id)
        .execute()
    )

    return result.data[0] if result.data else None
