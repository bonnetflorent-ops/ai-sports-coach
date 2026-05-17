"""Tracking des coûts LLM par utilisateur."""
from collections import defaultdict
import time

# Coût par million de tokens (prix OpenRouter mai 2026, USD → EUR ≈×0.92)
MODEL_COSTS_PER_M = {
    "deepseek/deepseek-v4-pro": {"input": 0.55, "output": 2.19},
    "deepseek/deepseek-chat": {"input": 0.14, "output": 0.28},
}

_user_costs: dict[int, float] = defaultdict(float)
_user_message_count: dict[int, int] = defaultdict(int)
_daily_totals: dict[int, float] = defaultdict(float)
_daily_reset: float = time.time()

DAILY_RESET_SECONDS = 86400  # 24h


def _reset_daily_if_needed():
    """Reset les compteurs quotidiens si 24h se sont écoulées."""
    global _daily_reset, _daily_totals
    now = time.time()
    if now - _daily_reset > DAILY_RESET_SECONDS:
        _daily_totals.clear()
        _daily_reset = now


def track_cost(
    telegram_id: int, model: str, tokens_in: int, tokens_out: int
) -> float:
    """Enregistre le coût d'un appel LLM pour un utilisateur.

    Retourne le coût en euros de cet appel.
    """
    _reset_daily_if_needed()

    costs = MODEL_COSTS_PER_M.get(model, {"input": 0.55, "output": 2.19})
    cost_eur = (
        (tokens_in / 1_000_000) * costs["input"]
        + (tokens_out / 1_000_000) * costs["output"]
    )

    _user_costs[telegram_id] += cost_eur
    _daily_totals[telegram_id] += cost_eur
    _user_message_count[telegram_id] += 1

    return cost_eur


def get_user_cost(telegram_id: int) -> dict:
    """Retourne les stats de coût pour un utilisateur."""
    _reset_daily_if_needed()
    return {
        "total_cost_eur": round(_user_costs.get(telegram_id, 0), 4),
        "daily_cost_eur": round(_daily_totals.get(telegram_id, 0), 4),
        "message_count": _user_message_count.get(telegram_id, 0),
    }


def get_global_stats() -> dict:
    """Stats globales pour l'endpoint /metrics."""
    _reset_daily_if_needed()
    return {
        "active_users": len(_user_message_count),
        "total_cost_eur": round(sum(_user_costs.values()), 2),
        "daily_cost_eur": round(sum(_daily_totals.values()), 2),
        "top_users_by_cost": sorted(
            [{"id": uid, "cost_eur": round(c, 4)} for uid, c in _user_costs.items()],
            key=lambda x: x["cost_eur"],
            reverse=True,
        )[:10],
    }