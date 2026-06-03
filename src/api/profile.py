# -*- coding: utf-8 -*-
"""
Profile API — gestion et consultation du profil utilisateur.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends

from src.api.dependencies import get_current_user
from src.db.users import update_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/profile", tags=["profile"])


# ── Modèle de mise à jour du profil ─────────────────────────────────


class ProfileUpdate:
    """Modèle pour la mise à jour partielle du profil.

    Tous les champs sont optionnels — seuls les champs fournis
    seront mis à jour.
    """
    def __init__(
        self,
        first_name: Optional[str] = None,
        sports: Optional[str] = None,
        level: Optional[int] = None,
        goals: Optional[str] = None,
        equipment: Optional[str] = None,
        weekly_slots: Optional[int] = None,
        weight_kg: Optional[float] = None,
        height_cm: Optional[float] = None,
        age: Optional[int] = None,
        gender: Optional[str] = None,
    ):
        self.first_name = first_name
        self.sports = sports
        self.level = level
        self.goals = goals
        self.equipment = equipment
        self.weekly_slots = weekly_slots
        self.weight_kg = weight_kg
        self.height_cm = height_cm
        self.age = age
        self.gender = gender

    def to_db_updates(self) -> dict:
        """Convertit les champs non-None en mappage pour la DB."""
        field_map = {
            "first_name": "first_name",
            "sports": "sport",
            "level": "level",
            "goals": "goal",
            "equipment": "equipment",
            "weekly_slots": "weekly_slots",
            "weight_kg": "weight_kg",
            "height_cm": "height_cm",
            "age": "age",
            "gender": "gender",
        }
        updates = {}
        for attr, db_col in field_map.items():
            val = getattr(self, attr, None)
            if val is not None:
                updates[db_col] = val
        return updates


# ── Endpoints ───────────────────────────────────────────────────────


@router.get("")
async def get_profile(user: dict = Depends(get_current_user)):
    """Retourne le profil complet de l'utilisateur connecté."""
    # Ne pas exposer le mot de passe haché
    safe_user = {k: v for k, v in user.items() if k != "password_hash"}
    return safe_user


@router.patch("")
async def update_profile(
    profile: dict,
    user: dict = Depends(get_current_user),
):
    """Met à jour partiellement le profil de l'utilisateur connecté.

    Seuls les champs fournis dans le body JSON seront modifiés.
    """
    # Filtrer les champs autorisés
    allowed_fields = {
        "first_name", "sports", "level", "goals", "equipment",
        "weekly_slots", "weight_kg", "height_cm", "age", "gender",
    }
    updates = {k: v for k, v in profile.items() if k in allowed_fields and v is not None}

    if not updates:
        return user  # Rien à mettre à jour

    update_user(user["id"], updates)
    updated_user = {k: v for k, v in user.items() if k != "password_hash"}
    updated_user.update(updates)
    return updated_user
