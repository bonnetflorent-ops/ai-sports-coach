"""
Proactive coach — evaluates triggers for each user and generates notifications.
Called by system cron 2x/day (8h, 18h UTC).
"""
import logging
from datetime import date, datetime, timezone, timedelta
from typing import Optional
from src.db import get_supabase_admin
from src.db.users import get_all_active_users

logger = logging.getLogger(__name__)

TRIGGER_INACTIVITY_DAYS = 3
TRIGGER_TSB_THRESHOLD = -20
TRIGGER_TSB_DAYS = 5
TRIGGER_GOAL_WEEKS = 12


async def evaluate_all_users() -> list[dict]:
    """
    Scans all active users, evaluates triggers, returns list of
    {user_id, trigger_type, title, body, url} for push notifications.
    """
    users = get_all_active_users()
    notifications = []
    today = date.today()

    for user in users:
        user_id = user["id"]

        # 1. Inactivity check: 3+ days without message
        if _check_inactivity(user_id, today):
            notifications.append({
                "user_id": user_id,
                "trigger_type": "inactivity",
                "title": "Tout va bien ?",
                "body": "Pas de nouvelle depuis quelques jours. Ta prochaine sortie est prévue quand ?",
                "url": "/",
            })

        # 2. TSB check: TSB < -20
        tsb_alert = _check_tsb_danger(user_id)
        if tsb_alert:
            notifications.append(tsb_alert)

        # 3. Goal deadline approaching (12 weeks)
        goal_alert = _check_goal_deadline(user_id, today)
        if goal_alert:
            notifications.append(goal_alert)

        # 4. Injury follow-up
        injury_alert = _check_injury_followup(user_id, today)
        if injury_alert:
            notifications.append(injury_alert)

        # 5. Sunday 18h: weekly recap push
        if today.weekday() == 6:
            recap = await _build_weekly_recap(user_id)
            if recap:
                notifications.append(recap)

    return notifications


def _check_inactivity(user_id: str, today: date) -> bool:
    admin = get_supabase_admin()
    result = (
        admin.table("chat_messages")
        .select("created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if not result.data:
        return False
    last_msg = datetime.fromisoformat(result.data[0]["created_at"].replace("Z", "+00:00"))
    days_since = (today - last_msg.date()).days
    return days_since >= TRIGGER_INACTIVITY_DAYS


def _check_tsb_danger(user_id: str) -> Optional[dict]:
    """Checks if TSB has been below -20 for 5+ consecutive days."""
    from src.db.athlete_models import get_latest_model
    model_record = get_latest_model(user_id)
    if not model_record:
        return None
    model = model_record["model_json"]
    tsb = model.get("etat_actuel", {}).get("tsb", 0)
    if tsb < TRIGGER_TSB_THRESHOLD:
        return {
            "user_id": user_id,
            "trigger_type": "tsb_danger",
            "title": "⚠️ Charge d'entraînement élevée",
            "body": f"Ton TSB est à {tsb}. Pense à alléger cette semaine pour éviter le surentraînement.",
            "url": "/dashboard",
        }
    return None


def _check_goal_deadline(user_id: str, today: date) -> Optional[dict]:
    """Checks if a goal deadline is within 12 weeks."""
    from src.db.athlete_models import get_latest_model
    model_record = get_latest_model(user_id)
    if not model_record:
        return None
    model = model_record["model_json"]
    goal = model.get("objectifs", {}).get("actuel")
    if not goal:
        return None
    target_date_str = goal.get("date_cible")
    if not target_date_str:
        return None
    try:
        target_date = date.fromisoformat(target_date_str)
        weeks_until = (target_date - today).days / 7
        if 0 < weeks_until <= TRIGGER_GOAL_WEEKS:
            return {
                "user_id": user_id,
                "trigger_type": "goal_approaching",
                "title": f"🎯 {goal.get('nom', 'Objectif')} dans {int(weeks_until)} semaines",
                "body": "On entre en phase spécifique. Prêt à passer au niveau supérieur ?",
                "url": "/dashboard",
            }
    except (ValueError, TypeError):
        pass
    return None


def _check_injury_followup(user_id: str, today: date) -> Optional[dict]:
    """Checks for injuries marked 'à surveiller'."""
    from src.db.athlete_models import get_latest_model
    model_record = get_latest_model(user_id)
    if not model_record:
        return None
    model = model_record["model_json"]
    for injury in model.get("blessures", []):
        if injury.get("statut") == "à surveiller":
            body_part = injury.get("body_part", injury.get("type", "blessure"))
            return {
                "user_id": user_id,
                "trigger_type": "injury_followup",
                "title": "🩺 Suivi santé",
                "body": f"Comment se comporte ton {body_part} ? On en avait parlé récemment.",
                "url": "/",
            }
    return None


async def _build_weekly_recap(user_id: str) -> Optional[dict]:
    """Builds the Sunday weekly recap push notification."""
    from src.engine.weekly_rollup import maybe_generate_last_week_rollup
    from src.db.weekly_rollups import get_latest_rollup

    rollup = await maybe_generate_last_week_rollup(user_id)
    if not rollup:
        rollup_record = get_latest_rollup(user_id)
        if rollup_record:
            rollup = rollup_record["rollup_json"]
        else:
            return None

    nb_sessions = rollup.get("nb_sessions", 0)
    volume = rollup.get("total_volume_h", 0)
    tsb = rollup.get("avg_tsb", 0)
    summary = rollup.get("summary", "")

    return {
        "user_id": user_id,
        "trigger_type": "weekly_recap",
        "title": "🏁 Ta semaine sportive",
        "body": f"{nb_sessions} séances · {volume}h · TSB {tsb}\n{summary[:100]}",
        "url": "/dashboard",
    }


async def send_push_notifications(notifications: list[dict]):
    """
    Sends Web Push notifications to users via stored subscriptions.
    Uses pywebpush with VAPID keys for end-to-end encryption.
    """
    import json as _json
    from src.db.push_subscriptions import get_subscription
    from src.utils.config import settings

    try:
        from pywebpush import WebPush, WebPushException
    except ImportError:
        logger.error("pywebpush not installed — cannot send push notifications")
        return

    for notif in notifications:
        user_id = notif["user_id"]
        sub = get_subscription(user_id)
        if not sub:
            logger.debug(f"No push subscription for user={user_id}, skipping")
            continue

        try:
            wp = WebPush(
                subscription_info={
                    "endpoint": sub["endpoint"],
                    "keys": {"p256dh": sub["p256dh"], "auth": sub["auth"]},
                },
                data=_json.dumps({
                    "title": notif["title"],
                    "body": notif["body"],
                    "url": notif.get("url", "/"),
                }),
                vapid_private_key=settings.vapid_private_key,
                vapid_claims={"sub": f"mailto:{settings.vapid_subject}"},
            )
            wp.send()
            logger.info(f"Push sent: user={user_id}, trigger={notif['trigger_type']}")

        except Exception as e:
            logger.warning(f"Push failed for user={user_id}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                if getattr(e.response, 'status_code', None) == 410:
                    from src.db.push_subscriptions import remove_subscription
                    remove_subscription(user_id)
                    logger.info(f"Removed expired subscription for user={user_id}")
