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
