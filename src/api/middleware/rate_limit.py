# -*- coding: utf-8 -*-
"""
Rate limiting middleware — per-user in-memory sliding window.

Limites :
- 10 messages / minute
- 100 messages / heure
- 500 messages / jour

Les timestamps sont nettoyés (>24h) à chaque vérification.
"""
import logging
import time
from collections import defaultdict

logger = logging.getLogger(__name__)

# Stockage : user_id -> [list of timestamps (seconds since epoch)]
_user_requests: dict[str, list[float]] = defaultdict(list)

WINDOW_MINUTE = 60          # 1 minute
WINDOW_HOUR = 3600          # 1 heure
WINDOW_DAY = 86400          # 24 heures

LIMIT_MINUTE = 10
LIMIT_HOUR = 100
LIMIT_DAY = 500


def _cleanup(user_id: str, now: float):
    """Supprime les timestamps plus vieux que 24h."""
    cutoff = now - WINDOW_DAY
    timestamps = _user_requests.get(user_id, [])
    _user_requests[user_id] = [t for t in timestamps if t > cutoff]


def check_rate_limit(user_id: str) -> bool:
    """
    Vérifie si l'utilisateur a dépassé les limites de taux.

    Args:
        user_id: Identifiant unique de l'utilisateur (UUID).

    Returns:
        True si la requête est autorisée, False si une limite est dépassée.
    """
    now = time.time()
    _cleanup(user_id, now)

    timestamps = _user_requests.get(user_id, [])

    # Compter dans les fenêtres
    minute_ago = now - WINDOW_MINUTE
    hour_ago = now - WINDOW_HOUR

    count_minute = sum(1 for t in timestamps if t > minute_ago)
    count_hour = sum(1 for t in timestamps if t > hour_ago)
    count_day = len(timestamps)

    if count_minute >= LIMIT_MINUTE:
        logger.warning("Rate limit minute dépassé pour user=%s", user_id)
        return False

    if count_hour >= LIMIT_HOUR:
        logger.warning("Rate limit heure dépassé pour user=%s", user_id)
        return False

    if count_day >= LIMIT_DAY:
        logger.warning("Rate limit jour dépassé pour user=%s", user_id)
        return False

    # Enregistrer la requête
    _user_requests[user_id].append(now)
    return True


def get_rate_limit_stats(user_id: str) -> dict:
    """
    Retourne les statistiques de rate limiting pour un utilisateur.
    """
    now = time.time()
    _cleanup(user_id, now)

    timestamps = _user_requests.get(user_id, [])

    minute_ago = now - WINDOW_MINUTE
    hour_ago = now - WINDOW_HOUR

    return {
        "minute": {
            "count": sum(1 for t in timestamps if t > minute_ago),
            "limit": LIMIT_MINUTE,
        },
        "hour": {
            "count": sum(1 for t in timestamps if t > hour_ago),
            "limit": LIMIT_HOUR,
        },
        "day": {
            "count": len(timestamps),
            "limit": LIMIT_DAY,
        },
    }
