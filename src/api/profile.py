# -*- coding: utf-8 -*-
"""
Profile API — gestion et consultation du profil utilisateur.
"""
import logging

from fastapi import APIRouter, Depends

from src.api.dependencies import get_current_user
from src.db.users import update_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/profile", tags=["profile"])

# Mapping des noms de champs frontend vers les colonnes DB.
# Ex: le frontend envoie "sports" (pluriel), la colonne DB est "sport" (singulier).
# Ex: le frontend envoie "goals", la colonne DB est "goal".
FIELD_TO_DB = {
    "first_name": "first_name",
    "sports": "sport",
    "sport": "sport",
    "level": "level",
    "goals": "goal",
    "goal": "goal",
    "equipment": "equipment",
    "weekly_slots": "weekly_slots",
    "weight_kg": "weight_kg",
    "height_cm": "height_cm",
    "age": "age",
    "gender": "gender",
}

ALLOWED_FIELDS = set(FIELD_TO_DB.keys())


# ── Endpoints ─────────────────────────────────────────────────────────


@router.get("")
async def get_profile(user: dict = Depends(get_current_user)):
    """Retourne le profil complet de l'utilisateur connecté."""
    safe_user = {k: v for k, v in user.items() if k != "password_hash"}
    return safe_user


@router.patch("")
async def update_profile(
    profile: dict,
    user: dict = Depends(get_current_user),
):
    """Met à jour partiellement le profil de l'utilisateur connecté.

    Seuls les champs autorisés sont modifiés. Les noms de champs
    frontend sont automatiquement mappés vers les colonnes DB
    (ex: "sports" → "sport", "goals" → "goal").
    """
    updates = {}
    for frontend_key, value in profile.items():
        if frontend_key in ALLOWED_FIELDS and value is not None:
            db_col = FIELD_TO_DB[frontend_key]
            updates[db_col] = value

    if not updates:
        return user  # Rien à mettre à jour

    update_user(user["id"], updates)
    updated_user = {k: v for k, v in user.items() if k != "password_hash"}
    updated_user.update(updates)
    return updated_user
