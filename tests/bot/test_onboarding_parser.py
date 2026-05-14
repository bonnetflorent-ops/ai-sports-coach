"""Tests for _parse_onboarding function."""
import pytest
from src.bot.handlers.chat import _parse_onboarding


class TestParseOnboarding:
    """Tests for onboarding message parser."""

    def test_complete_cyclist_intermediate(self):
        """Complete cyclist intermediate with all fields."""
        text = (
            "Florent\n"
            "cyclisme\n"
            "intermédiaire\n"
            "Objectif: préparer une course de 100km\n"
            "3 créneaux par semaine\n"
            "Blessure: non, aucune blessure"
        )
        result = _parse_onboarding(text, "FallbackName")

        assert result["name"] == "Florent"
        assert result["sport"] == "cyclisme"
        assert result["level"] == 2
        assert result["experience"] == "intermédiaire"
        assert result["goal"] is not None
        assert "course" in result["goal"].lower()
        assert result["blessures"] == "Aucune"

    def test_runner_beginner(self):
        """Runner beginner."""
        text = (
            "1. Alice\n"
            "2. running\n"
            "3. débutant\n"
            "Objectif: courir un 10km\n"
            "2 soirs par semaine\n"
            "Blessures: RAS"
        )
        result = _parse_onboarding(text, "Fallback")

        assert result["name"] == "Alice"
        assert result["sport"] == "running"
        assert result["level"] == 1
        assert result["experience"] == "débutant"
        assert result["blessures"] == "Aucune"

    def test_triathlete_expert(self):
        """Triathlete expert."""
        text = (
            "1. Marc\n"
            "2. triathlon\n"
            "3. expert\n"
            "4. Ironman dans 6 mois\n"
            "5. 10 créneaux/semaine\n"
            "6. tendinite au genou droit en rémission"
        )
        result = _parse_onboarding(text, "Fallback")

        assert result["name"] == "Marc"
        assert result["sport"] == "triathlon"
        assert result["level"] == 3
        assert result["experience"] == "expert"
        assert result["blessures"] is not None
        assert "Aucune" not in result["blessures"]  # not "no injury"

    def test_velo_maps_to_cyclisme(self):
        """'vélo' maps to 'cyclisme'."""
        text = "1. Sophie\n2. vélo\n3. intermédiaire\n4. sorties longues\n5. 3 fois\n6. non"
        result = _parse_onboarding(text, "Fallback")
        assert result["sport"] == "cyclisme"

    def test_musculation_maps_to_fitness(self):
        """'musculation' maps to 'fitness'."""
        text = "1. Paul\n2. musculation\n3. débutant\n4. prise de masse\n5. 4 fois\n6. rien"
        result = _parse_onboarding(text, "Fallback")
        assert result["sport"] == "fitness"

    def test_no_injury_variants(self):
        """Various 'no injury' answers all map to 'Aucune'."""
        variants = [
            "non",
            "aucune",
            "pas de blessure",
            "RAS",
            "rien",
        ]
        for answer in variants:
            text = (
                f"1. Test\n"
                f"2. cyclisme\n"
                f"3. intermédiaire\n"
                f"Objectif: objectif\n"
                f"Souple\n"
                f"Blessures: {answer}"
            )
            result = _parse_onboarding(text, "Fallback")
            assert result["blessures"] == "Aucune", f"Failed for: '{answer}'"

    def test_response_without_explicit_numbering(self):
        """Response without explicit numbering — first line is name."""
        text = (
            "Florent\n"
            "cyclisme intermédiaire\n"
            "préparer l'Étape du Tour\n"
            "3 créneaux par semaine\n"
            "pas de blessure"
        )
        result = _parse_onboarding(text, "TelegramName")

        assert result["name"] == "Florent"
        assert result["sport"] == "cyclisme"
        assert result["level"] == 2

    def test_advanced_expert_confirme_all_level_3(self):
        """'avancé', 'expert', 'confirmé' all map to level 3."""
        for level_word in ["avancé", "expert", "confirmé"]:
            text = (
                f"1. Jean\n"
                f"2. cyclisme\n"
                f"3. {level_word}\n"
                f"4. objectif\n"
                f"5. flexible\n"
                f"6. non"
            )
            result = _parse_onboarding(text, "Fallback")
            assert result["level"] == 3, f"Failed for: '{level_word}'"
            assert result["experience"] == "expert", f"Failed for: '{level_word}'"
