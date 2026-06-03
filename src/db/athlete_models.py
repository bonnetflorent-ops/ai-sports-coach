"""Athlete Model CRUD — Supabase."""
from src.db import get_supabase_admin


def get_latest_model(user_id: str) -> dict | None:
    admin = get_supabase_admin()
    result = (
        admin.table("athlete_models")
        .select("*")
        .eq("user_id", user_id)
        .order("version", desc=True)
        .limit(1)
        .execute()
    )
    if result.data:
        return result.data[0]
    return None


def save_model_version(user_id: str, model_json: dict, version: int) -> dict:
    admin = get_supabase_admin()
    result = admin.table("athlete_models").insert({
        "user_id": user_id,
        "model_json": model_json,
        "version": version,
    }).execute()
    return result.data[0]
