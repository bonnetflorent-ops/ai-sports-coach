# -*- coding: utf-8 -*-
"""
Fact extraction from conversation messages using deepseek-chat.
Extracts structured facts: entraînement, blessure, objectif, préférence, etc.
"""

import json
import logging

from openai import OpenAI
from src.utils.config import settings

logger = logging.getLogger(__name__)

EXTRACTOR_MODEL = "deepseek/deepseek-chat"
EXTRACTOR_MAX_TOKENS = 300

_client = None

FACT_CATEGORIES = [
    "entraînement",
    "blessure",
    "objectif",
    "préférence",
    "nutrition",
    "historique",
    "équipement",
    "récupération",
    "autre",
]

EXTRACTION_PROMPT = """Tu es un assistant qui extrait des faits structurés d'une conversation entre un coach IA et un athlète.

RÈGLES :
- Extrais 2 à 6 faits distincts et concis (max 150 caractères par fait)
- Chaque fait doit être une affirmation factuelle sur l'athlète (pas un conseil, pas une question)
- Ignore les salutations, les remerciements, et les conseils donnés par le coach
- Formule les faits à la 3ème personne (ex: "Florent court 3×/semaine")
- N'invente RIEN — uniquement ce qui est explicitement dit dans la conversation

CATÉGORIES DISPONIBLES :
- entraînement : volume, fréquence, type de séances, zones
- blessure : douleurs, blessures passées ou actuelles, limitations
- objectif : courses prévues, objectifs de performance, deadlines
- préférence : ce que l'athlète aime ou n'aime pas
- nutrition : habitudes alimentaires, hydratation, suppléments
- historique : passé sportif, anciennes performances
- équipement : matériel utilisé (vélo, capteurs, chaussures...)
- récupération : sommeil, étirements, gestion de la fatigue
- autre : tout ce qui ne rentre pas ailleurs

IMPORTANCE (0.1 à 1.0) :
- 1.0 : critique (blessure active, objectif de course important, FTP/VDOT)
- 0.7 : important (routine d'entraînement, préférence forte)
- 0.4 : informatif (contexte général, petit détail)
- 0.1 : mineur (anecdote sans impact coaching)

Réponds UNIQUEMENT avec un tableau JSON de faits, sans autre texte :
[
  {"fact": "...", "category": "...", "importance": 0.X},
  ...
]
"""


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            timeout=30.0,
        )
    return _client


def extract_facts_from_messages(messages: list[dict]) -> list[dict]:
    """
    Extract structured facts from a batch of chat messages.
    
    Args:
        messages: list of dicts with 'role' and 'content' keys
    
    Returns:
        list of dicts with {fact, category, importance}
    """
    if not messages:
        return []
    
    # Build conversation text
    conversation = "\n".join(
        [f"[{m.get('role', 'unknown')}] {m.get('content', '')}" for m in messages]
    )
    
    raw = ""
    try:
        client = _get_client()
        response = client.chat.completions.create(
            model=EXTRACTOR_MODEL,
            messages=[
                {"role": "system", "content": EXTRACTION_PROMPT},
                {"role": "user", "content": f"Extrais les faits de cette conversation :\n\n{conversation[:3000]}"},
            ],
            max_tokens=EXTRACTOR_MAX_TOKENS,
            temperature=0.3,
        )
        
        content = response.choices[0].message.content
        if content is None:
            logger.warning("fact_extraction_empty_response")
            return []
        raw = content.strip()
        
        # Extract JSON from the response (handle markdown code blocks)
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        
        facts = json.loads(raw)
        
        # Validate
        valid_facts = []
        for f in facts:
            if not isinstance(f, dict):
                continue
            fact_text = f.get("fact", "").strip()
            category = f.get("category", "autre").strip().lower()
            importance = float(f.get("importance", 0.5))
            
            if not fact_text or len(fact_text) < 5:
                continue
            if category not in FACT_CATEGORIES:
                category = "autre"
            importance = max(0.1, min(1.0, importance))
            
            valid_facts.append({
                "fact": fact_text[:200],
                "category": category,
                "importance": importance,
            })
        
        logger.info(
            "facts_extracted: input_messages=%s extracted_count=%s",
            len(messages),
            len(valid_facts),
        )
        return valid_facts
    
    except json.JSONDecodeError as e:
        logger.warning("fact_extraction_json_error: error=%s raw=%s", str(e), raw[:200])
        return []
    except Exception as e:
        logger.error("fact_extraction_failed: error=%s", str(e))
        return []
