# -*- coding: utf-8 -*-
"""
Handler principal — Chat conversationnel avec injection de connaissances.

Flux complet :
1. Message utilisateur reçu → get_or_create_user (Supabase)
2. Récupérer ou créer une session active
3. Sélecteur LLM choisit les concepts pertinents (avec contexte récent)
4. Prompt builder assemble le système prompt avec connaissances + profil
5. LLM coach répond avec tout le contexte
6. Sauvegarder user + assistant messages dans Supabase
"""

import asyncio
import logging

from aiogram import Router, types
from aiogram.fsm.context import FSMContext

from src.engine.llm import get_client, chat as llm_chat
from src.engine.selector import select_concepts
from src.engine.prompt_builder import build_system_prompt
from src.bot.handlers.start import Onboarding

from src.db.users import (
    get_or_create_user,
    update_user_profile,
    get_user_profile,
)
from src.db.sessions import (
    get_or_create_active_session,
    get_recent_context,
    save_message,
)

router = Router(name="chat")
logger = logging.getLogger(__name__)


# Fallback profile quand Supabase est down (le bot reste utilisable)
FALLBACK_PROFILE = {
    "name": "",
    "sport": "non spécifié",
    "level": 1,
    "goal": "non spécifié",
    "experience": "débutant",
    "blessures": None,
    "ctl": None,
    "tsb": None,
    "recent_sessions": None,
}


