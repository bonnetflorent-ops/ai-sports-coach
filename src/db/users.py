# -*- coding: utf-8 -*-
"""
Repository utilisateurs — CRUD Supabase pour la table `users`.

Toutes les fonctions sont synchrones (supabase-py est synchrone).
Dans le handler async, on les wrap avec asyncio.to_thread().
"""

import logging
from datetime import datetime
from typing import Optional

from src.db import get_supabase_admin

logger = logging.getLogger(__name__)


def get_or_create_user(telegram_id: int, first_name: str, username: Optional[str] = None) -> dict:
    """
    Récupère un utilisateur par telegram_id, ou le crée si inexistant.
    Retourne le dict complet de l'utilisateur.
    """
    admin = get_supabase_admin()

    # Chercher l'utilisateur existant
    result = (
        admin.table("users")
        .select("*")
        .eq("telegram_id", telegram_id)
        .execute()
    )

    if result.data:
        user = result.data[0]
        # Mettre à jour first_name/username si changé
        updates = {}
        if user.get("first_name") != first_name:
            updates["first_name"] = first_name
        if username and user.get("username") != username:
            updates["username"] = username
        if updates:
            updates["updated_at"] = "now()"
            admin.table("users").update(updates).eq("id", user["id"]).execute()
            user.update(updates)
        return user

    # Créer un nouvel utilisateur
    new_user = {
        "telegram_id": telegram_id,
        "first_name": first_name,
        "username": username,
    }
    result = admin.table("users").insert(new_user).execute()
    logger.info(f"Nouvel utilisateur créé: telegram_id={telegram_id} (id={result.data[0]['id']})")
    return result.data[0]


def update_user_profile(telegram_id: int, profile: dict) -> dict:
    """
    Met à jour le profil sportif d'un utilisateur.

    Accepte un dict avec les clés:
        sport, level, goal, experience_years, experience (texte → converti),
        ftp_watts, vdot, weight_kg, height_cm, age, resting_hr,
        ctl, atl, tsb, injuries, limitations
    """
    admin = get_supabase_admin()

    # Récupérer l'ID d'abord
    result = admin.table("users").select("id").eq("telegram_id", telegram_id).execute()
    if not result.data:
        raise ValueError(f"Utilisateur telegram_id={telegram_id} introuvable")

    user_id = result.data[0]["id"]

    # Mapper les clés du profil vers les colonnes DB
    field_map = {
        "sport": "sport",
        "level": "level",
        "goal": "goal",
        "experience_years": "experience_years",
        "name": "first_name",
        "ftp_watts": "ftp_watts",
        "vdot": "vdot",
        "weight_kg": "weight_kg",
        "height_cm": "height_cm",
        "age": "age",
        "gender": "gender",
        "email": "email",
        "resting_hr": "resting_hr",
        "ctl": "ctl",
        "atl": "atl",
        "tsb": "tsb",
        "injuries": "injuries",
        "limitations": "limitations",
    }

    updates = {"updated_at": datetime.utcnow().isoformat()}

    for profile_key, db_col in field_map.items():
        if profile_key in profile and profile[profile_key] is not None:
            updates[db_col] = profile[profile_key]

    # Convertir l'expérience texte en années si pas déjà numérique
    if "experience" in profile and "experience_years" not in profile:
        exp_text = str(profile["experience"]).lower()
        exp_map = {
            "débutant": 0,
            "débutante": 0,
            "1 an": 1,
            "2 ans": 2,
            "3 ans": 3,
            "intermédiaire": 2,
            "avancé": 5,
            "expert": 8,
        }
        updates["experience_years"] = exp_map.get(exp_text, 0)
        # On garde aussi experience_years si fourni directement
    elif "experience_years" in profile:
        updates["experience_years"] = profile["experience_years"]

    # Blessures au format JSON
    if "blessures" in profile and profile["blessures"] is not None:
        updates["injuries"] = profile["blessures"]

    if not updates:
        return {}  # Rien à mettre à jour

    result = admin.table("users").update(updates).eq("id", user_id).execute()
    logger.info(f"Profil mis à jour: telegram_id={telegram_id}, champs={list(updates.keys())}")
    return result.data[0] if result.data else {}


def get_user_profile(telegram_id: int) -> dict:
    """
    Récupère le profil complet d'un utilisateur, formaté pour le prompt builder.
    """
    admin = get_supabase_admin()

    result = (
        admin.table("users")
        .select("*")
        .eq("telegram_id", telegram_id)
        .execute()
    )

    if not result.data:
        raise ValueError(f"Utilisateur telegram_id={telegram_id} introuvable")

    user = result.data[0]

    # Formater pour être compatible avec le prompt builder existant
    level_map = {1: "Débutant", 2: "Intermédiaire", 3: "Expert"}

    return {
        "name": user.get("first_name", ""),
        "sport": user.get("sport", "non spécifié"),
        "level": user.get("level", 1),
        "level_name": level_map.get(user.get("level", 1), "Débutant"),
        "goal": user.get("goal", "non spécifié"),
        "experience": f"{user.get('experience_years', 0)} ans",
        "experience_years": user.get("experience_years", 0),
        "blessures": user.get("injuries"),
        "email": user.get("email"),
        "email_verified": user.get("email_verified", False),
        "gender": user.get("gender"),
        "ctl": user.get("ctl"),
        "atl": user.get("atl"),
        "tsb": user.get("tsb"),
        "ftp_watts": user.get("ftp_watts"),
        "vdot": user.get("vdot"),
        "weight_kg": user.get("weight_kg"),
        "height_cm": user.get("height_cm"),
        "age": user.get("age"),
        "resting_hr": user.get("resting_hr"),
        "recent_sessions": None,  # Sera peuplé depuis chat_sessions
    }
