"""
Weekly rollup engine — condenses 7 daily summaries into 1 weekly synthesis.
Triggered on Sundays, or on demand for the previous week.
"""
import json
import logging
from datetime import date, timedelta, datetime, timezone
from typing import Optional

from src.engine.llm import chat
from src.db.daily_summaries import get_summaries_for_range
from src.db.weekly_rollups import save_weekly_rollup, get_weekly_rollup

logger = logging.getLogger(__name__)

ROLLUP_REQUIRED_FIELDS = [
    "week", "start_date", "end_date", "nb_sessions", "total_volume_h",
    "summary", "avg_rpe", "avg_ctl", "avg_tsb", "key_metrics",
    "injuries_active", "injuries_resolved", "goals_progress", "coach_notes",
]

METRIC_REQUIRED_FIELDS = ["name", "value", "unit", "trend"]


def get_week_label(day: date) -> str:
    """Returns ISO week label, e.g. '2026-W23'."""
    iso = day.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def validate_rollup_json(rollup: dict) -> bool:
    """Validates that a rollup has all required fields."""
    if not isinstance(rollup, dict):
        return False
    for field in ROLLUP_REQUIRED_FIELDS:
        if field not in rollup:
            logger.warning(f"Rollup missing field: {field}")
            return False
    for metric in rollup.get("key_metrics", []):
        for field in METRIC_REQUIRED_FIELDS:
            if field not in metric:
                logger.warning(f"Rollup metric missing field: {field}")
                return False
    return True


def build_rollup_prompt(summaries: list[dict], week_label: str, start: date, end: date) -> str:
    """Builds the LLM prompt for weekly rollup."""
    summary_text = "\n\n---\n\n".join(
        f"Jour {s['date']}:\nNarrative: {s.get('narrative', '')}\n"
        f"Métriques: {json.dumps(s.get('metrics_extracted', []), ensure_ascii=False)}\n"
        f"Blessures: {json.dumps(s.get('injuries_reported', []), ensure_ascii=False)}\n"
        f"Décisions: {json.dumps(s.get('decisions', []), ensure_ascii=False)}\n"
        f"Suivis: {json.dumps(s.get('follow_ups', []), ensure_ascii=False)}\n"
        f"Ton: {s.get('emotional_tone', 'neutre')}"
        for s in summaries
    )

    return f"""Semaine {week_label} ({start.isoformat()} au {end.isoformat()}).
Nombre de jours avec activité: {len(summaries)}.

Résumés quotidiens:
{summary_text}

Produis une synthèse JSON de cette semaine (format vu ci-dessus). Sois concis et factuel."""


async def generate_weekly_rollup(
    user_id: str,
    week_start: date,
    week_end: date,
) -> Optional[dict]:
    """
    Generates a weekly rollup from daily summaries.
    Returns the rollup JSON or None on failure.
    """
    summaries = get_summaries_for_range(user_id, week_start, week_end)
    if not summaries:
        logger.info(f"No summaries for user={user_id}, week={week_start}")
        return None

    week_label = get_week_label(week_start)

    system_prompt = f"""Tu es un assistant qui synthétise une semaine de coaching sportif en JSON structuré.

RÈGLES :
- Synthétise UNIQUEMENT à partir des résumés quotidiens fournis
- N'invente RIEN
- Calcule les totaux (nb_sessions, volume_h) à partir des résumés
- avg_rpe, avg_ctl, avg_tsb : moyenne des valeurs présentes (ignore les absentes)
- trends pour métriques clés : "up", "down", ou "stable"
- coach_notes : 2-3 phrases de synthèse pour le coach

Retourne UNIQUEMENT un objet JSON (pas de markdown, pas de texte) :
{{
  "week": "{week_label}",
  "start_date": "{week_start.isoformat()}",
  "end_date": "{week_end.isoformat()}",
  "nb_sessions": N,
  "total_volume_h": X.X,
  "summary": "2-3 phrases résumant la semaine",
  "avg_rpe": X.X,
  "avg_ctl": XX,
  "avg_tsb": XX,
  "key_metrics": [
    {{"name": "...", "value": N, "unit": "...", "trend": "up|down|stable"}}
  ],
  "injuries_active": [{{"body_part": "...", "status": "...", "since": "YYYY-MM-DD"}}],
  "injuries_resolved": [{{"body_part": "...", "resolved_date": "YYYY-MM-DD"}}],
  "goals_progress": "1 phrase sur la progression vers l'objectif",
  "coach_notes": "2-3 phrases de notes pour le coach"
}}"""

    try:
        raw = await chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": build_rollup_prompt(summaries, week_label, week_start, week_end)},
            ],
            temperature=0.3,
            max_tokens=600,
        )

        rollup = json.loads(raw)

        if not validate_rollup_json(rollup):
            logger.error(f"Invalid rollup JSON for user={user_id}, week={week_label}")
            return None

        save_weekly_rollup(user_id, week_label, rollup)

        logger.info(f"Weekly rollup saved: user={user_id}, week={week_label}")
        return rollup

    except json.JSONDecodeError as e:
        logger.error(f"LLM returned invalid JSON for rollup: {e}")
        return None
    except Exception as e:
        logger.error(f"Rollup generation failed: {e}")
        return None


async def maybe_generate_last_week_rollup(user_id: str) -> Optional[dict]:
    """
    Checks if a rollup is needed for the previous week (Sunday trigger).
    Called by proactive cron or on first message of a new week.
    """
    today = date.today()
    days_since_monday = today.weekday()
    last_monday = today - timedelta(days=days_since_monday + 7)
    last_sunday = last_monday + timedelta(days=6)

    week_label = get_week_label(last_monday)

    existing = get_weekly_rollup(user_id, week_label)
    if existing:
        return None

    return await generate_weekly_rollup(user_id, last_monday, last_sunday)
