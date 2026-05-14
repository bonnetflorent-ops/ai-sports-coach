"""Tests for knowledge loader."""
import pytest
from src.engine.knowledge import (
    load_concept,
    get_all_concepts_for_selector,
    get_concept_by_id,
)


class TestKnowledgeLoader:
    """Tests for knowledge base loading."""

    def test_get_all_concepts_returns_at_least_30(self):
        """get_all_concepts_for_selector() returns >= 30 concepts."""
        concepts = get_all_concepts_for_selector()
        assert len(concepts) >= 30

        # Each concept should have required fields
        for c in concepts:
            assert "id" in c
            assert "name" in c
            assert "domain" in c
            assert "keywords" in c

    def test_load_concept_valid_id_returns_content(self):
        """load_concept with valid ID returns substantial content."""
        content = load_concept("physiologie/systemes-energetiques", 2)

        # Should be substantial (more than 50 chars)
        assert len(content) > 50

        # Should NOT start with error prefix
        assert not content.startswith("[Concept introuvable")
        assert not content.startswith("[Niveau")

    def test_load_concept_beginner_level(self):
        """load_concept beginner level returns valid content."""
        content = load_concept("physiologie/systemes-energetiques", 1)
        assert len(content) > 50
        assert not content.startswith("[")

    def test_load_concept_expert_level(self):
        """load_concept expert level returns valid content."""
        content = load_concept("physiologie/systemes-energetiques", 3)
        assert len(content) > 50
        assert not content.startswith("[")

    def test_load_concept_invalid_id(self):
        """load_concept with invalid ID returns error prefix."""
        content = load_concept("nonexistent/fake-concept", 1)
        assert content.startswith("[Concept introuvable")

    def test_load_concept_invalid_level(self):
        """load_concept with invalid level (99) returns error prefix."""
        content = load_concept("physiologie/systemes-energetiques", 99)
        assert content.startswith("[Niveau")

    def test_get_concept_by_id_returns_metadata(self):
        """get_concept_by_id returns metadata with name and domain_name."""
        meta = get_concept_by_id("physiologie/systemes-energetiques")

        assert meta is not None
        assert "name" in meta
        assert "domain_name" in meta
        assert isinstance(meta["name"], str)
        assert isinstance(meta["domain_name"], str)
        assert len(meta["name"]) > 0
        assert len(meta["domain_name"]) > 0

    def test_get_concept_by_id_invalid(self):
        """get_concept_by_id with invalid ID returns None."""
        meta = get_concept_by_id("nonexistent/fake-concept")
        assert meta is None

    def test_all_7_domains_present(self):
        """All 7 expected domains are present."""
        concepts = get_all_concepts_for_selector()
        domains = set(c["domain"] for c in concepts)

        expected_domains = [
            "Physiologie de l'effort",
            "Planification & périodisation",
            "Séances types par filière énergétique",
            "Récupération & adaptation",
            "Blessures & prévention",
            "Nutrition sportive",
            "Psychologie & mental",
        ]

        for domain in expected_domains:
            assert domain in domains, f"Domain '{domain}' not found"
