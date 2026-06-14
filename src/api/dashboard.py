# -*- coding: utf-8 -*-
"""
Dashboard API — métriques, graphiques, récapitulatif hebdomadaire.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from src.api.dependencies import get_current_user
from src.db.athlete_models import get_latest_model
from src.db.weekly_rollups import get_latest_rollup

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


# ── Modèles de réponse ────────────────────────────────────────────────


class MetricValue(BaseModel):
    name: str
    value: Optional[float] = None
    unit: str
    trend: Optional[str] = None  # "up", "down", "stable"


class ChartPoint(BaseModel):
    date: str
    ctl: Optional[float] = None
    atl: Optional[float] = None
    tsb: Optional[float] = None


class MetricsResponse(BaseModel):
    metrics: list[MetricValue]


class ChartResponse(BaseModel):
    period: str
    days: int
    chart: list[ChartPoint]


class RecapResponse(BaseModel):
    recap: str


class UpcomingSession(BaseModel):
    date: str
    type: str
    duration: str
    description: str


class UpcomingResponse(BaseModel):
    session: Optional[UpcomingSession] = None


# ── Helpers ───────────────────────────────────────────────────────────

METRIC_DEFS = [
    {"name": "CTL", "key": "ctl", "unit": "TSS/jour", "trend": "stable"},
    {"name": "TSB", "key": "tsb", "unit": "TSS", "trend": "stable"},
    {"name": "VO₂max", "key": "vo2max", "unit": "ml/kg/min", "trend": "up"},
    {"name": "FC max", "key": "fcmax", "unit": "bpm", "trend": "stable"},
    {"name": "FTP", "key": "ftp", "unit": "W", "trend": "up"},
]


def _extract_flat_metrics(model: dict | None) -> dict:
    """Extrait les valeurs brutes CTL, TSB, VO2max, FCmax, FTP."""
    flat = {"ctl": None, "tsb": None, "vo2max": None, "fcmax": None, "ftp": None}

    if model is None:
        return flat

    model_json = model.get("model_json") or model

    ftp = model_json.get("physique", {}).get("ftp_estime")
    if isinstance(ftp, dict):
        flat["ftp"] = ftp.get("value")

    fcmax = model_json.get("physique", {}).get("fcmax")
    if isinstance(fcmax, dict):
        flat["fcmax"] = fcmax.get("value")

    etat = model_json.get("etat_actuel", {})
    flat["ctl"] = etat.get("ctl")
    flat["tsb"] = etat.get("tsb")

    return flat


def _build_metric_items(flat: dict) -> list[MetricValue]:
    """Convertit le dictionnaire plat en liste de MetricValue."""
    return [
        MetricValue(
            name=defn["name"],
            value=flat.get(defn["key"]),
            unit=defn["unit"],
            trend=defn["trend"],
        )
        for defn in METRIC_DEFS
    ]


# ── Endpoints ─────────────────────────────────────────────────────────


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(user: dict = Depends(get_current_user)):
    """Extrait les métriques clés du modèle athlète."""
    model = get_latest_model(user["id"])
    flat = _extract_flat_metrics(model)
    return MetricsResponse(metrics=_build_metric_items(flat))


@router.get("/chart", response_model=ChartResponse)
async def get_chart(
    period: str = Query("7d", pattern=r"^(7d|30d|90d)$"),
    user: dict = Depends(get_current_user),
):
    """Retourne une série temporelle CTL/ATL/TSB pour la période demandée.

    Stub: retourne un tableau vide pour l'instant.
    L'implémentation complète viendra lorsque les daily_summaries
    seront historisées.
    """
    days = int(period.rstrip("d"))
    return ChartResponse(period=period, days=days, chart=[])


@router.get("/recap", response_model=RecapResponse)
async def get_recap(user: dict = Depends(get_current_user)):
    """Retourne le dernier récapitulatif hebdomadaire sous forme de texte."""
    rollup = get_latest_rollup(user["id"])
    if rollup is None:
        return RecapResponse(recap="")
    # Formater le rollup en texte lisible
    recap_text = _format_recap(rollup)
    return RecapResponse(recap=recap_text)


def _format_recap(rollup: dict) -> str:
    """Formate un objet rollup en texte lisible."""
    parts = []
    summary = rollup.get("summary") or rollup.get("recap_text") or ""
    if summary:
        parts.append(summary)
    else:
        # Fallback: construire à partir des champs structurés
        week_label = rollup.get("week_label", "")
        if week_label:
            parts.append(f"📅 {week_label}")
        highlights = rollup.get("highlights", [])
        if highlights:
            parts.append("\n".join(f"• {h}" for h in highlights))
        notes = rollup.get("coach_notes", "")
        if notes:
            parts.append(f"\n💡 {notes}")
    return "\n".join(parts) if parts else "Pas encore de récapitulatif disponible."


@router.get("/upcoming", response_model=UpcomingResponse)
async def get_upcoming(user: dict = Depends(get_current_user)):
    """Retourne la prochaine séance planifiée (stub pour le MVP)."""
    # TODO: implémenter la planification réelle des séances
    return UpcomingResponse(session=None)
