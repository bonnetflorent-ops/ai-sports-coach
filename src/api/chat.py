# -*- coding: utf-8 -*-
"""
Chat API — envoi de message (SSE streaming), historique, sessions.
"""
import json
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.api.dependencies import get_current_user
from src.api.middleware.rate_limit import check_rate_limit
from src.engine.chat_stream import stream_llm_response, format_sse_event
from src.engine.summarizer import maybe_summarize_yesterday
from src.engine.selector import select_concepts
from src.engine.prompt_builder import build_system_prompt
from src.engine.llm import get_client
from src.engine.cost_tracker import track_cost
from src.db.sessions import (
    get_or_create_active_session_for_user,
    save_message,
    get_session_messages,
    get_user_messages_paginated,
    get_user_sessions,
)
from src.utils.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


# ── Modèles ─────────────────────────────────────────────────────────


class ChatMessageRequest(BaseModel):
    message: str


# ── Endpoints ───────────────────────────────────────────────────────


@router.get("/sessions")
async def list_sessions(
    user: dict = Depends(get_current_user),
):
    """Liste les sessions de chat de l'utilisateur."""
    sessions = get_user_sessions(user["id"])
    return {"sessions": sessions}


@router.get("/history")
async def chat_history(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    user: dict = Depends(get_current_user),
):
    """Retourne l'historique paginé des messages de l'utilisateur."""
    result = get_user_messages_paginated(user["id"], page=page, per_page=per_page)
    return result


@router.post("/message")
async def chat_message(
    request: ChatMessageRequest,
    user: dict = Depends(get_current_user),
):
    """Envoie un message et reçoit une réponse streamée via SSE.

    Le flux SSE contient les événements suivants :
    - event: token — un token de la réponse
    - event: message_complete — la réponse est terminée
    - event: error — une erreur s'est produite

    Retourne un Content-Type: text/event-stream.
    """
    user_id = user["id"]

    # Rate limiting
    if not check_rate_limit(user_id):
        raise HTTPException(
            status_code=429,
            detail="Trop de requêtes. Veuillez attendre avant d'envoyer un nouveau message.",
        )

    # Session management
    try:
        session = get_or_create_active_session_for_user(user_id)
    except Exception as e:
        logger.error("Erreur session user=%s: %s", user_id, e)
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la récupération de la session",
        )

    session_id = session["id"]

    # Sauvegarder le message utilisateur
    try:
        save_message(session_id, "user", request.message)
    except Exception as e:
        logger.error("Erreur sauvegarde message user: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la sauvegarde du message",
        )

    # Résumé de la veille (stub)
    try:
        yesterday_summary = await maybe_summarize_yesterday(user_id, user)
    except Exception as e:
        logger.warning("Erreur summarizer: %s", e)
        yesterday_summary = None

    # Hot memory : charger les 15 derniers messages
    try:
        recent_messages = get_session_messages(session_id, limit=15)
    except Exception as e:
        logger.error("Erreur chargement historique: %s", e)
        recent_messages = []

    # Sélection des concepts
    try:
        client = get_client()
        selection = await select_concepts(
            client,
            request.message,
            user_profile=user,
            recent_context=[m["content"][:200] for m in recent_messages[-3:]],
        )
    except Exception as e:
        logger.warning("Erreur sélection concepts: %s, fallback", e)
        selection = {
            "concepts": [],
            "level": user.get("level", 1),
            "reasoning": "Fallback suite à erreur sélecteur",
        }

    # Construction du prompt système
    coaching_context = None
    if yesterday_summary:
        coaching_context = f"Résumé de la session précédente : {yesterday_summary}"

    system_prompt = build_system_prompt(selection, user, coaching_context)

    # Messages pour le LLM
    llm_messages = [{"role": "system", "content": system_prompt}]
    for m in recent_messages:
        llm_messages.append({"role": m["role"], "content": m["content"]})
    llm_messages.append({"role": "user", "content": request.message})

    # Création du générateur SSE
    async def event_generator():
        """Génère les événements SSE."""
        full_content = ""

        try:
            async for sse_event in stream_llm_response(
                messages=llm_messages,
                model=settings.llm_model,
                temperature=0.7,
                max_tokens=1500,
            ):
                yield sse_event

                # Capturer le contenu pour sauvegarde
                if sse_event.startswith("event: token"):
                    try:
                        data_line = sse_event.split("data: ", 1)[1]
                        data = json.loads(data_line)
                        full_content += data.get("token", "")
                    except (IndexError, json.JSONDecodeError):
                        pass

        except Exception as e:
            logger.error("Erreur dans le stream chat: %s", e)
            yield format_sse_event("error", {"detail": "Erreur lors du streaming"})

        finally:
            # Sauvegarder la réponse de l'assistant
            if full_content:
                try:
                    # Estimation grossière des tokens (4 caractères ≈ 1 token)
                    tokens_out = len(full_content) // 4
                    tokens_in = sum(len(m.get("content", "")) for m in llm_messages) // 4

                    save_message(
                        session_id,
                        "assistant",
                        full_content,
                        tokens_in=tokens_in,
                        tokens_out=tokens_out,
                        concepts_used=selection.get("concepts", []),
                        level_used=selection.get("level"),
                    )
                    track_cost(
                        user.get("id"),
                        settings.llm_model,
                        tokens_in,
                        tokens_out,
                    )
                except Exception as e:
                    logger.error("Erreur sauvegarde réponse: %s", e)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )
