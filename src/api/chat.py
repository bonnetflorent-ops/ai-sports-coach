# -*- coding: utf-8 -*-
"""
Chat API — envoi de message (SSE streaming), historique, sessions.
"""
import asyncio
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
    count_session_messages,
)
from src.utils.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


def _schedule_fact_extraction(session_id: str, user_id: str):
    """Lance l'extraction de faits en arrière-plan (fire-and-forget).

    Appelée tous les 5 messages dans une session.
    Extrait 2-6 faits structurés via le LLM, puis les stocke avec
    déduplication par similarité cosinus (pgvector).
    """
    async def _extract_and_store():
        try:
            from src.engine.fact_extractor import extract_facts_from_messages
            from src.engine.embeddings import embed_text
            from src.db.facts import add_fact, deduplicate_facts, bump_importance

            recent_msgs = await asyncio.to_thread(
                get_session_messages, session_id, limit=20
            )
            if not recent_msgs:
                return

            facts = await asyncio.to_thread(
                extract_facts_from_messages, recent_msgs
            )
            if not facts:
                return

            for fact_data in facts:
                try:
                    embedding = await asyncio.to_thread(
                        embed_text, fact_data["fact"]
                    )
                    if all(v == 0.0 for v in embedding):
                        continue

                    is_dup, existing = await asyncio.to_thread(
                        deduplicate_facts, user_id, fact_data["fact"]
                    )

                    if is_dup and existing:
                        await asyncio.to_thread(
                            bump_importance, existing["id"]
                        )
                    else:
                        await asyncio.to_thread(
                            add_fact,
                            user_id,
                            fact_data["fact"],
                            fact_data["category"],
                            fact_data["importance"],
                            session_id,
                            embedding,
                        )
                except Exception:
                    pass

            logger.info(
                "facts_extracted_pwa: user=%s session=%s count=%s",
                user_id, session_id, len(facts),
            )
        except Exception as e:
            logger.error("fact_extraction_pwa_failed: %s", e)

    asyncio.create_task(_extract_and_store())


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

    # Résumé de la veille
    try:
        yesterday_summary = await maybe_summarize_yesterday(user_id, user)
    except Exception as e:
        logger.warning("Erreur summarizer: %s", e)
        yesterday_summary = None

    # Mettre à jour le modèle athlète avec le résumé quotidien (Niveau 2→5)
    if yesterday_summary:
        try:
            from src.db.athlete_models import get_latest_model, save_model_version
            from src.engine.athlete_model import update_model_from_summary

            current_model = await asyncio.to_thread(get_latest_model, user_id)
            if current_model:
                model_json = current_model.get("model_json") or current_model
                updated_model = await update_model_from_summary(
                    model_json, yesterday_summary
                )
                new_version = (current_model.get("version") or 1) + 1
                await asyncio.to_thread(
                    save_model_version, user_id, updated_model, new_version
                )
                logger.info(
                    "athlete_model_updated: user=%s version=%s",
                    user_id, new_version,
                )
        except Exception as e:
            logger.warning("Erreur mise à jour modèle athlète: %s", e)

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

    # Injecter les faits pertinents par recherche sémantique (Niveau 3 — pgvector)
    facts_context = ""
    try:
        from src.engine.embeddings import embed_text
        from src.db.facts import get_relevant_facts

        msg_embedding = await asyncio.to_thread(embed_text, request.message)
        if any(v != 0.0 for v in msg_embedding):
            relevant = await asyncio.to_thread(
                get_relevant_facts, user_id, msg_embedding, limit=5
            )
            if relevant:
                facts_lines = [
                    f"- {f['fact']}  [{f.get('category', '')}]"
                    for f in relevant
                ]
                facts_context = (
                    "FAITS CONNUS SUR L'ATHLÈTE :\n" + "\n".join(facts_lines)
                )
    except Exception as e:
        logger.warning("Erreur récupération faits pertinents: %s", e)

    # Construction du prompt système
    coaching_parts = []
    if yesterday_summary:
        coaching_parts.append(
            f"Résumé de la session précédente : {yesterday_summary}"
        )
    if facts_context:
        coaching_parts.append(facts_context)
    coaching_context = "\n\n".join(coaching_parts) if coaching_parts else None

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

            # Extraction de faits en arrière-plan (tous les 5 messages)
            try:
                msg_count = count_session_messages(session_id)
                if msg_count > 0 and msg_count % 5 == 0:
                    _schedule_fact_extraction(session_id, user_id)
            except Exception as e:
                logger.warning("Erreur comptage messages pour extraction faits: %s", e)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )
