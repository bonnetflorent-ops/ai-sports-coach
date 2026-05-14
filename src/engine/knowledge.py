# -*- coding: utf-8 -*-
"""
Chargeur de la base de connaissances.
Parse index.yaml, lit les fichiers markdown, extrait les concepts par niveau.
"""

import re
from pathlib import Path
from typing import Optional
import yaml


# Résolu relativement au module
KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent.parent / "knowledge"
INDEX_PATH = KNOWLEDGE_DIR / "index.yaml"
DOMAINS_DIR = KNOWLEDGE_DIR / "domains"

_index_cache: Optional[dict] = None
_files_cache: dict[str, str] = {}  # chemin → contenu complet


def _load_index() -> dict:
    """Charge l'index YAML (avec cache)."""
    global _index_cache
    if _index_cache is None:
        with open(INDEX_PATH) as f:
            _index_cache = yaml.safe_load(f)
    return _index_cache


def _read_file(filepath: str) -> str:
    """Lit un fichier markdown (avec cache)."""
    path = str(DOMAINS_DIR / filepath)
    if path not in _files_cache:
        with open(path) as f:
            _files_cache[path] = f.read()
    return _files_cache[path]


def load_concept(concept_id: str, level: int) -> str:
    """
    Charge le contenu d'un concept pour un niveau donné.

    Exemple: load_concept("physiologie/systemes-energetiques", 2)
    Retourne le markdown de la Couche 2 uniquement.
    """
    index = _load_index()
    domain_id, concept_slug = concept_id.split("/", 1)

    # Trouver le domaine et le concept dans l'index
    domain = index["domains"].get(domain_id)
    if not domain:
        return f"[Concept introuvable: {concept_id}]"

    concept = None
    for c in domain["concepts"]:
        if c["id"] == concept_id:
            concept = c
            break
    if not concept:
        return f"[Concept introuvable: {concept_id}]"

    # Lire le fichier source
    file_content = _read_file(domain["file"])

    # Extraire les lignes pour le niveau demandé
    layer_key = f"layer{level}"
    lines_spec = concept.get("lines", {}).get(layer_key)
    if not lines_spec:
        return f"[Niveau {level} non disponible pour {concept_id}]"

    return _extract_lines(file_content, lines_spec)


def _extract_lines(content: str, lines_spec: str) -> str:
    """
    Extrait une plage de lignes d'un contenu markdown.
    lines_spec au format "5-14" ou "5-14" (peut avoir des sauts de ligne
    entre les couches — on lit jusqu'au prochain #### ou ###).
    """
    match = re.match(r"(\d+)-(\d+)", lines_spec)
    if not match:
        return content

    start = int(match.group(1))
    end = int(match.group(2))

    all_lines = content.split("\n")

    # On prend les lignes start-end (1-indexed dans le YAML)
    # Puis on étend jusqu'au prochain header de même niveau si le contenu
    # déborde (certaines couches peuvent être plus longues que prévu)
    result = []
    for i in range(start - 1, min(end, len(all_lines))):
        result.append(all_lines[i])

    # Vérifier si les lignes suivantes appartiennent encore à cette couche
    # (pas de nouveau #### ou ###)
    for i in range(end, len(all_lines)):
        line = all_lines[i].strip()
        if line.startswith("#### ") or line.startswith("### "):
            break
        if line.startswith("## ") or line.startswith("# "):
            break
        if line == "---":
            break
        result.append(all_lines[i])

    return "\n".join(result)


def get_all_concepts_for_selector() -> list[dict]:
    """
    Retourne tous les concepts sous forme simplifiée pour le prompt du sélecteur.
    """
    index = _load_index()
    concepts = []

    for domain_id, domain in index["domains"].items():
        for c in domain["concepts"]:
            concepts.append({
                "id": c["id"],
                "name": c["name"],
                "domain": domain["name"],
                "keywords": c.get("keywords", []),
                "triggers": c.get("triggers", []),
                "priority": c.get("priority", "normal"),
            })

    return concepts


def get_intent_rules() -> list[dict]:
    """Retourne les règles d'intention pour le fallback."""
    index = _load_index()
    return index.get("intent_rules", {})


def get_selector_config() -> dict:
    """Retourne la configuration du sélecteur."""
    index = _load_index()
    return index.get("selector_config", {})


def get_concept_by_id(concept_id: str) -> Optional[dict]:
    """Retourne les métadonnées d'un concept."""
    index = _load_index()
    domain_id, concept_slug = concept_id.split("/", 1)

    domain = index["domains"].get(domain_id)
    if not domain:
        return None

    for c in domain["concepts"]:
        if c["id"] == concept_id:
            return {
                **c,
                "domain_name": domain["name"],
                "domain_file": domain["file"],
            }
    return None
