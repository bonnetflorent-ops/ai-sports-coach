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
    1: "naturel et encourageant, comme un coach qui envoie un message à son athlète — tutoie, sois chaleureux mais pas infantilisant",
    2: "direct et concret, comme un coach qui parle à un athlète qui connaît ses zones — tutoie, va droit au but avec des chiffres utiles",
    3: "précis et sans détour, comme un préparateur physique qui échange avec un pair — tutoie, utilise le jargon technique sans le définir",
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
    system_prompt = f"""Tu es un coach sportif qui discute par messages avec son athlète. Tu es spécialisé en {user_profile.get('sport', 'sport')}.

{profile_block}
{context_block}
CONNAISSANCES SCIENTIFIQUES PERTINENTES :
{knowledge_blocks}

{rules_block}

Ton style : {LEVEL_STYLE.get(level, LEVEL_STYLE[1])}.
Parle comme un humain, pas comme un robot. Écris comme tu parlerais à un pote qui s'entraîne — pas de listes numérotées, pas de structures rigides, pas de formules toutes faites du type "En résumé" ou "Pour conclure". Sois concis : l'athlète est sur son téléphone, il n'a pas envie de lire un roman.
Si la question sort de ton expertise, dis-le simplement. Si tu ne sais pas, avoue-le."""

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
    """Construit le bloc profil utilisateur avec données physiologiques."""
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

    # Métriques d'entraînement
    ctl = profile.get("ctl")
    tsb = profile.get("tsb")
    ftp = profile.get("ftp_watts")
    vdot = profile.get("vdot")
    resting_hr = profile.get("resting_hr")

    if any([ctl is not None, ftp, vdot]):
        lines.append("")
        lines.append("MÉTRIQUES :")
        if ctl is not None:
            lines.append(f"- CTL={ctl}" + (f", TSB={tsb}" if tsb is not None else ""))
        if ftp:
            weight = profile.get("weight_kg")
            pwr = round(ftp / weight, 1) if weight else None
            lines.append(f"- FTP : {ftp}W" + (f" ({pwr} W/kg)" if pwr else ""))
        if vdot:
            lines.append(f"- VDOT : {vdot}")
        if resting_hr:
            lines.append(f"- FC repos : {resting_hr} bpm")

    # Données physiologiques
    weight = profile.get("weight_kg")
    height = profile.get("height_cm")
    age = profile.get("age")
    gender = profile.get("gender")

    if any([weight, height, age, gender]):
        lines.append("")
        lines.append("PHYSIOLOGIE :")
        if weight:
            lines.append(f"- Poids : {weight} kg")
        if height:
            lines.append(f"- Taille : {height} cm")
        if age:
            lines.append(f"- Âge : {age} ans")
        if gender:
            lines.append(f"- Sexe : {gender}")

    # Blessures
    blessures = profile.get("blessures")
    if blessures and blessures != "Aucune":
        lines.append("")
        lines.append(f"⚠️ BLESSURES/CONTRAINTES : {blessures}")

    # Dernières séances
    recent = profile.get("recent_sessions")
    if recent:
        lines.append(f"- Dernières séances : {recent}")

    return "\n".join(lines)


def _build_rules_block(level: int, profile: dict) -> str:
    """Construit les règles de coaching adaptées au niveau et au profil."""
    sport = profile.get("sport", "")
    ctl = profile.get("ctl")

    base_rules = f"""RÈGLES ESSENTIELLES :
- Langage : {LEVEL_INSTRUCTIONS.get(level, LEVEL_INSTRUCTIONS[1])}
- Appuie-toi sur les connaissances scientifiques ci-dessus. Si une info n'y est pas, dis-le.
- Douleur signalée → priorité SÉCURITÉ : recommande de réduire la charge ou d'arrêter, JAMAIS de diagnostic médical.
- Pose 2-3 questions max par message, pas plus.
- Explique chaque sigle technique (FTP, PMA, VMA, etc.) à sa première utilisation dans la conversation.
  Exemple naturel : "ta FTP (la puissance max que tu tiens 1h) est à 260W, donc ton endurance se travaille autour de 145-170W"
- PERSONNALISATION : utilise les données du profil pour justifier chaque conseil chiffré.
  Incorpore-les naturellement, pas comme une fiche technique. Exemples de bonnes formulations :
  "Avec tes 73 kg, bosser à 145-170W en endurance c'est parfait"
  "À 32 ans, laisse-toi 48h de récup après une sortie intense"
  "Ton objectif 120 km avec 3.6W/kg, tu peux viser 4h30-5h"
  Ne JAMAIS lister les données sans les utiliser concrètement."""


    # Règle spécifique si on a les métriques de charge
    if ctl is not None:
        tsb = profile.get("tsb", 0)
        base_rules += f"""
- CHARGE ACTUELLE : CTL={ctl}, TSB={tsb}. Ajuste l'intensité en fonction : TSB < -20 → récup prioritaire, TSB entre -10 et +5 → zone optimale pour du qualité, TSB > +10 → l'athlète est frais, tu peux charger."""
        base_rules += """
- Sois encourageant mais honnête. Pas de positivité toxique.
- Question hors de ton champ → oriente vers un professionnel (médecin, kiné, diététicien)."""
    else:
        base_rules += """
- Sois encourageant mais honnête. Pas de positivité toxique.
- Question hors de ton champ → oriente vers un professionnel (médecin, kiné, diététicien)."""

    return base_rules


def _clean_footnotes(content: str) -> str:
    """Supprime les références de footnotes [^1], [^2] pour alléger le prompt."""
    import re
    return re.sub(r"\[\^\d+(?:,\d+)*\]", "", content)
