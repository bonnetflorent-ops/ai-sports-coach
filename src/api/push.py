# -*- coding: utf-8 -*-
"""
API Push Notifications — gestion des abonnements Web Push.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.api.dependencies import get_current_user
from src.db.push_subscriptions import save_subscription, remove_subscription
from src.utils.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/push", tags=["push"])


class PushSubscriptionRequest(BaseModel):
    endpoint: str
    keys: dict


@router.get("/vapid-public-key")
async def get_vapid_public_key():
    """Retourne la clé publique VAPID pour que le frontend puisse s'abonner."""
    if not settings.vapid_public_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Push notifications non configurées (VAPID_PUBLIC_KEY manquante)",
        )
    return {"public_key": settings.vapid_public_key}


@router.post("/subscribe")
async def subscribe(
    body: PushSubscriptionRequest,
    user: dict = Depends(get_current_user),
):
    """Enregistre un abonnement push pour l'utilisateur courant."""
    user_id = user["id"]
    try:
        sub_dict = {
            "endpoint": body.endpoint,
            "keys": {
                "p256dh": body.keys.get("p256dh"),
                "auth": body.keys.get("auth"),
            },
        }
        save_subscription(user_id, sub_dict)
        logger.info("Push subscription enregistrée pour user=%s", user_id)
        return {"status": "ok"}
    except Exception as e:
        logger.error("Erreur sauvegarde push subscription: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de l'enregistrement de l'abonnement",
        )


@router.delete("/subscribe")
async def unsubscribe(user: dict = Depends(get_current_user)):
    """Supprime l'abonnement push de l'utilisateur courant."""
    user_id = user["id"]
    try:
        remove_subscription(user_id)
        logger.info("Push subscription supprimée pour user=%s", user_id)
        return {"status": "ok"}
    except Exception as e:
        logger.error("Erreur suppression push subscription: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la suppression de l'abonnement",
        )
