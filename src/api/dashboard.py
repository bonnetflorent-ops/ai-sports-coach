# -*- coding: utf-8 -*-
"""
Dashboard API — métriques, graphiques, récapitulatif hebdomadaire.
"""
import logging
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query

from src.api.dependencies import get_current_user
from src.db.athlete_models import get_latest_model
from src.db.weekly_rollups import get_latest_rollup

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def _extract_metrics(model: dict | None) -> dict:
    """Extracts CTL, TSB, VO2max, FCmax, FTP from the athlete model."""
    metrics = {
        "ctl": None,
        "tsb": None,
        "vo2max": None,
        "fcmax": None,
        "ftp": None,
    }

    if model is None:
        return metrics

    model_json = model.get("model_json") or model

    # FTP
    ftp = model_json.get("physique", {}).get("ftp_estime")
    if isinstance(ftp, dict):
        metrics["ftp"] = ftp.get("value")

    # FCmax
    fcmax = model_json.get("physique", {}).get("fcmax")
    if isinstance(fcmax, dict):
        metrics["fcmax"] = fcmax.get("value")

    # CTL / ATL / TSB from etat_actuel
    etat = model_json.get("etat_actuel", {})
    metrics["ctl"] = etat.get("ctl")
    metrics["tsb"] = etat.get("tsb")

    return metrics


@router.get("/metrics")
async def get_metrics(user: dict = Depends(get_current_user)):
    """Extrait les métriques clés du modèle athlète."""
    model = get_latest_model(user["id"])
    metrics = _extract_metrics(model)
    return metrics


@router.get("/chart")
async def get_chart(
    period: str = Query("7d", pattern=r"^(7d|30d|90d)$"),
    user: dict = Depends(get_current_user),
):
    """Retourne une série temporelle CTL/ATL/TSB pour la période demandée.

    Stub: retourne un tableau vide pour l'instant.
    L'implémentation complète viendra lorsque les daily_summaries
    seront historisées.
    """
    # Parse period
    days = int(period.rstrip("d"))

    return {
        "period": period,
        "days": days,
        "series": [],
    }


@router.get("/recap")
async def get_recap(user: dict = Depends(get_current_user)):
    """Retourne le dernier récapitulatif hebdomadaire."""
    rollup = get_latest_rollup(user["id"])
    if rollup is None:
        return {
            "has_recap": False,
            "recap": None,
        }
    return {
        "has_recap": True,
        "recap": rollup,
    }
