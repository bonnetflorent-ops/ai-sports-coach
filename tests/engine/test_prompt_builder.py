"""Tests for build_system_prompt and _clean_footnotes."""
import pytest
from src.engine.prompt_builder import build_system_prompt, _clean_footnotes


class TestCleanFootnotes:
    """Tests for footnote removal."""

    def test_removes_footnote_patterns(self):
        """Removes [^1], [^2] patterns."""
        text = "Le VO2max est une métrique clé[^1] pour l'endurance[^2]."
        result = _clean_footnotes(text)
        assert "[^1]" not in result
        assert "[^2]" not in result
        assert "métrique clé pour l'endurance" in result

    def test_removes_multi_footnotes(self):
        """Removes multi-reference footnotes [^1,2]."""
        text = "Plusieurs études le confirment[^1,2,3]."
        result = _clean_footnotes(text)
        assert "[^1,2,3]" not in result

    def test_text_without_footnotes_unchanged(self):
        """Text without footnotes remains unchanged."""
        text = "La FTP est la puissance maximale soutenable pendant 1 heure."
        result = _clean_footnotes(text)
        assert result == text


class TestBuildSystemPrompt:
    """Tests for system prompt builder."""

    def test_full_prompt_cyclist_intermediate(self):
        """Full prompt for cyclist intermediate."""
        selection = {
            "concepts": [
                "physiologie/systemes-energetiques",
                "planification/gestion-charge",
            ],
            "level": 2,
            "reasoning": "test",
        }
        profile = {
            "name": "Florent",
            "sport": "cyclisme",
            "level": 2,
            "goal": "préparer l'Étape du Tour",
            "experience": "intermédiaire",
            "blessures": "Aucune",
            "ctl": 75,
            "tsb": -5,
        }

        prompt = build_system_prompt(selection, profile)

        # Check key elements
        assert "Florent" in prompt
        assert "cyclisme" in prompt
        assert "préparer l'Étape du Tour" in prompt
        assert "CTL=75" in prompt
        assert "TSB=-5" in prompt
        assert "PERSONNALISATION" in prompt
        assert "Explique chaque sigle technique" in prompt

    def test_beginner_prompt_pedagogue(self):
        """Beginner prompt — check 'pédagogue' is present."""
        selection = {
            "concepts": ["physiologie/systemes-energetiques"],
            "level": 1,
            "reasoning": "test",
        }
        profile = {
            "name": "Alice",
            "sport": "running",
            "level": 1,
            "goal": "courir 10km",
            "experience": "débutant",
        }

        prompt = build_system_prompt(selection, profile)

        assert "encourageant" in prompt
        assert "Débutant" in prompt

    def test_low_tsb_prompt(self):
        """Low TSB prompt (TSB=-25) — check 'privilégie la récupération'."""
        selection = {
            "concepts": ["recuperation/sommeil"],
            "level": 2,
            "reasoning": "test",
        }
        profile = {
            "name": "Jean",
            "sport": "cyclisme",
            "level": 2,
            "goal": "progresser",
            "experience": "intermédiaire",
            "ctl": 80,
            "tsb": -25,
        }

        prompt = build_system_prompt(selection, profile)

        assert "récup prioritaire" in prompt
        assert "TSB=-25" in prompt

    def test_prompt_without_ctl_has_no_tsb_rules(self):
        """Prompt without CTL/TSB should not contain TSB rules."""
        selection = {
            "concepts": ["physiologie/systemes-energetiques"],
            "level": 1,
            "reasoning": "test",
        }
        profile = {
            "name": "Bob",
            "sport": "fitness",
            "level": 1,
            "goal": "prise de masse",
            "experience": "débutant",
        }

        prompt = build_system_prompt(selection, profile)

        # TSB-specific charge rules should NOT be present (but SIGLES TECHNIQUES always lists TSB as acronym)
        assert "privilégie la récupération" not in prompt
        assert "CHARGE ACTUELLE" not in prompt
