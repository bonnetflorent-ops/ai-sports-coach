# -*- coding: utf-8 -*-
"""
Embedding generation using Gemini Embedding 2 (768d).
Uses OpenRouter's OpenAI-compatible endpoint.
"""

import logging
from openai import OpenAI
from src.utils.config import settings

logger = logging.getLogger(__name__)

GEMINI_EMBEDDING_MODEL = "google/gemini-embedding-2"
EMBEDDING_DIM = 768

_client = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            timeout=15.0,
        )
    return _client


def embed_text(text: str) -> list[float]:
    """
    Generate a 768d embedding for a text using Gemini Embedding 2 via OpenRouter.

    Returns a list of 768 floats.
    """
    if not text or not text.strip():
        return [0.0] * EMBEDDING_DIM

    try:
        client = _get_client()
        response = client.embeddings.create(
            model=GEMINI_EMBEDDING_MODEL,
            input=text[:8000],  # Truncate to safe input length
        )
        embedding = response.data[0].embedding

        if len(embedding) != EMBEDDING_DIM:
            logger.warning(
                f"embedding_dimension_mismatch expected={EMBEDDING_DIM} actual={len(embedding)}"
            )
            # Pad or truncate
            if len(embedding) < EMBEDDING_DIM:
                embedding.extend([0.0] * (EMBEDDING_DIM - len(embedding)))
            else:
                embedding = embedding[:EMBEDDING_DIM]

        return embedding

    except Exception as e:
        logger.error(f"embedding_failed: {e}")
        return [0.0] * EMBEDDING_DIM  # Degrade gracefully


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for multiple texts. Returns list of embeddings."""
    return [embed_text(t) for t in texts]
