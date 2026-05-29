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

    def test_name_with_je_m_appelle_prefix(self):
        """"Je m'appelle Florent" → name = Florent."""
        text = (
            "1. Je m'appelle Florent\n"
            "2. vélo\n"
            "3. intermédiaire\n"
            "4. être affûté\n"
            "5. 4 créneaux\n"
            "6. douleur au psoas"
        )
        result = _parse_onboarding(text, "Fallback")
        assert result["name"] == "Florent"

    def test_name_with_je_suis_prefix(self):
        """"Je suis Paul" → name = Paul."""
        text = (
            "1. Je suis Paul\n"
            "2. running\n"
            "3. débutant\n"
            "4. courir un 10km\n"
            "5. 2 créneaux\n"
            "6. non"
        )
        result = _parse_onboarding(text, "Fallback")
        assert result["name"] == "Paul"

    def test_name_with_mon_prenom_cest(self):
        """"Mon prénom c'est Sophie" → name = Sophie."""
        text = (
            "1. Mon prénom c'est Sophie\n"
            "2. fitness\n"
            "3. débutant\n"
            "4. prise de masse\n"
            "5. 3 créneaux\n"
            "6. rien"
        )
        result = _parse_onboarding(text, "Fallback")
        assert result["name"] == "Sophie"

    def test_name_with_moi_cest(self):
        """"Moi c'est Marc" → name = Marc."""
        text = (
            "1. Moi c'est Marc\n"
            "2. triathlon\n"
            "3. expert\n"
            "4. Ironman\n"
            "5. 10 créneaux\n"
            "6. tendinite"
        )
        result = _parse_onboarding(text, "Fallback")
        assert result["name"] == "Marc"

    def test_clean_name_fallback_on_multiline_answer(self):
        """Long answer with name buried in text → still extracts."""
        text = (
            "1. Je m'appelle Florent \n"
            "2. Je fais du vélo de route, du VTT, du home-trainer\n"
            "3. J'ai un niveau intermédiaire\n"
            "4. Mon objectif est d'être affûté pour le vélo\n"
            "5. lundi, mardi, jeudi, vendredi\n"
            "6. douleur au psoas gauche"
        )
        result = _parse_onboarding(text, "Fallback")
        assert result["name"] == "Florent"
        assert result["sport"] == "cyclisme"  # vélo → cyclisme
        assert result["blessures"] is not None
        assert "Aucune" not in result["blessures"]

    def test_goal_and_injury_prefix_stripped(self):
        """Numeric prefixes '4.' and '6.' are stripped from goal and injuries."""
        text = (
            "1. Florent\n"
            "2. cyclisme\n"
            "3. intermédiaire\n"
            "4. Être affûté pour le vélo et avoir un physique athlétique\n"
            "5. 4 créneaux\n"
            "6. douleur au psoas gauche"
        )
        result = _parse_onboarding(text, "Fallback")
        # Goal should NOT start with "4."
        assert not result["goal"].startswith("4"), f"Goal still has prefix: {result['goal']}"
        assert "affûté" in result["goal"]
        # Injuries should NOT start with "6."
        assert not result["blessures"].startswith("6"), f"Injuries still has prefix: {result['blessures']}"
        assert "psoas" in result["blessures"]
