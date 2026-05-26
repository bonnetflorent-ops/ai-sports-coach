# -*- coding: utf-8 -*-
"""Sélecteur de concepts — choisit les 2-4 concepts les plus pertinents
pour répondre à une question utilisateur.

Trois stratégies (par ordre de priorité) :
1. DÉTECTION CRITIQUE — douleur/blessure → injection immédiate
2. KEYWORD FALLBACK — mots-clés (gratuit, couvre ~80% des cas)
3. LLM SELECTOR — appel à deepseek-chat (uniquement si score fallback < 2)
"""

import json
import logging
from typing import Optional

from openai import AsyncOpenAI

from src.engine.knowledge import (
    get_all_concepts_for_selector,
    get_intent_rules,
    get_selector_config,
)

logger = logging.getLogger(__name__)

# Seuil de confiance pour les mots-clés dans le fallback
KEYWORD_MATCH_THRESHOLD = 2

# Mots-clés critiques qui déclenchent une alerte immédiate
CRITICAL_KEYWORDS = {
    "douleur": "blessures",
    "mal": "blessures",
    "blessure": "blessures",
    "blessé": "blessures",
    "tendinite": "blessures",
    "genou": "blessures",
    "cheville": "blessures",
    "dos bloqué": "blessures",
}

# Mapping sport → concept blessure
SPORT_INJURY_MAP = {
    "cyclisme": "blessures/cyclisme",
    "vélo": "blessures/cyclisme",
    "running": "blessures/running",
    "course": "blessures/running",
    "course à pied": "blessures/running",
    "musculation": "blessures/fitness-musculation",
    "muscu": "blessures/fitness-musculation",
    "fitness": "blessures/fitness-musculation",
    "salle": "blessures/fitness-musculation",
    "crossfit": "blessures/fitness-musculation",
}


async def select_concepts(
    client: AsyncOpenAI,
    user_message: str,
    user_profile: Optional[dict] = None,
    recent_context: Optional[list[str]] = None,
) -> dict:
    """
    Sélectionne les concepts pertinents pour répondre à un message.

    Args:
        client: Client OpenAI async (pour OpenRouter)
        user_message: Le message de l'utilisateur
        user_profile: Profil utilisateur (dict avec sport, level, etc.)
        recent_context: 2-3 derniers messages pour contexte

    Returns:
        {
            "concepts": ["id/concept1", "id/concept2"],
            "level": 1,
            "reasoning": "..."
        }
    """
    user_profile = user_profile or {}
    recent_context = recent_context or []

    # 1. Détection rapide : douleur = priorité critique
    critical_check = _check_critical(user_message, user_profile)
    if critical_check:
        logger.info(f"ALERTE critique détectée → concepts: {critical_check}")
        return {
            "concepts": critical_check,
            "level": user_profile.get("level", 1),
            "reasoning": "Détection critique (douleur/blessure) — fallback immédiat",
        }

    # 2. Essayer le fallback mot-clé d'abord (gratuit, couvre ~80% des cas)
    fallback_result = _keyword_fallback(user_message, user_profile)
    fallback_score = fallback_result.pop("_score", 0)

    if fallback_score >= 2:
        logger.info(
            f"Fallback mot-clé (score={fallback_score}) → {fallback_result['concepts']}"
        )
        return fallback_result

    # 3. Score faible → essayer le sélecteur LLM
    try:
        result = await _llm_select(client, user_message, user_profile, recent_context)
        logger.info(f"Sélecteur LLM → {result}")
        return result
    except Exception as e:
        logger.warning(
            f"Sélecteur LLM échoué ({e}), fallback mot-clé (score={fallback_score})"
        )
        return fallback_result