@router.message()
async def handle_message(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    prenom = message.from_user.first_name or ""
    username = message.from_user.username

    # --- Étape 0: Onboarding (2 messages max) ---
    current_state = await state.get_state()

    # Phase 1: réponses aux 6 questions → demander les infos optionnelles
    if current_state == Onboarding.waiting.state:
        try:
            user = await asyncio.to_thread(get_or_create_user, user_id, prenom, username)
            profile_data = _parse_onboarding(message.text, prenom)
            await asyncio.to_thread(update_user_profile, user_id, profile_data)

            # Utiliser le prénom parsé (pas le Telegram first_name)
            parsed_name = profile_data.get("name", prenom)

            # Message 2/2 : demander les infos optionnelles
            await message.answer(
                f"Merci {parsed_name} ! Pour affiner tes zones d'entraînement, "
                f"j'aurais besoin de quelques infos (tout est optionnel, réponds juste "
                f"« non » ou « plus tard » si tu préfères) :\n\n"
                f"• Ton poids (kg)\n"
                f"• Ta taille (cm)\n"
                f"• Ton âge\n"
                f"• Ton sexe (H/F)\n"
                f"• Un email de secours (si tu perds Telegram)\n\n"
                f"Réponds en vrac, je trierai."
            )
            await state.set_state(Onboarding.details)
        except Exception as e:
            logger.error(f"Erreur onboarding phase 1: {e}", exc_info=True)
            await state.clear()
            await message.answer("Souci technique. Réessaie /start.")
        return

    # Phase 2: infos optionnelles → message de bienvenue
    if current_state == Onboarding.details.state:
        await state.clear()
        try:
            # Parser les détails
            details = _parse_details(message.text)
            if details:
                await asyncio.to_thread(update_user_profile, user_id, details)

            # Charger le profil complet
            profile = await asyncio.to_thread(get_user_profile, user_id)
            athlete_name = profile.get("name", prenom)

            # Envoyer "..." puis générer le message d'accueil proactif
            ack = await message.answer("...")

            detail_str = ""
            if profile.get("weight_kg"):
                detail_str += f"- Poids : {profile['weight_kg']} kg\n"
            if profile.get("height_cm"):
                detail_str += f"- Taille : {profile['height_cm']} cm\n"
            if profile.get("age"):
                detail_str += f"- Âge : {profile['age']} ans\n"
            if profile.get("gender"):
                detail_str += f"- Sexe : {profile['gender']}\n"

            welcome_prompt = f"""Tu es un coach sportif IA qui vient de terminer l'onboarding avec un nouvel athlète.
Ton message d'accueil doit être PROACTIF : ne dis pas "pose-moi des questions", prends l'initiative.

PROFIL DE L'ATHLÈTE :
- Prénom : {athlete_name}
- Sport : {profile.get('sport', 'cyclisme')}
- Niveau : intermédiaire
- Objectif : {profile.get('goal', 'être en forme')}
- Blessure/contrainte : {profile.get('blessures', 'aucune')}
{detail_str}
RÈGLES POUR CE MESSAGE :
1. Commence par un mot d'accueil chaleureux
2. Montre que tu as bien compris son profil et son objectif
3. Si l'athlète a mentionné une douleur/blessure → donne UN conseil concret
4. Si tu as son poids/taille/âge → utilise-les pour contextualiser tes conseils
5. Propose UNE action concrète pour cette semaine
6. Termine par UNE question ouverte sur son planning/routine
7. Reste concis (8-12 lignes max), français courant, émojis avec parcimonie
8. IMPORTANT : ne termine PAS par "n'hésite pas à..." — sois proactif."""

            client = get_client()
            welcome_response = await llm_chat([
                {"role": "system", "content": welcome_prompt},
                {"role": "user", "content": "Génère le message de bienvenue pour cet athlète."},
            ])

            await ack.edit_text(welcome_response)
            logger.info(f"Onboarding terminé pour user={user_id}")

        except Exception as e:
            logger.error(f"Erreur onboarding phase 2: {e}", exc_info=True)
            await message.answer(
                "J'ai bien tout noté ! Tu peux commencer à me parler — "
                "entraînement, nutrition, récupération, vas-y."
            )
        return

    # --- Étape 1: Charger l'utilisateur et la session ---
    profile = FALLBACK_PROFILE.copy()
    session = None

    try:
        # Créer ou récupérer l'utilisateur
        user = await asyncio.to_thread(
            get_or_create_user, user_id, prenom, username
        )
        # Charger le profil complet
        profile = await asyncio.to_thread(get_user_profile, user_id)
        # Si pas de prénom enregistré (onboarding pas fait), fallback Telegram
        if not profile.get("name"):
            profile["name"] = prenom

        # Récupérer ou créer une session active
        session = await asyncio.to_thread(
            get_or_create_active_session, user_id
        )
    except Exception as e:
        logger.warning(f"Supabase indisponible, mode dégradé: {e}")

    # --- Étape 2: Accusé de réception immédiat ---
    ack_msg = await message.answer("...")

    try:
        client = get_client()

        # Contexte récent pour le sélecteur
        recent_context = []
        if session:
            try:
                recent_context = await asyncio.to_thread(
                    get_recent_context, session["id"], limit=6
                )
            except Exception:
                pass  # Pas grave si on n'a pas le contexte

        # --- Étape 3: Sélectionner les concepts ---
        selection = await select_concepts(
            client=client,
            user_message=message.text,
            user_profile=profile,
            recent_context=recent_context,
        )
        logger.info(
            f"[user={user_id}] Sélection: {selection['concepts']} "
            f"(niveau {selection['level']}, raison: {selection['reasoning']})"
        )

        # --- Étape 4: Construire le prompt système ---
        system_prompt = build_system_prompt(
            selection=selection,
            user_profile=profile,
        )

        # --- Étape 5: Appeler le LLM coach ---
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"[{profile.get('name', prenom)}] {message.text}"},
        ]

        response = await llm_chat(messages)

        # --- Étape 6: Sauvegarder les messages ---
        if session:
            try:
                # Message utilisateur
                await asyncio.to_thread(
                    save_message,
                    session_id=session["id"],
                    role="user",
                    content=message.text,
                    tokens_in=0,  # On pourrait estimer plus tard
                    tokens_out=0,
                    cost_eur=0.0,
                    concepts_used=selection.get("concepts"),
                    level_used=selection.get("level"),
                )
                # Réponse assistant
                await asyncio.to_thread(
                    save_message,
                    session_id=session["id"],
                    role="assistant",
                    content=response,
                    tokens_in=0,
                    tokens_out=0,
                    cost_eur=0.0,
                    concepts_used=selection.get("concepts"),
                    level_used=selection.get("level"),
                )
            except Exception as e:
                logger.warning(f"Sauvegarde message échouée: {e}")

        # Remplacer le "..." par la vraie réponse
        await ack_msg.edit_text(response)

    except Exception as e:
        logger.error(f"[user={user_id}] Erreur: {e}", exc_info=True)
        await ack_msg.edit_text(
            "Désolé, je rencontre un problème technique. "
            "Réessaie dans un instant. Si ça persiste, contacte le support."
        )


