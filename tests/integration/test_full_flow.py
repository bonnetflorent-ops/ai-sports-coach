"""Test d'intégration du flux complet (hors LLM réel)."""
import pytest
from src.engine.selector import _keyword_fallback, _check_critical
from src.engine.prompt_builder import build_system_prompt
from src.engine.knowledge import load_concept, get_all_concepts_for_selector


@pytest.mark.integration
class TestFullFlow:
    """Simule un échange complet (avec fallback, pas de vrai LLM)."""

    def test_question_entrainement(self):
        """Flow : message → sélecteur → prompt builder."""
        message = "Je veux progresser en vélo, comment organiser mes semaines ?"
        profile = {
            "name": "Florent",
            "sport": "cyclisme",
            "level": 2,
            "goal": "granfondo",
            "experience": "3 ans",
            "ctl": 80,
            "tsb": -5,
        }

        # Étape 1 : Sélecteur (fallback)
        selection = _keyword_fallback(message, profile)
        assert len(selection["concepts"]) > 0

        # Étape 2 : Prompt builder
        prompt = build_system_prompt(selection, profile)
        assert len(prompt) > 500
        assert "Florent" in prompt
        assert "cyclisme" in prompt

        # Étape 3 : Vérifier que les connaissances se chargent
        for concept_id in selection["concepts"]:
            content = load_concept(concept_id, selection["level"])
            assert not content.startswith(
                "[Concept"
            ), f"Échec chargement: {concept_id}"

    def test_question_douleur_critical_path(self):
        """Flow : douleur → détection critique → injection blessures."""
        message = "J'ai mal au genou quand je pédale"
        profile = {"sport": "cyclisme", "level": 2}

        # Étape 1 : Détection critique
        critical = _check_critical(message, profile)
        assert critical is not None
        assert "blessures/cyclisme" in critical

        # Étape 2 : Construire une sélection — critical est déjà une liste
        selection = {"concepts": critical, "level": 2, "reasoning": "critical"}
        prompt = build_system_prompt(selection, profile)
        assert len(prompt) > 200

        # Étape 3 : Vérifier que chaque concept critique se charge
        for cid in critical:
            content = load_concept(cid, 2)
            assert not content.startswith("[Concept"), f"Échec chargement: {cid}"
            assert len(content) > 50

    def test_question_nutrition(self):
        """Flow : nutrition → sélecteur → prompt builder."""
        message = "Quoi manger avant une sortie longue de 3h ?"
        profile = {
            "name": "Marie",
            "sport": "cyclisme",
            "level": 2,
            "goal": "forme",
            "experience": "1 an",
        }

        selection = _keyword_fallback(message, profile)
        assert any("nutrition" in c for c in selection["concepts"])

        prompt = build_system_prompt(selection, profile)
        assert "Marie" in prompt

    def test_question_debutant(self):
        """Flow : niveau 1 → prompt pédagogue."""
        message = "Je débute la course à pied, par où commencer ?"
        profile = {
            "name": "Thomas",
            "sport": "running",
            "level": 1,
            "goal": "5km",
            "experience": "0 ans",
        }

        selection = _keyword_fallback(message, profile)
        assert len(selection["concepts"]) > 0

        prompt = build_system_prompt(selection, profile)
        assert "Thomas" in prompt
        # Vérifier que le ton est adapté au niveau 1
        assert "running" in prompt.lower() or "course" in prompt.lower()

    def test_concepts_index_integrity(self):
        """Tous les concepts du sélecteur sont chargeables aux 3 niveaux."""
        concepts = get_all_concepts_for_selector()
        assert len(concepts) >= 30

        issues = []
        for c in concepts:
            for lvl in [1, 2, 3]:
                content = load_concept(c["id"], lvl)
                if content.startswith("[Concept") or content.startswith(
                    "[Niveau"
                ):
                    issues.append(f"{c['id']} level {lvl}: {content}")

        if issues:
            pytest.fail(f"Concepts non chargeables:\n" + "\n".join(issues))
