"""Push subscription CRUD — Supabase."""
from src.db import get_supabase_admin


def save_subscription(user_id: str, subscription: dict) -> dict:
    admin = get_supabase_admin()
    result = admin.table("push_subscriptions").upsert({
        "user_id": user_id,
        "endpoint": subscription["endpoint"],
        "p256dh": subscription["keys"]["p256dh"],
        "auth": subscription["keys"]["auth"],
    }, on_conflict="user_id").execute()
    return result.data[0]


def get_subscription(user_id: str) -> dict | None:
    admin = get_supabase_admin()
    result = (
        admin.table("push_subscriptions")
        .select("*")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def remove_subscription(user_id: str) -> None:
    admin = get_supabase_admin()
    admin.table("push_subscriptions").delete().eq("user_id", user_id).execute()
