# -*- coding: utf-8 -*-
"""
Repository sessions + messages — Supabase.

Les sessions groupent les messages d'une conversation.
Les messages sont sauvegardés avec métadonnées (tokens, coût, concepts).
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from src.db import get_supabase_admin

logger = logging.getLogger(__name__)


def create_session(telegram_id: int, topic: Optional[str] = None) -> dict:
    """
    Crée une nouvelle session de chat pour un utilisateur.
    Retourne la session créée.
    """
    admin = get_supabase_admin()

    # Trouver le user_id
    user_result = (
        admin.table("users")
        .select("id")
        .eq("telegram_id", telegram_id)
        .execute()
    )
    if not user_result.data:
        raise ValueError(f"Utilisateur telegram_id={telegram_id} introuvable")

    user_id = user_result.data[0]["id"]

    session_data = {
        "user_id": user_id,
        "topic": topic,
    }

    result = admin.table("chat_sessions").insert(session_data).execute()
    session = result.data[0]
    logger.debug(f"Session créée: {session['id']} pour user={telegram_id}")
    return session


def save_message(
    session_id: str,
    role: str,
    content: str,
    tokens_in: int = 0,
    tokens_out: int = 0,
    cost_eur: float = 0.0,
    concepts_used: Optional[list[str]] = None,
    level_used: Optional[int] = None,
) -> dict:
    """
    Sauvegarde un message dans une session.
    Met à jour le compteur de messages de la session.
    """
    admin = get_supabase_admin()

    msg_data = {
        "session_id": session_id,
        "role": role,
        "content": content,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "cost_eur": cost_eur,
        "concepts_used": concepts_used or [],
        "level_used": level_used,
    }

    result = admin.table("chat_messages").insert(msg_data).execute()
    message = result.data[0]

    # Incrémenter le compteur de messages de la session
    admin.rpc(
        "increment_session_count",
        {"session_id_param": session_id},
    ).execute()

    # Alternative: update direct
    # Mais on utilise la fonction SQL ci-dessus car plus atomique
    return message


def get_recent_context(session_id: str, limit: int = 6) -> list[str]:
    """
    Récupère les derniers messages d'une session pour le contexte du sélecteur.
    Retourne une liste de strings (contenus des messages).
    """
    admin = get_supabase_admin()

    result = (
        admin.table("chat_messages")
        .select("role, content")
        .eq("session_id", session_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )

    # Inverser pour avoir l'ordre chronologique
    messages = list(reversed(result.data))
    return [f"[{m['role']}] {m['content'][:200]}" for m in messages]


def get_or_create_active_session(telegram_id: int) -> dict:
    """
    Récupère la session active la plus récente, ou en crée une nouvelle.
    Une session est "active" si elle a moins de 24h et pas encore terminée.
    """
    admin = get_supabase_admin()

    # Trouver le user_id
    user_result = (
        admin.table("users")
        .select("id")
        .eq("telegram_id", telegram_id)
        .execute()
    )
    if not user_result.data:
        raise ValueError(f"Utilisateur telegram_id={telegram_id} introuvable")

    user_id = user_result.data[0]["id"]

    # Chercher une session active récente
    result = (
        admin.table("chat_sessions")
        .select("*")
        .eq("user_id", user_id)
        .is_("ended_at", "null")
        .order("started_at", desc=True)
        .limit(1)
        .execute()
    )

    if result.data:
        session = result.data[0]
        # Vérifier si la session a moins de 24h
        started = datetime.fromisoformat(session["started_at"].replace("+00:00", ""))
        age = datetime.now(timezone.utc) - started.replace(tzinfo=timezone.utc)
        if age.total_seconds() < 86400:  # 24h
            return session

    # Créer une nouvelle session
    return create_session(telegram_id)


def get_session_messages(session_id: str, limit: int = 10) -> list[dict]:
    """
    Returns the last N messages of a session, WITH FULL CONTENT (no truncation).
    Ordered chronologically (oldest first).
    Each dict: {role, content, created_at}

    Unlike get_recent_context(), this returns complete messages
    for injection into the coach prompt.
    """
    admin = get_supabase_admin()

    result = (
        admin.table("chat_messages")
        .select("role, content, created_at")
        .eq("session_id", session_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )

    # Reverse to chronological order
    return list(reversed(result.data))


def summarize_session(session_id: str) -> str:
    """
    Generate a 300-500 char session summary using deepseek-chat.
    Saves summary to chat_sessions.session_summary column.
    Returns the summary string.
    """
    import json
    from openai import OpenAI
    from src.utils.config import settings

    admin = get_supabase_admin()

    # Get session messages (last 30, for summarization we want more context)
    messages = get_session_messages(session_id, limit=30)
    if not messages:
        return ""

    # Build conversation text
    conversation = "\n".join(
        [f"[{m['role']}] {m['content'][:300]}" for m in messages[-20:]]
    )

    # Summarize with deepseek-chat
    try:
        client = OpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            timeout=30.0,
        )
        response = client.chat.completions.create(
            model="deepseek/deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Tu es un assistant qui résume des sessions de coaching sportif. "
                        "Résume en 3-5 phrases en français (300-500 caractères max) : "
                        "ce dont l'athlète a parlé, les décisions prises, les faits mentionnés, "
                        "les suivis à faire. Sois concis et factuel. Format : texte simple, pas de markdown."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Résume cette session de coaching :\n\n{conversation}",
                },
            ],
            max_tokens=200,
            temperature=0.3,
        )

        summary = response.choices[0].message.content.strip()[:600]

        # Save to DB
        admin.table("chat_sessions").update(
            {"session_summary": summary}
        ).eq("id", session_id).execute()

        logger.info(f"Session summarized: {session_id[:8]}... ({len(summary)} chars)")
        return summary

    except Exception as e:
        logger.warning(f"Session summarization failed for {session_id[:8]}...: {e}")
        return ""


def get_recent_summaries(telegram_id: int, limit: int = 3) -> list[dict]:
    """
    Returns summaries of the last N completed sessions (excluding current).
    Each dict: {started_at, session_summary}
    """
    admin = get_supabase_admin()

    # Find user_id
    user_result = (
        admin.table("users")
        .select("id")
        .eq("telegram_id", telegram_id)
        .execute()
    )
    if not user_result.data:
        return []

    user_id = user_result.data[0]["id"]

    result = (
        admin.table("chat_sessions")
        .select("started_at, session_summary")
        .eq("user_id", user_id)
        .not_.is_("session_summary", "null")
        .order("started_at", desc=True)
        .limit(limit)
        .execute()
    )

    return result.data


def _get_active_session_id(telegram_id: int) -> dict | None:
    """
    Returns the ID of the current active session (if any, even if expired).
    Used to detect session expiry for auto-summarization.
    """
    admin = get_supabase_admin()

    user_result = (
        admin.table("users")
        .select("id")
        .eq("telegram_id", telegram_id)
        .execute()
    )
    if not user_result.data:
        return None

    user_id = user_result.data[0]["id"]

    result = (
        admin.table("chat_sessions")
        .select("id, message_count, session_summary")
        .eq("user_id", user_id)
        .is_("ended_at", "null")
        .order("started_at", desc=True)
        .limit(1)
        .execute()
    )

    if result.data:
        return result.data[0]
    return None


def end_session(session_id: str):
    """Marque une session comme terminée."""
    admin = get_supabase_admin()
    admin.table("chat_sessions").update({"ended_at": datetime.now(timezone.utc).isoformat()}).eq("id", session_id).execute()
    logger.debug(f"Session terminée: {session_id}")


def get_session_history(telegram_id: int, limit: int = 5) -> list[dict]:
    """
    Récupère l'historique des dernières sessions pour un utilisateur.
    """
    admin = get_supabase_admin()

    user_result = (
        admin.table("users")
        .select("id")
        .eq("telegram_id", telegram_id)
        .execute()
    )
    if not user_result.data:
        return []

    user_id = user_result.data[0]["id"]

    result = (
        admin.table("chat_sessions")
        .select("id, started_at, ended_at, topic, message_count")
        .eq("user_id", user_id)
        .order("started_at", desc=True)
        .limit(limit)
        .execute()
    )

    return result.data
