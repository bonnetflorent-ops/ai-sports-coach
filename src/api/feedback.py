# -*- coding: utf-8 -*-
"""
Feedback API — collecte des likes/dislikes, consultation admin.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.dependencies import get_current_user
from src.db.feedback import save_feedback, get_all_feedback

logger = logging.getLogger(__name__)

router = APIRouter(tags=["feedback"])


# ── Modèles ─────────────────────────────────────────────────────────


class FeedbackCreate:
    """Modèle pour la création d'un feedback."""
    def __init__(
        self,
        message_id: str,
        type: str,
        detail: Optional[str] = None,
    ):
        valid_types = {"like", "dislike", "bug"}
        if type not in valid_types:
            raise ValueError(f"Le type doit être l'un de: {', '.join(sorted(valid_types))}")
        self.message_id = message_id
        self.type = type
        self.detail = detail


# ── Endpoints ───────────────────────────────────────────────────────


@router.post("/api/chat/feedback")
async def create_feedback(
    body: dict,
    user: dict = Depends(get_current_user),
):
    """Enregistre un like/dislike/bug sur un message du chat."""
    feedback_type = body.get("type")
    message_id = body.get("message_id")
    detail = body.get("detail")

    valid_types = {"like", "dislike", "bug"}
    if feedback_type not in valid_types:
        raise HTTPException(
            status_code=422,
            detail=f"Le type doit être l'un de: {', '.join(sorted(valid_types))}",
        )
    if not message_id:
        raise HTTPException(status_code=422, detail="message_id est requis")

    saved = save_feedback(
        user_id=user["id"],
        message_id=message_id,
        feedback_type=feedback_type,
        detail=detail,
    )
    return {"status": "ok", "feedback": saved}


@router.get("/api/admin/feedback")
async def list_feedback(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    type: Optional[str] = Query(None, alias="type"),
    user: dict = Depends(get_current_user),
):
    """Liste tous les feedbacks (MVP: accessible à tout utilisateur authentifié)."""
    result = get_all_feedback(page=page, limit=limit, feedback_type=type)
    return result
