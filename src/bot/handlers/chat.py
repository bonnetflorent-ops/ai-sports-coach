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
import structlog

from aiogram import Router, types
from aiogram.fsm.context import FSMContext

from src.engine.llm import get_client, chat as llm_chat, chat_with_metrics as llm_chat_metrics
from src.engine.selector import select_concepts
from src.engine.prompt_builder import build_system_prompt
from src.engine.cost_tracker import track_cost, get_user_cost
from src.bot.handlers.start import Onboarding
from src.utils.config import settings

from src.db.users import (
    get_or_create_user,
    update_user_profile,
    get_user_profile,
)
from src.db.sessions import (
    get_or_create_active_session,
    get_recent_context,
    save_message,
    get_recent_summaries,
    _get_active_session_id,
    summarize_session,
    get_session_messages,
)

router = Router(name="chat")
logger = structlog.get_logger(__name__)

# Telegram message limit (4096 chars, with safety margin)
TELEGRAM_MAX_CHARS = 4000


async def _summarize_session_async(session_id: str):
    """Summarize a session in the background (doesn't block the bot)."""
    try:
        await asyncio.to_thread(summarize_session, session_id)
    except Exception:
        pass  # Never crash the bot


def _split_long_message(text: str, max_chars: int = TELEGRAM_MAX_CHARS) -> list[str]:
    """Split a long message into Telegram-safe chunks.

    Splits at paragraph boundaries (double newline) first,
    then at sentence boundaries (. ! ?) if a paragraph is still too long,
    and finally hard-splits if all else fails.
    """
    if len(text) <= max_chars:
        return [text]

    chunks = []
    paragraphs = text.split("\n\n")

    for para in paragraphs:
        if len(para) <= max_chars:
            if para.strip():
                chunks.append(para.strip())
        else:
            # Try splitting at sentence boundaries
            import re
            sentences = re.split(r"(?<=[.!?])\s+", para)
            current = ""
            for sentence in sentences:
                if len(current) + len(sentence) + 1 <= max_chars:
                    current = f"{current} {sentence}".strip() if current else sentence
                else:
                    if current:
                        chunks.append(current)
                    # If a single sentence is still too long, hard-split
                    if len(sentence) > max_chars:
                        for i in range(0, len(sentence), max_chars):
                            chunks.append(sentence[i:i + max_chars])
                    else:
                        current = sentence
            if current:
                chunks.append(current)

    # Merge small tail chunks with previous ones if possible
    merged = []
    for chunk in chunks:
        if merged and len(merged[-1]) + len(chunk) + 2 <= max_chars:
            merged[-1] = f"{merged[-1]}\n\n{chunk}"
        else:
            merged.append(chunk)

    return merged


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
            logger.error("onboarding_phase1_error", error=str(e), exc_info=True)
            await state.clear()
            await message.answer("Souci technique. Réessaie /start.")
        return

    # Phase 2: infos optionnelles → questionnaire PAR-Q
    if current_state == Onboarding.details.state:
        try:
            # Parser les détails
            details = _parse_details(message.text)
            if details:
                await asyncio.to_thread(update_user_profile, user_id, details)

            # Passer au questionnaire PAR-Q
            await message.answer(
                "👍 Noté ! Dernière étape avant de commencer : un petit questionnaire "
                "de santé obligatoire (PAR-Q).\n\n"
                "Réponds simplement par les *numéros* des questions où tu réponds OUI. "
                "Exemple : « 1, 4 » ou « non » si tout va bien.\n\n"
                "1️⃣ Un médecin t'a-t-il déjà dit que tu avais un problème cardiaque "
                "et que tu ne devais faire que l'activité physique prescrite ?\n"
                "2️⃣ Ressens-tu une douleur à la poitrine quand tu fais de l'activité physique ?\n"
                "3️⃣ As-tu eu des douleurs à la poitrine sans activité physique au cours du dernier mois ?\n"
                "4️⃣ As-tu des problèmes osseux ou articulaires qui pourraient être aggravés par l'activité physique ?\n"
                "5️⃣ Perds-tu l'équilibre ou as-tu déjà perdu connaissance ?\n"
                "6️⃣ Prends-tu des médicaments pour la tension artérielle ou un problème cardiaque ?\n"
                "7️⃣ Y a-t-il une autre raison pour laquelle tu ne devrais pas faire d'activité physique ?"
            )
            await state.set_state(Onboarding.parq)
        except Exception as e:
            logger.error("onboarding_phase2_error", error=str(e), exc_info=True)
            await state.clear()
            await message.answer("Souci technique. Réessaie /start.")
        return

    # Phase 3: PAR-Q → message de bienvenue
    if current_state == Onboarding.parq.state:
        await state.clear()
        try:
            # Parser les réponses PAR-Q
            parq_oui = _parse_parq(message.text)

            # Charger le profil complet
            profile = await asyncio.to_thread(get_user_profile, user_id)
            athlete_name = profile.get("name", prenom)

            # Envoyer "..." puis générer le message d'accueil proactif
            ack = await message.answer("...")

            # Si PAR-Q a des OUI → avertissement
            parq_warning = ""
            if parq_oui:
                parq_warning = (
                    "\n⚠️ ATTENTION : L'athlète a répondu OUI aux questions PAR-Q suivantes : "
                    + ", ".join(str(q) for q in parq_oui)
                    + ". Ajoute un avertissement bienveillant dans ton message "
                    "(« consulte ton médecin avant d'augmenter ton activité ») mais ne sois pas alarmiste."
                )

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
{parq_warning}
RÈGLES POUR CE MESSAGE :
1. Commence par un mot d'accueil chaleureux
2. Montre que tu as bien compris son profil et son objectif
3. Si l'athlète a mentionné une douleur/blessure → donne UN conseil concret
4. Si tu as son poids/taille/âge → utilise-les pour contextualiser tes conseils
5. Propose UNE action concrète pour cette semaine
6. Termine par UNE question ouverte sur son planning/routine
7. Reste concis (8-12 lignes max), français courant, émojis avec parcimonie
8. IMPORTANT : ne termine PAS par "n'hésite pas à..." — sois proactif.
9. Termine par une petite ligne de disclaimer : « ⚠️ Je suis une IA, pas un médecin. En cas de doute ou de douleur, consulte un professionnel de santé. »"""

            client = get_client()
            welcome_response = await llm_chat([
                {"role": "system", "content": welcome_prompt},
                {"role": "user", "content": "Génère le message de bienvenue pour cet athlète."},
            ], max_tokens=2000)

            chunks = _split_long_message(welcome_response)
            await ack.edit_text(chunks[0])
            for chunk in chunks[1:]:
                await message.answer(chunk)
            logger.info("onboarding_complete", user_id=user_id, parq_oui=parq_oui or [])

        except Exception as e:
            logger.error("onboarding_phase3_error", error=str(e), exc_info=True)
            await message.answer(
                "J'ai bien tout noté ! Tu peux commencer à me parler — "
                "entraînement, nutrition, récupération, vas-y."
            )
        return

    # --- Étape 0.5: Vérifier le quota quotidien ---
    DAILY_COST_LIMIT = 0.08  # 8 centimes par jour max (~15 messages avec max_tokens=2000)
    costs = get_user_cost(user_id)
    if costs["daily_cost_eur"] > DAILY_COST_LIMIT and current_state is None:
        await message.answer(
            "Tu as atteint ta limite de coaching pour aujourd'hui 🔄 "
            "Reviens demain pour continuer !"
        )
        return

    # --- Étape 1: Charger l'utilisateur et la session ---
    profile = FALLBACK_PROFILE.copy()
    session = None
    previous_summaries = []

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
        # Check for expired session first (for auto-summarization)
        old_session = None
        try:
            old_session = await asyncio.to_thread(_get_active_session_id, user_id)
        except Exception:
            pass

        session = await asyncio.to_thread(
            get_or_create_active_session, user_id
        )

        # If session changed (old one expired), trigger background summarization
        if (
            old_session
            and old_session.get("message_count", 0) > 0
            and not old_session.get("session_summary")
            and old_session["id"] != session["id"]
        ):
            asyncio.create_task(_summarize_session_async(old_session["id"]))
            logger.info(
                "auto_summarize_triggered",
                old_session=old_session["id"][:8],
                new_session=session["id"][:8],
            )

        # Fetch previous session summaries for coaching context
        previous_summaries = []
        try:
            previous_summaries = await asyncio.to_thread(
                get_recent_summaries, user_id
            )
        except Exception:
            pass
    except Exception as e:
        logger.warning("supabase_degraded", error=str(e))

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
            "concept_selection",
            user_id=user_id,
            concepts=selection["concepts"],
            level=selection["level"],
            reasoning=selection["reasoning"],
        )

        # Build coaching context from session messages + summaries + facts
        coaching_context_parts = []

        # 1. Current session messages (hot memory — A2)
        if session:
            try:
                session_msgs = await asyncio.to_thread(
                    get_session_messages, session["id"], limit=10
                )
                if session_msgs:
                    lines = ["CONVERSATION EN COURS :"]
                    for m in session_msgs:
                        role_label = "athlète" if m["role"] == "user" else "coach"
                        lines.append(f"[{role_label}] {m['content']}")
                    coaching_context_parts.append("\n".join(lines))
            except Exception:
                pass

        # 2. Relevant persistent facts (warm memory — C6)
        try:
            from src.engine.embeddings import embed_text
            from src.db.facts import get_relevant_facts

            msg_embedding = await asyncio.to_thread(embed_text, message.text)
            if not all(v == 0.0 for v in msg_embedding):
                db_user_id = str(profile.get("id", ""))
                if db_user_id:
                    facts = await asyncio.to_thread(
                        get_relevant_facts, db_user_id, msg_embedding, 5
                    )
                    if facts:
                        fact_lines = ["FAITS CONNUS SUR L'ATHLÈTE :"]
                        for f in facts:
                            cat = f.get("category", "autre")
                            fact_lines.append(f"- {f['fact']}   [{cat}]")
                        coaching_context_parts.append("\n".join(fact_lines))
        except Exception:
            pass

        # 3. Previous session summaries (warm memory — B4)
        if previous_summaries:
            summary_lines = ["SESSIONS PRÉCÉDENTES :"]
            for s in previous_summaries:
                date_str = (s.get("started_at") or "?")[:10]
                summary_lines.append(f"- {date_str}: {s['session_summary']}")
            coaching_context_parts.append("\n".join(summary_lines))

        coaching_context = "\n\n".join(coaching_context_parts) if coaching_context_parts else None

        # --- Étape 4: Construire le prompt système ---
        system_prompt = build_system_prompt(
            selection=selection,
            user_profile=profile,
            coaching_context=coaching_context,
        )

        # --- Étape 5: Appeler le LLM coach ---
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"[{profile.get('name', prenom)}] {message.text}"},
        ]

        result = await llm_chat_metrics(messages, max_tokens=2000)
        response = result["content"]

        # Track cost
        call_cost = track_cost(
            telegram_id=user_id,
            model=result.get("model", settings.llm_model),
            tokens_in=result["tokens_in"],
            tokens_out=result["tokens_out"],
        )
        logger.info(
            "llm_call",
            user_id=user_id,
            tokens_in=result["tokens_in"],
            tokens_out=result["tokens_out"],
            cost_eur=round(call_cost, 6),
            concepts=selection["concepts"],
        )

        # --- Étape 6: Sauvegarder les messages ---
        if session:
            try:
                # Message utilisateur
                await asyncio.to_thread(
                    save_message,
                    session_id=session["id"],
                    role="user",
                    content=message.text,
                    tokens_in=result["tokens_in"],
                    tokens_out=result["tokens_out"],
                    cost_eur=round(call_cost, 6),
                    concepts_used=selection.get("concepts"),
                    level_used=selection.get("level"),
                )
                # Réponse assistant
                await asyncio.to_thread(
                    save_message,
                    session_id=session["id"],
                    role="assistant",
                    content=response,
                    tokens_in=result["tokens_in"],
                    tokens_out=result["tokens_out"],
                    cost_eur=round(call_cost, 6),
                    concepts_used=selection.get("concepts"),
                    level_used=selection.get("level"),
                )
            except Exception as e:
                logger.warning("save_message_failed", error=str(e))

        # --- Background fact extraction (C5) ---
        # Trigger every 5 messages in the session
        if session:
            msg_count = session.get("message_count", 0) + 1
            if msg_count % 5 == 0:
                async def _extract_and_store():
                    try:
                        from src.engine.fact_extractor import extract_facts_from_messages
                        from src.engine.embeddings import embed_text
                        from src.db.facts import add_fact, deduplicate_facts, bump_importance

                        recent_msgs = await asyncio.to_thread(
                            get_session_messages, session["id"], limit=20
                        )
                        if not recent_msgs:
                            return

                        facts = await asyncio.to_thread(
                            extract_facts_from_messages, recent_msgs
                        )
                        if not facts:
                            return

                        db_user_id = str(profile.get("id", ""))
                        if not db_user_id:
                            return

                        for fact_data in facts:
                            try:
                                embedding = await asyncio.to_thread(
                                    embed_text, fact_data["fact"]
                                )
                                if all(v == 0.0 for v in embedding):
                                    continue

                                is_dup, existing = await asyncio.to_thread(
                                    deduplicate_facts, db_user_id, fact_data["fact"]
                                )

                                if is_dup and existing:
                                    await asyncio.to_thread(
                                        bump_importance, existing["id"]
                                    )
                                else:
                                    await asyncio.to_thread(
                                        add_fact,
                                        db_user_id,
                                        fact_data["fact"],
                                        fact_data["category"],
                                        fact_data["importance"],
                                        session["id"],
                                        embedding,
                                    )
                            except Exception:
                                pass
                    except Exception:
                        pass

                asyncio.create_task(_extract_and_store())

        # Remplacer le "..." par la vraie réponse (split si > 4000 chars)
        chunks = _split_long_message(response)
        await ack_msg.edit_text(chunks[0])
        for chunk in chunks[1:]:
            await message.answer(chunk)

    except Exception as e:
        logger.error("chat_error", user_id=user_id, error=str(e), exc_info=True)
        error_text = (
            "Désolé, je rencontre un problème technique. "
            "Réessaie dans un instant. Si ça persiste, contacte le support."
        )
        try:
            await ack_msg.edit_text(error_text)
        except Exception:
            await message.answer(error_text)


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
    # Stratégie : chercher "1." / "1)" / "1 -", extraire le nom, puis nettoyer
    import re

    # Préfixes courants d'auto-présentation à supprimer
    NAME_PREFIXES = [
        r"je m['’]?appelle\s+",
        r"je suis\s+(?!un|une|à|au|en|de|des|du|le|la|les|pas|très)",
        r"mon (?:petit )?prénom\s+(?:c['’]?est|:)\s*",
        r"moi\s+c['’]?est\s+",
        r"alors\s+(?:mon\s+prénom\s+(?:c['’]?est|:)\s*)?",
        r"c['’]?est\s+(?!un|une|à|au|en|de|des|du|le|la|les|pas|très)",
    ]

    def _clean_name(raw: str) -> str:
        """Nettoie un prénom en supprimant les préfixes d'auto-présentation."""
        raw = raw.strip()
        for pattern in NAME_PREFIXES:
            m = re.match(pattern, raw, re.IGNORECASE)
            if m:
                raw = raw[m.end():].strip()
                break
        # Si après nettoyage il reste des mots parasites, prendre le premier mot
        if raw and " " in raw and len(raw) > 20:
            # Probablement du texte libre, prendre le premier mot qui ressemble à un prénom
            words = raw.split()
            for w in words:
                if w[0].isupper() and len(w) >= 2:
                    return w
            return words[0] if len(words[0]) < 20 else raw[:20]
        # Si le résultat fait plus de 30 caractères, c'est pas un prénom
        if len(raw) > 30:
            return raw[:20]
        return raw

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # Pattern: "1. Florent" ou "1) Florent" ou "1 - Florent" ou juste "Florent" en première ligne
        m = re.match(r"1[.)\-\s]+(.+)", stripped)
        if m:
            name = _clean_name(m.group(1))
            # Nettoyer (pas de chiffres, pas plus de 30 chars)
            if name and len(name) < 30 and not name.isdigit():
                profile["name"] = name
                break
        elif lines.index(line) == 0 and len(stripped) < 30 and not any(kw in stripped.lower() for kw in ["cyclisme", "vélo", "running", "course", "triathlon", "fitness", "muscu", "crossfit", "débutant", "intermédiaire", "avancé", "expert", "objectif"]):
            profile["name"] = _clean_name(stripped)
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

    # Objectif — chercher la ligne contenant "4" ou "objectif"
    for line in text.split("\n"):
        line_lower = line.lower().strip()
        if re.match(r"4[.)\-\s]", line_lower) or "objectif" in line_lower:
            profile["goal"] = line_lower
            break

    # Blessures — chercher "6" ou "blessure"
    for line in text.split("\n"):
        line_lower = line.lower().strip()
        if re.match(r"6[.)\-\s]", line_lower) or "blessure" in line_lower or "contrainte" in line_lower:
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

