# -*- coding: utf-8 -*-
"""
Chat streaming helpers — SSE formatting and LLM stream handling.
"""
import json
import logging
from typing import AsyncGenerator, Optional

from src.engine.llm import get_client
from src.utils.config import settings

logger = logging.getLogger(__name__)


def format_sse_event(event_type: str, data: dict) -> str:
    """
    Formatte un événement SSE (Server-Sent Events).

    Args:
        event_type: Type d'événement (token, message_complete, error, ...)
        data: Dictionnaire de données à sérialiser en JSON.

    Returns:
        Chaîne SSE formatée, terminée par deux sauts de ligne.
    """
    return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def stream_llm_response(
    messages: list[dict],
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 1500,
) -> AsyncGenerator[str, None]:
    """
    Stream la réponse LLM depuis OpenRouter via SSE.

    Yields des événements SSE formatés :
    - event: token  → un token de texte
    - event: message_complete → la réponse complète (fin du stream)
    - event: error  → une erreur s'est produite

    Args:
        messages: Liste de messages au format OpenAI (role, content)
        model: Modèle LLM à utiliser (défaut: settings.llm_model)
        temperature: Température d'échantillonnage (0.0-1.0)
        max_tokens: Nombre maximum de tokens en sortie
    """
    client = get_client()
    actual_model = model or settings.llm_model

    full_content = ""

    try:
        stream = await client.chat.completions.create(
            model=actual_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                token = chunk.choices[0].delta.content
                full_content += token
                yield format_sse_event("token", {"token": token})

        yield format_sse_event(
            "message_complete",
            {"content": full_content},
        )

    except Exception as e:
        logger.error("Stream LLM error: %s", e, exc_info=True)
        yield format_sse_event(
            "error",
            {"detail": f"Erreur lors de la génération de la réponse: {str(e)}"},
        )
