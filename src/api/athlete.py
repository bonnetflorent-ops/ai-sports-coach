# -*- coding: utf-8 -*-
"""
Athlete Model API — consultation, correction humaine, badge.
"""
import copy
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.api.dependencies import get_current_user
from src.db.athlete_models import get_latest_model, save_model_version
from src.engine.athlete_model import create_initial_model, SOURCE_PRIORITY

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/athlete", tags=["athlete"])


# ── Modèles ─────────────────────────────────────────────────────────


class ModelPatch(BaseModel):
    """Human correction of a single field in the athlete model.

    ``path`` uses dot notation, e.g. ``physique.ftp_estime.value``.
    ``value`` is the new value for the leaf field.
    """
    path: str
    value: Any


# ── Helpers ─────────────────────────────────────────────────────────


def _navigate_and_patch(model: dict, path: str, value: Any) -> bool:
    """Traverse *model* following dot-separated *path* and set *value*.

    If the parent object of the leaf has a ``source`` key, it is set to
    ``"corrected_by_human"``.

    Returns ``True`` if the path was resolved and the value applied.
    """
    parts = path.split(".")
    obj = model
    for part in parts[:-1]:
        if isinstance(obj, dict) and part in obj:
            obj = obj[part]
        else:
            return False

    leaf = parts[-1]
    if isinstance(obj, dict):
        obj[leaf] = value
        # If sibling "source" exists, upgrade it
        if "source" in obj:
            obj["source"] = "corrected_by_human"
        return True
    return False


def _badge_level(count: int) -> str:
    """Return the badge emoji for a given session count."""
    if count >= 25:
        return "\U0001f947"  # 🥇
    if count >= 10:
        return "\U0001f948"  # 🥈
    return "\U0001f949"  # 🥉


# ── Endpoints ───────────────────────────────────────────────────────


@router.get("/model")
async def get_model(user: dict = Depends(get_current_user)):
    """Retourne le dernier modèle athlète, en crée un si inexistant."""
    user_id = user["id"]
    model = get_latest_model(user_id)

    if model is None:
        # Create initial model
        initial = create_initial_model()
        model = save_model_version(user_id, initial, 1)
        logger.info("Initial athlete model created for user=%s", user_id)

    return model


@router.patch("/model")
async def patch_model(
    patch: ModelPatch,
    user: dict = Depends(get_current_user),
):
    """Correction humaine d'un champ du modèle athlète.

    Incrémente la version à chaque modification et marque la source
    comme ``corrected_by_human``.
    """
    user_id = user["id"]
    current = get_latest_model(user_id)

    if current is None:
        raise HTTPException(status_code=404, detail="Aucun modèle athlète trouvé")

    model_json = copy.deepcopy(
        current.get("model_json") or current
    )

    success = _navigate_and_patch(model_json, patch.path, patch.value)
    if not success:
        raise HTTPException(
            status_code=422,
            detail=f"Impossible de naviguer le chemin: {patch.path}",
        )

    # Increment version
    new_version = (current.get("version") or 1) + 1

    saved = save_model_version(user_id, model_json, new_version)
    return saved


@router.get("/badge")
async def get_badge(user: dict = Depends(get_current_user)):
    """Retourne le badge de l'athlète basé sur le nombre de sessions.

    Niveaux:
    - 🥉 (< 10 sessions)
    - 🥈 (10-24 sessions)
    - 🥇 (>= 25 sessions)
    """
    user_id = user["id"]
    model = get_latest_model(user_id)

    count = 0
    if model:
        model_json = model.get("model_json") or model
        count = model_json.get("meta", {}).get("nb_sessions_totales", 0)

    level = _badge_level(count)
    return {"count": count, "level": level}
