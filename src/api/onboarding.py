# -*- coding: utf-8 -*-
"""
Onboarding API — inscription sportive en trois phases.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, field_validator

from src.api.dependencies import get_current_user
from src.db.users import update_user
from src.db.athlete_models import save_model_version
from src.engine.athlete_model import create_initial_model

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])


# ── Modèles ─────────────────────────────────────────────────────────


class Phase1Request(BaseModel):
    sport: str
    level: str
    goal: str
    injuries: str
    equipment: str
    slots: str


class Phase2Request(BaseModel):
    weight: Optional[float] = None
    height: Optional[float] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    email: Optional[str] = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        if v is not None and ("@" not in v or "." not in v.split("@")[-1]):
            raise ValueError("Email invalide")
        return v.strip().lower() if v else v


class ParqItem(BaseModel):
    question: str
    answer: bool


class ParqRequest(BaseModel):
    items: list[ParqItem]

    @field_validator("items")
    @classmethod
    def validate_items(cls, v: list[ParqItem]) -> list[ParqItem]:
        if len(v) != 7:
            raise ValueError("Le PAR-Q doit contenir exactement 7 questions")
        return v


# ── Endpoints ───────────────────────────────────────────────────────


# Mapping niveau string → entier (colonne SMALLINT en DB)
LEVEL_MAP = {
    "debutant": 1,
    "debutante": 1,
    "intermediaire": 2,
    "avance": 3,
    "expert": 3,
}


@router.post("/phase1")
async def phase1(
    body: Phase1Request,
    user: dict = Depends(get_current_user),
):
    """Première phase d'onboarding: informations sportives générales."""
    level_int = LEVEL_MAP.get(body.level.lower(), 1)
    updates = {
        "sport": body.sport,
        "level": level_int,
        "goal": body.goal,
        "injuries": body.injuries,
        "equipment": body.equipment,
        "weekly_slots": body.slots,
        "onboarding_phase": 1,
    }
    update_user(user["id"], updates)
    logger.info("Onboarding phase1 completed for user=%s", user["id"])
    return {"status": "ok", "phase": 1}


@router.post("/phase2")
async def phase2(
    body: Phase2Request,
    user: dict = Depends(get_current_user),
):
    """Deuxième phase d'onboarding: données physiques et contact."""
    updates = {}
    if body.weight is not None:
        updates["weight_kg"] = body.weight
    if body.height is not None:
        updates["height_cm"] = body.height
    if body.age is not None:
        updates["age"] = body.age
    if body.gender is not None:
        updates["gender"] = body.gender
    if body.email is not None:
        updates["email"] = body.email

    if updates:
        updates["onboarding_phase"] = 2
        update_user(user["id"], updates)

    logger.info("Onboarding phase2 completed for user=%s", user["id"])
    return {"status": "ok", "phase": 2}


@router.post("/parq")
async def parq(
    body: ParqRequest,
    user: dict = Depends(get_current_user),
):
    """Questionnaire PAR-Q (7 questions) et finalisation de l'onboarding.

    Après soumission valide, l'onboarding est marqué comme terminé et
    un modèle athlète initial est créé.
    """
    user_id = user["id"]

    # Vérifier qu'il n'y a pas de réponse "oui" contre-indiquant le sport
    any_yes = any(item.answer for item in body.items)

    # Marquer onboarding comme terminé
    update_user(user_id, {
        "onboarding_completed": True,
        "onboarding_phase": 3,
        "parq_responses": [item.model_dump() for item in body.items],
        "parq_any_yes": any_yes,
    })

    # Créer le modèle athlète initial
    from src.db.athlete_models import get_latest_model as _get_latest_model
    existing_model = _get_latest_model(user_id)
    if existing_model is None:
        initial = create_initial_model()
        save_model_version(user_id, initial, 1)
        logger.info("Initial athlete model created after PAR-Q for user=%s", user_id)

    logger.info(
        "Onboarding PAR-Q completed for user=%s (any_yes=%s)",
        user_id, any_yes,
    )
    return {
        "status": "ok",
        "onboarding_completed": True,
        "parq_any_yes": any_yes,
        "message": (
            "Certaines réponses indiquent des contre-indications. "
            "Consultez un professionnel de santé avant de commencer."
            if any_yes
            else "Tout est en ordre pour commencer!"
        ),
    }
