# -*- coding: utf-8 -*-
"""
Facts API — consultation des faits extraits des conversations.
"""
import logging

from fastapi import APIRouter, Depends

from src.api.dependencies import get_current_user
from src.db.facts import get_facts_by_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/facts", tags=["facts"])

# Noms lisibles pour les catégories
CATEGORY_LABELS: dict[str, str] = {
    "entraînement": "🏃 Entraînement",
    "blessure": "⚠️ Blessure",
    "objectif": "🎯 Objectif",
    "préférence": "💡 Préférence",
    "nutrition": "🍎 Nutrition",
    "historique": "📜 Historique",
    "équipement": "🎒 Équipement",
    "récupération": "😴 Récupération",
    "autre": "📌 Autre",
}


@router.get("")
async def list_facts(user: dict = Depends(get_current_user)):
    """Retourne tous les faits extraits pour l'utilisateur, triés par importance."""
    facts = get_facts_by_user(user["id"], limit=50)

    return {
        "facts": [
            {
                "id": f["id"],
                "fact": f["fact"],
                "category": f["category"],
                "category_label": CATEGORY_LABELS.get(f["category"], f["category"]),
                "importance": f["importance"],
                "created_at": f.get("created_at"),
            }
            for f in facts
        ],
        "total": len(facts),
    }
