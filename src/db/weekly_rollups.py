"""Weekly rollups CRUD — Supabase."""
from src.db import get_supabase_admin


def save_weekly_rollup(user_id: str, week: str, rollup_json: dict) -> dict:
    admin = get_supabase_admin()
    result = admin.table("weekly_rollups").upsert({
        "user_id": user_id,
        "week": week,
        "rollup_json": rollup_json,
    }, on_conflict="user_id,week").execute()
    return result.data[0]


def get_weekly_rollup(user_id: str, week: str) -> dict | None:
    admin = get_supabase_admin()
    result = (
        admin.table("weekly_rollups")
        .select("*")
        .eq("user_id", user_id)
        .eq("week", week)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def get_latest_rollup(user_id: str) -> dict | None:
    admin = get_supabase_admin()
    result = (
        admin.table("weekly_rollups")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None
