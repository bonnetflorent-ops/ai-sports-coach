# -*- coding: utf-8 -*-
"""
Resume quotidien structure — produit un JSON a partir des messages bruts.
"""
import json
import logging
from datetime import date

from src.engine.llm import chat
from src.db.daily_summaries import save_daily_summary, get_daily_summary
from src.db.sessions import get_session_messages

logger = logging.getLogger(__name__)

REQUIRED_FIELDS = [
    "date", "nb_messages", "narrative", "metrics_extracted",
    "injuries_reported", "decisions", "follow_ups", "emotional_tone",
    "training_done_today",
]
METRIC_REQUIRED_FIELDS = ["name", "value", "unit", "source", "confidence"]
VALID_CONFIDENCES = {"measured", "reported", "estimated", "auto_extracted"}

SUMMARY_PROMPT = """Tu es un assistant qui resume une journee de coaching sportif en JSON structure.
REGLES:
- Extrais UNIQUEMENT ce qui est explicitement mentionne
- N'invente JAMAIS de metriques, de blessures ou de decisions
- Si aucun fait d'une categorie, mets un tableau vide []
- Formule les faits de maniere concise (max 100 caracteres par entree)
- emotional_tone: "motive", "fatigue", "inquiet", "content", "neutre", "decu mais determine"
Retourne UNIQUEMENT un objet JSON valide avec ce format:
{
  "date": "YYYY-MM-DD", "nb_messages": N,
  "narrative": "2-3 phrases", "metrics_extracted": [...], "injuries_reported": [...],
  "decisions": [...], "follow_ups": [...], "emotional_tone": "...", "training_done_today": "..."
}"""


def validate_summary_json(summary: dict) -> bool:
    """Validate the structure of a parsed summary JSON."""
    if not isinstance(summary, dict):
        return False
    for field in REQUIRED_FIELDS:
        if field not in summary:
            logger.warning("Missing required field: %s", field)
            return False
    for metric in summary.get("metrics_extracted", []):
        for field in METRIC_REQUIRED_FIELDS:
            if field not in metric:
                logger.warning("Metric missing field: %s", field)
                return False
        if metric.get("confidence") not in VALID_CONFIDENCES:
            return False
    return True


async def summarize_day(user_id: str, session_id: str, day: date) -> dict | None:
    """Summarize a day's conversation into a structured JSON summary."""
    messages = get_session_messages(session_id, limit=50)
    if not messages:
        logger.info("No messages found for session=%s, day=%s", session_id, day)
        return None

    conversation = "\n".join(f"[{m['role']}] {m['content']}" for m in messages)
    system_prompt = SUMMARY_PROMPT
    user_prompt = (
        f"Date: {day.isoformat()}\n"
        f"Nombre de messages: {len(messages)}\n\n"
        f"Conversation:\n{conversation[:6000]}\n\n"
        f"Produis le resume JSON structure:"
    )

    try:
        raw = await chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=800,
        )
        summary = json.loads(raw)
        if not validate_summary_json(summary):
            logger.error("Summary validation failed for user=%s", user_id)
            return None

        summary["nb_messages"] = len(messages)
        summary["date"] = day.isoformat()
        save_daily_summary(
            user_id=user_id,
            day=day,
            summary_json=summary,
            nb_messages=len(messages),
        )
        logger.info(
            "Daily summary saved: user=%s, date=%s, messages=%d",
            user_id, day, len(messages),
        )
        return summary

    except (json.JSONDecodeError, Exception) as e:
        logger.error("Summarization failed for user=%s: %s", user_id, e)
        return None


async def maybe_summarize_yesterday(user_id: str, user: dict) -> dict | None:
    """Check if yesterday needs summarizing and do so if needed.

    Returns the summary dict if one was generated, or None if
    already summarized or no data available.
    """
    today = date.today()
    existing = get_daily_summary(user_id, today)
    if existing:
        return None

    from src.db.sessions import get_or_create_active_session_for_user

    session = get_or_create_active_session_for_user(user_id)
    if not session:
        return None

    return await summarize_day(user_id, session["id"], today)