# --- Correction de prénom ---
    # Si l'utilisateur redonne son prénom (ex: "Alors mon prénom c'est : Florent")
    name_patterns = [
        r"(?:alors\s+)?mon\s+(?:petit\s+)?prénom\s+(?:c[''']?est|:)[\s:]*(\w+)",
        r"je\s+m[''']?appelle\s+(\w+)",
        r"je\s+suis\s+(\w+)(?!\s+(?:un|une|à|au|en|de|des|du|le|la|les|pas|très))",
        r"moi\s+c[''']?est\s+(\w+)",
    ]
    for pattern in name_patterns:
        m = re.search(pattern, text_lower, re.IGNORECASE)
        if m:
            name = m.group(1).capitalize()
            if len(name) >= 2 and len(name) < 30 and not name.isdigit():
                details["name"] = name
            break

    # --- Poids ---
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


def _parse_parq(text: str) -> list[int]:
    """Parse les réponses au questionnaire PAR-Q.

    Retourne la liste des numéros de questions où l'utilisateur a répondu OUI.
    Liste vide = tout va bien.
    """
    import re

    text_lower = text.lower().strip()

    # Si l'utilisateur dit "non", "rien", "ras", "aucun" → tout va bien
    if text_lower in ("non", "non.", "rien", "ras", "aucun", "non merci", "0"):
        return []

    # Extraire tous les chiffres de 1 à 7
    oui = []
    for num in re.findall(r"[1-7]", text_lower):
        n = int(num)
        if n not in oui:
            oui.append(n)

    return sorted(oui)
