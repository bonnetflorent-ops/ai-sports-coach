# -*- coding: utf-8 -*-
"""
Prompt Builder — Assemble le prompt système du coach avec :
- Les connaissances injectées (concepts sélectionnés)
- Le profil utilisateur complet
- L'historique de coaching
- Les règles de coaching adaptées au niveau
"""

import logging
from typing import Optional

from src.engine.knowledge import load_concept, get_concept_by_id

logger = logging.getLogger(__name__)

LEVEL_INSTRUCTIONS = {
    1: "Langage simple, métaphores, pas de jargon technique. Explique chaque terme.",
    2: "Utilise les zones, les métriques (FC, puissance, RPE, TSS). Donne des fourchettes chiffrées et des plans d'action concrets.",
    3: "Va dans le détail physiologique, cite les mécanismes, utilise la terminologie scientifique avancée.",
}

LEVEL_STYLE = {
    1: "pédagogue et rassurant, comme un prof de sport qui explique à un débutant motivé",
    2: "précis et actionnable, comme un coach qui parle à un athlète qui connaît ses zones",
    3: "technique et sans compromis, comme un préparateur physique qui échange avec un pair",
}


def build_system_prompt(
    selection: dict,
    user_profile: dict,
    coaching_context: Optional[str] = None,
) -> str:
    """
    Construit le prompt système complet pour le LLM coach.

    Args:
        selection: Résultat du sélecteur {"concepts": [...], "level": 1, "reasoning": "..."}
        user_profile: Profil complet de l'utilisateur
        coaching_context: Historique/notes de coaching (optionnel)

    Returns:
        Le prompt système complet (str)
    """
    concepts = selection.get("concepts", [])
    level = selection.get("level", user_profile.get("level", 1))

    # 1. Charger et formater les connaissances
    knowledge_blocks = _load_knowledge_blocks(concepts, level)

    # 2. Construire le profil
    profile_block = _build_profile_block(user_profile, level)

    # 3. Construire les règles de coaching
    rules_block = _build_rules_block(level, user_profile)

    # 4. Contexte de coaching
    context_block = ""
    if coaching_context:
        context_block = f"""
CONTEXTE DE COACHING :
{coaching_context}
"""

    # 5. Assemblage final
    system_prompt = f"""Tu es un assistant d'entraînement IA expert, spécialisé en {user_profile.get('sport', 'sport')}.

{profile_block}
{context_block}
CONNAISSANCES SCIENTIFIQUES PERTINENTES :
{knowledge_blocks}

{rules_block}

Style de communication : {LEVEL_STYLE.get(level, LEVEL_STYLE[1])}.
Réponds de manière concise et actionnable. L'athlète veut des conseils, pas un cours magistral.
Si tu ne sais pas ou si la question sort de ton expertise, dis-le honnêtement."""

    return system_prompt


def _load_knowledge_blocks(concepts: list[str], level: int) -> str:
    """Charge et formate chaque concept pour le niveau cible."""
    blocks = []

    for i, concept_id in enumerate(concepts, 1):
        meta = get_concept_by_id(concept_id)
        content = load_concept(concept_id, level)

        if content.startswith("[Concept") or content.startswith("[Niveau"):
            logger.warning(f"Concept non chargé: {concept_id} → {content}")
            continue

        # Nettoyer les footnotes pour réduire le bruit
        content = _clean_footnotes(content)

        name = meta["name"] if meta else concept_id
        blocks.append(f"### {i}. {name}\n{content}")

    if not blocks:
        return "(Aucune connaissance spécifique chargée — réponds avec tes connaissances générales en sciences du sport.)"

    return "\n\n".join(blocks)


def _build_profile_block(profile: dict, level: int) -> str:
    """Construit le bloc profil utilisateur."""
    name = profile.get("name", "Athlète")
    sport = profile.get("sport", "non spécifié")
    goal = profile.get("goal", "non spécifié")
    experience = profile.get("experience", "non spécifiée")
    level_name = {1: "Débutant", 2: "Intermédiaire", 3: "Expert"}.get(level, "?")

    lines = [
        "PROFIL DE L'ATHLÈTE :",
        f"- Prénom : {name}",
        f"- Niveau : {level_name}",
        f"- Sport(s) : {sport}",
        f"- Objectif : {goal}",
        f"- Expérience : {experience}",
    ]

    # Métriques si disponibles
    ctl = profile.get("ctl")
    tsb = profile.get("tsb")
    if ctl is not None:
        lines.append(f"- Charge actuelle : CTL={ctl}" + (f", TSB={tsb}" if tsb is not None else ""))

    blessures = profile.get("blessures")
    if blessures:
        lines.append(f"- Blessures/contraintes : {blessures}")

    # Dernières séances si disponibles
    recent = profile.get("recent_sessions")
    if recent:
        lines.append(f"- Dernières séances : {recent}")

    return "\n".join(lines)


def _build_rules_block(level: int, profile: dict) -> str:
    """Construit les règles de coaching adaptées au niveau et au profil."""
    sport = profile.get("sport", "")
    ctl = profile.get("ctl")

    base_rules = f"""RÈGLES DE COACHING :
1. Niveau de langage : {LEVEL_INSTRUCTIONS.get(level, LEVEL_INSTRUCTIONS[1])}
2. Base TOUJOURS tes conseils sur les connaissances scientifiques injectées ci-dessus.
   Si une information n'est pas dans les connaissances, signale-le.
3. Si l'athlète signale une douleur → priorité SÉCURITÉ. Recommande d'abord d'arrêter
   ou réduire la charge, puis suggère des adaptations. JAMAIS de diagnostic médical.
4. Équilibre tes réponses : ne pose pas plus de 2-3 questions à la fois.
5. SIGLES TECHNIQUES : à la première utilisation d'un sigle dans ta réponse (FTP, CTL, TSB,
   PMA, VMA, VO2max, FC, RPE, TSS, IF, NP, VI, SV1, SV2, PMC, HRV, etc.), donne sa
   définition complète entre parenthèses. Exemple : "ta FTP (Functional Threshold Power,
   puissance maximale soutenable 1h)". Ne présume JAMAIS que l'athlète connaît un sigle,
   même pour des termes que tu juges courants."""

    # Règle spécifique si on a les métriques de charge
    if ctl is not None:
        tsb = profile.get("tsb", 0)
        base_rules += f"""
6. CHARGE ACTUELLE : CTL (Charge d'entraînement chronique)={ctl}, TSB (Balance de stress)={tsb}.
   Adapte tes recommandations d'intensité :
   - Si TSB < -20 : privilégie la récupération, ne propose pas de haute intensité
   - Si TSB entre -10 et +5 : zone optimale pour du travail de qualité
   - Si TSB > +10 : l'athlète est frais, peut encaisser une charge élevée"""
        base_rules += f"""
7. Sois encourageant mais honnête. Pas de positivité toxique.
8. Si la question est hors de ton champ (médical, légal), oriente vers un professionnel."""
    else:
        base_rules += f"""
6. Sois encourageant mais honnête. Pas de positivité toxique.
7. Si la question est hors de ton champ (médical, légal), oriente vers un professionnel."""

    return base_rules


def _clean_footnotes(content: str) -> str:
    """Supprime les références de footnotes [^1], [^2] pour alléger le prompt."""
    import re
    return re.sub(r"\[\^\d+(?:,\d+)*\]", "", content)
