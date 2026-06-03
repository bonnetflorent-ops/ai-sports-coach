"""Daily summaries CRUD — Supabase."""
from datetime import date
from src.db import get_supabase_admin


def save_daily_summary(user_id: str, day: date, summary_json: dict, nb_messages: int) -> dict:
    admin = get_supabase_admin()
    result = admin.table("daily_summaries").upsert({
        "user_id": user_id,
        "date": day.isoformat(),
        "summary_json": summary_json,
        "nb_messages": nb_messages,
    }, on_conflict="user_id,date").execute()
    return result.data[0]


def get_daily_summary(user_id: str, day: date) -> dict | None:
    admin = get_supabase_admin()
    result = (
        admin.table("daily_summaries")
        .select("*")
        .eq("user_id", user_id)
        .eq("date", day.isoformat())
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def get_summaries_for_range(user_id: str, start: date, end: date) -> list[dict]:
    admin = get_supabase_admin()
    result = (
        admin.table("daily_summaries")
        .select("*")
        .eq("user_id", user_id)
        .gte("date", start.isoformat())
        .lte("date", end.isoformat())
        .order("date")
        .execute()
    )
    return result.data


def get_recent_summaries(user_id: str, days: int = 7) -> list[dict]:
    from datetime import timedelta
    start = date.today() - timedelta(days=days)
    return get_summaries_for_range(user_id, start, date.today())
