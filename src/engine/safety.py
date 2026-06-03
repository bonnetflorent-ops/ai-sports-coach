"""
Safety handler — detects pain/injury messages and returns a structured
three-part response: (1) acknowledge + recommend doctor, (2) adapt plan,
(3) follow-up plan. NEVER provides medical diagnosis.
"""
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

# Keywords that trigger the safety handler
PAIN_KEYWORDS = [
    r'\bdouleur\b', r'\bmal\b', r'\bblessure\b', r'\bblessé\b',
    r'\btendinite\b', r'\bgenou\b', r'\bcheville\b', r'\bdos bloqué\b',
    r'\bélongation\b', r'\bdéchirure\b', r'\bfracture\b', r'\bentorse\b',
    r'\binflammation\b', r'\barthrose\b', r'\bsciatique\b',
    r'\bcontracture\b', r'\bcrampe\b', r'\bclaquage\b',
    r'\bpériostite\b', r'\baponévrosite\b', r'\bfasciite\b',
]

# Phrases NEVER to use
FORBIDDEN_PATTERNS = [
    r"c'est (une|un) \w+",       # "c'est une tendinite" — diagnostic
    r"tu as (une|un) \w+",        # "tu as une tendinite"
    r"diagnostic",                 # never use this word
    r"prends? (des? )?\w+",       # "prends des anti-inflammatoires"
    r"médicament",                 # never suggest medication
]


def is_safety_trigger(message: str) -> bool:
    """Returns True if the message contains pain/injury keywords."""
    msg_lower = message.lower()
    return any(re.search(kw, msg_lower) for kw in PAIN_KEYWORDS)


def get_safety_response(sport: str = "") -> dict:
    """
    Returns the structured safety response injected into the system prompt.
    The LLM uses this to frame its response, not a hardcoded message.
    """
    return {
        "triggered": True,
        "rules": [
            "ÉTAPE 1 — TOUJOURS : 'Ça peut être plusieurs choses. Consulte un médecin du sport pour un diagnostic précis.'",
            "ÉTAPE 2 — TOUJOURS : 'En attendant, voici comment j'adapte ton programme.'",
            "ÉTAPE 3 — ADAPTATION CONCRÈTE : remplacer l'activité à risque, réduire volume/intensité, ajouter renforcement, donner un seuil de douleur pour arrêter.",
            "ÉTAPE 4 — SUIVI : 'Je note cette adaptation. On en reparle à ta prochaine séance.'",
        ],
        "forbidden": [
            "NE JAMAIS faire de diagnostic médical",
            "NE JAMAIS suggérer de médicament",
            "NE JAMAIS dire 'continue normalement'",
            "NE JAMAIS ignorer la douleur",
        ],
    }


def check_for_forbidden_content(text: str) -> list[str]:
    """Scans response text for forbidden patterns. Returns list of violations."""
    violations = []
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            violations.append(f"Forbidden pattern matched: {pattern}")
    return violations


SAFETY_SYSTEM_INJECTION = """
RÈGLES SÉCURITÉ ABSOLUES :
1. Si l'athlète signale une douleur ou une blessure → applique le protocole sécurité en 4 étapes :
   - ÉTAPE 1 : "Ça peut être plusieurs choses. Consulte un médecin du sport."
   - ÉTAPE 2 : "En attendant, voici comment j'adapte ton programme."
   - ÉTAPE 3 : Proposer une adaptation concrète (remplacer, réduire, renforcer)
   - ÉTAPE 4 : Programmer un suivi ("Je note, on vérifie dans X jours.")
2. JAMAIS de diagnostic médical. JAMAIS.
3. JAMAIS de conseil médicamenteux. JAMAIS.
4. Si tu ne sais pas → dis-le, propose de chercher ou oriente vers un professionnel.
5. Termine CHAQUE réponse par : "🤖 Je suis une IA, pas un médecin. Consulte un professionnel de santé pour tout problème médical."
"""