async def _llm_select(
    client: AsyncOpenAI,
    user_message: str,
    user_profile: dict,
    recent_context: list[str],
) -> dict:
    """Appelle le petit LLM pour sélectionner les concepts."""

    # Construire la liste des concepts pour le prompt
    all_concepts = get_all_concepts_for_selector()
    concepts_text = _format_concepts_for_prompt(all_concepts)

    # Construire le contexte
    sport = user_profile.get("sport", "non spécifié")
    level = user_profile.get("level", 1)
    goal = user_profile.get("goal", "non spécifié")
    ctl = user_profile.get("ctl", "N/A")
    tsb = user_profile.get("tsb", "N/A")

    context_str = ""
    if recent_context:
        context_str = "CONTEXTE RÉCENT (3 derniers messages) :\n" + "\n".join(
            f"- {m}" for m in recent_context[-3:]
        )

    system_prompt = f"""Tu es un classifieur spécialisé en sciences du sport.
Ta seule mission est de sélectionner les concepts de connaissance pertinents.

Retourne UNIQUEMENT un objet JSON :
{{"concepts": ["id1", "id2"], "level": 1, "reasoning": "1 phrase"}}

RÈGLES :
- 2 à 4 concepts MAXIMUM
- level = {level} (niveau de l'athlète : 1=débutant, 2=intermédiaire, 3=expert)
- Si douleur ou blessure → priorité CRITIQUE au concept du sport concerné
- Si fatigue/épuisement → injecte TOUJOURS recuperation/surcompensation-surentrainement
- Si démotivation → injecte psychologie/motivation-autodetermination
- Ne sélectionne PAS de concept hors-sujet

CONCEPTS DISPONIBLES :
{concepts_text}"""

    user_prompt = f"""ATHLÈTE :
Sport: {sport}
Niveau: {level}
Objectif: {goal}
Charge: CTL={ctl}, TSB={tsb}

{context_str}

QUESTION DE L'ATHLÈTE :
{user_message}

Sélectionne les 2-4 concepts les plus pertinents."""

    config = get_selector_config()
    selector_model = config.get("selector_model", "deepseek/deepseek-chat")

    response = await client.chat.completions.create(
        model=selector_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.0,  # Déterministe
        max_tokens=200,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    result = json.loads(raw)

    # Validation
    if "concepts" not in result or not isinstance(result["concepts"], list):
        raise ValueError("Réponse LLM invalide : pas de liste de concepts")

    # Limiter à max_concepts
    max_c = config.get("max_concepts_per_query", 4)
    result["concepts"] = result["concepts"][:max_c]

    # Garantir que level est valide
    result["level"] = max(1, min(3, int(result.get("level", level))))

    return result


def _check_critical(user_message: str, user_profile: dict) -> Optional[list[str]]:
    """
    Détection rapide des situations critiques (douleur, blessure).
    Retourne la liste des concepts à injecter, ou None si pas critique.
    """
    msg_lower = user_message.lower()

    # Détection douleur
    is_pain = any(kw in msg_lower for kw in CRITICAL_KEYWORDS)
    if not is_pain:
        return None

    # Trouver le concept blessure correspondant au sport
    sport = user_profile.get("sport", "").lower()
    injury_concept = None
    for sport_kw, concept_id in SPORT_INJURY_MAP.items():
        if sport_kw in sport or sport_kw in msg_lower:
            injury_concept = concept_id
            break

    concepts = []
    if injury_concept:
        concepts.append(injury_concept)
    else:
        # Si on ne trouve pas le sport, on met les 3 concepts blessures
        concepts = [
            "blessures/cyclisme",
            "blessures/running",
            "blessures/fitness-musculation",
        ]

    # Ajouter gestion de charge (souvent lié)
    concepts.append("planification/gestion-charge")

    return concepts[:4]


# Mots-clés par règle d'intention (indexés pour matching rapide)
INTENT_KEYWORDS = {
    "fatigue_surentrainement": [
        "fatigué", "fatigue", "épuisé", "crevé", "pas en forme",
        "récupère pas", "sommeil", "dors mal", "insomnie",
        "surentraînement", "récupération",
    ],
    "planifier_saison": [
        "planifier", "saison", "organiser", "programme", "plan",
        "préparation", "période", "objectif saison",
    ],
    "ameliorer_performance": [
        "progresser", "performance", "plus vite", "puissance",
        "endurance", "améliorer", "perf", "chrono", "temps",
    ],
    "gerer_nutrition": [
        "manger", "nutrition", "repas", "protéine", "glucide",
        "boire", "hydratation", "alimentation", "régime",
        "complément", "supplément", "whey", "gel",
    ],
    "blessure_douleur": [
        "douleur", "mal", "blessure", "tendinite", "genou",
        "cheville", "dos bloqué",
    ],
    "sommeil_recuperation": [
        "sommeil", "dormir", "récupération", "repos", "nuit",
        "sieste", "hrv", "variabilité",
    ],
    "motivation_mental": [
        "motivation", "démotivé", "envie", "mental", "bloqué",
        "plus envie", "abandonner", "lassé",
    ],
    "debutant_decouverte": [
        "débutant", "débuter", "débute", "commencer", "base", "découvrir",
        "première fois", "comment faire", "novice",
    ],
    "norvegienne_question": [
        "norvégien", "norvégienne", "norvège", "méthode norvégienne",
        "polarisé", "polarisée", "80/20", "80:20", "seiler",
        "inge brigtsen", "jacob", "jakob", "blummenfelt",
    ],
    "courir_lentement": [
        "courir lentement", "lentement", "escargot", "endurance fondamentale",
        "footing", "zone 2", "zone deux", "endurance de base",
        "base aérobie", "courir doucement", "allure facile",
    ],
    "seuil_lactate_question": [
        "seuil", "lactate", "lactique", "double seuil", "3x10",
        "5x6", "10x3", "mmol", "mlss", "seuil aérobie",
        "seuil anaérobie", "sv1", "sv2",
    ],
    "methode_norvegienne_pratique": [
        "semaine type", "exemple semaine", "plan norvégien",
        "double séance", "bi-quotidien", "application",
    ],
}


def _keyword_fallback(user_message: str, user_profile: dict) -> dict:
    """
    Fallback basé sur les mots-clés et les règles d'intention.
    Utilisé si le LLM sélecteur est indisponible.
    """
    msg_lower = user_message.lower()
    intent_rules = get_intent_rules()

    # Matcher les mots-clés d'intention
    best_match = None
    best_score = 0

    for rule_id, keywords in INTENT_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in msg_lower)
        if score > best_score:
            best_score = score
            best_match = rule_id

    if best_match and best_score >= 1:
        rule = intent_rules.get(best_match, {})
        if isinstance(rule, dict) and "concepts" in rule:
            return {
                "concepts": rule["concepts"][:4],
                "level": user_profile.get("level", 1),
                "reasoning": f"Fallback: règle '{best_match}' (score={best_score})",
                "_score": best_score,
            }

    # Fallback ultime : concepts les plus généraux
    return {
        "concepts": [
            "physiologie/systemes-energetiques",
            "seances/endurance-fondamentale",
        ],
        "level": user_profile.get("level", 1),
        "reasoning": "Fallback ultime (aucune règle trouvée)",
        "_score": 0,
    }


def _format_concepts_for_prompt(concepts: list[dict]) -> str:
    """Formate la liste des concepts pour le prompt du sélecteur (sans mots-clés)."""
    lines = []
    current_domain = None

    for c in concepts:
        domain = c["domain"]
        if domain != current_domain:
            current_domain = domain
            lines.append(f"\n## {domain.upper()}")
        # Format compact : id : nom (pas de mots-clés → économise ~40% de tokens)
        lines.append(f"  - {c['id']} : {c['name']}")

    return "\n".join(lines)