def _parse_onboarding(text: str, prenom: str) -> dict:
    """Parse les réponses d'onboarding en un profil utilisateur basique."""
    text_lower = text.lower()
    lines = text.split("\n")
    profile: dict = {
        "name": prenom,  # sera remplacé si trouvé
        "sport": None,
        "level": None,
        "goal": None,
        "experience": "débutant",
        "blessures": None,
    }

    # Prénom — première ligne ou ligne qui commence par "1"
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # Pattern: "1. Florent" ou "1) Florent" ou "1 - Florent" ou juste "Florent" en première ligne
        import re
        m = re.match(r"1[.)\-\s]+(.+)", stripped)
        if m:
            name = m.group(1).strip()
            # Nettoyer (pas de chiffres, pas plus de 30 chars)
            if name and len(name) < 30 and not name.isdigit():
                profile["name"] = name
                break
        elif lines.index(line) == 0 and len(stripped) < 30 and not any(kw in stripped.lower() for kw in ["cyclisme", "vélo", "running", "course", "triathlon", "fitness", "muscu", "crossfit", "débutant", "intermédiaire", "avancé", "expert", "objectif"]):
            profile["name"] = stripped
            break

    # Extraction par mot-clé du sport
    sport_keywords = [
        ("cyclisme", "cyclisme"), ("vélo", "cyclisme"),
        ("running", "running"), ("course à pied", "running"),
        ("course", "running"), ("triathlon", "triathlon"),
        ("natation", "triathlon"), ("fitness", "fitness"),
        ("musculation", "fitness"), ("muscu", "fitness"),
        ("crossfit", "crossfit"), ("salle", "fitness"),
    ]
    for keyword, sport in sport_keywords:
        if keyword in text_lower:
            profile["sport"] = sport
            break

    # Niveau
    if "débutant" in text_lower or "novice" in text_lower:
        profile["level"] = 1
        profile["experience"] = "débutant"
    elif "intermédiaire" in text_lower:
        profile["level"] = 2
        profile["experience"] = "intermédiaire"
    elif "avancé" in text_lower or "expert" in text_lower or "confirmé" in text_lower:
        profile["level"] = 3
        profile["experience"] = "expert"

    # Objectif — chercher la ligne contenant "3" ou "objectif"
    for line in text.split("\n"):
        line_lower = line.lower().strip()
        if "3" in line_lower[:3] or "objectif" in line_lower:
            profile["goal"] = line_lower
            break

    # Blessures — chercher "5" ou "blessure"
    for line in text.split("\n"):
        line_lower = line.lower().strip()
        if "5" in line_lower[:3] or "blessure" in line_lower or "contrainte" in line_lower:
            if any(w in line_lower for w in ["non", "aucun", "pas de", "ras", "rien"]):
                profile["blessures"] = "Aucune"
            else:
                profile["blessures"] = line_lower.strip()
            break

    return profile


def _parse_details(text: str) -> dict:
    """Parse les infos optionnelles : poids, taille, âge, sexe, email."""
    import re

    text_lower = text.lower()
    details: dict = {}

    # Skip si l'utilisateur refuse
    if text_lower.strip() in ("non", "plus tard", "non merci", "pas maintenant", ".", "nan"):
        return {}

    # Poids — cherche un nombre suivi de "kg" ou "kilo"
    m = re.search(r"(\d{2,3})\s*(?:kg|kilos?|k)", text_lower)
    if m:
        w = int(m.group(1))
        if 30 < w < 250:
            details["weight_kg"] = w

    # Taille — cherche un nombre suivi de "cm" ou "m"
    m = re.search(r"(\d{2,3})\s*cm", text_lower)
    if m:
        h = int(m.group(1))
        if 100 < h < 250:
            details["height_cm"] = h
    else:
        # Format "1,77m" ou "1.77"
        m = re.search(r"(\d)[,.](\d{2})\s*m?", text_lower)
        if m:
            h = int(m.group(1)) * 100 + int(m.group(2))
            if 100 < h < 250:
                details["height_cm"] = h

    # Âge — cherche un nombre entre 10 et 99
    m = re.search(r"(?:âge\s*:?\s*|age\s*:?\s*)?(\d{1,2})\s*(?:ans?|a)", text_lower)
    if m:
        a = int(m.group(1))
        if 10 < a < 99:
            details["age"] = a
    else:
        # Cherche un nombre isolé entre 15 et 80 (probablement l'âge)
        m = re.search(r"\b([1-7][0-9])\b(?!\s*(?:kg|kilo|cm|m|h))", text_lower)
        if m:
            a = int(m.group(1))
            if 15 <= a <= 80:
                details["age"] = a

    # Sexe
    if re.search(r"\b(h|homme|m|masculin)\b", text_lower):
        details["gender"] = "H"
    elif re.search(r"\b(f|femme|féminin)\b", text_lower):
        details["gender"] = "F"

    # Email — basic regex
    m = re.search(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text)
    if m:
        email = m.group(0).lower()
        # Common typo fixes
        email = email.replace("@gmial.com", "@gmail.com")
        email = email.replace("@gmal.com", "@gmail.com")
        email = email.replace("@gnail.com", "@gmail.com")
        email = email.replace("@hotmai.com", "@hotmail.com")
        email = email.replace("@yaho.com", "@yahoo.com")
        email = email.replace("@outloo.com", "@outlook.com")
        details["email"] = email

    return details
