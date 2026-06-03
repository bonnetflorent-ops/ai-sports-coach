"""Feedback CRUD — Supabase."""
from src.db import get_supabase_admin


def save_feedback(user_id: str, message_id: str, feedback_type: str, detail: str = None) -> dict:
    admin = get_supabase_admin()
    result = admin.table("feedback").insert({
        "user_id": user_id,
        "message_id": message_id,
        "type": feedback_type,
        "detail": detail,
    }).execute()
    return result.data[0]


def get_feedback_by_user(user_id: str, limit: int = 50) -> list[dict]:
    admin = get_supabase_admin()
    result = (
        admin.table("feedback")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data


def get_all_feedback(page: int = 1, limit: int = 50, feedback_type: str = None) -> dict:
    """Admin: list all feedback, paginated and filterable by type."""
    admin = get_supabase_admin()
    query = admin.table("feedback").select("*", count="exact")
    if feedback_type:
        query = query.eq("type", feedback_type)
    result = (
        query
        .order("created_at", desc=True)
        .range((page - 1) * limit, page * limit - 1)
        .execute()
    )
    return {
        "feedback": result.data,
        "total": result.count or 0,
        "page": page,
        "limit": limit,
    }
