"""Tests for _keyword_fallback and _check_critical functions."""
import pytest
from src.engine.selector import _keyword_fallback, _check_critical


class TestCheckCritical:
    """Tests for critical condition detection."""

    def test_pain_detection_cyclisme(self):
        """Pain detection with 'j'ai mal au genou' + cyclisme profile."""
        result = _check_critical(
            user_message="j'ai mal au genou depuis ma sortie d'hier",
            user_profile={"sport": "cyclisme"},
        )
        assert result is not None
        assert "blessures/cyclisme" in result
        assert "planification/gestion-charge" in result

    def test_no_pain_normal_question(self):
        """No pain detected for normal questions."""
        result = _check_critical(
            user_message="Comment améliorer ma FTP ?",
            user_profile={"sport": "cyclisme"},
        )
        assert result is None

    def test_tendinite_running(self):
        """Tendinite + running profile."""
        result = _check_critical(
            user_message="Je sens une tendinite au tendon d'Achille",
            user_profile={"sport": "running"},
        )
        assert result is not None
        assert "blessures/running" in result

    def test_no_profile_pain_defaults_to_all(self):
        """Pain without specific sport profile returns all injury concepts."""
        result = _check_critical(
            user_message="j'ai mal partout",
            user_profile={},
        )
        assert result is not None
        # Should contain all 3 injury concepts
        assert "blessures/cyclisme" in result
        assert "blessures/running" in result
        assert "blessures/fitness-musculation" in result


class TestKeywordFallback:
    """Tests for keyword-based fallback selector."""

    def test_fatigue_keywords(self):
        """Fatigue keywords → recuperation concepts."""
        result = _keyword_fallback(
            user_message="Je suis fatigué, je récupère pas bien",
            user_profile={"sport": "cyclisme", "level": 2},
        )
        assert result["level"] == 2
        assert len(result["concepts"]) >= 1
        # Should contain recuperation concepts from fatigue_surentrainement rule
        assert any("recuperation" in c for c in result["concepts"])

    def test_nutrition_keywords(self):
        """Nutrition keywords → nutrition concepts."""
        result = _keyword_fallback(
            user_message="Que manger après une sortie longue ? Protéine ou glucide ?",
            user_profile={"sport": "running", "level": 2},
        )
        assert len(result["concepts"]) >= 1
        assert any("nutrition" in c for c in result["concepts"])

    def test_motivation_keywords(self):
        """Motivation keywords → psychologie concepts."""
        result = _keyword_fallback(
            user_message="Je suis démotivé, plus envie de m'entraîner",
            user_profile={"sport": "cyclisme", "level": 1},
        )
        assert len(result["concepts"]) >= 1
        assert any("psychologie" in c for c in result["concepts"])

    def test_unknown_message_ultimate_fallback(self):
        """Unknown message → ultimate fallback with 2 default concepts."""
        result = _keyword_fallback(
            user_message="choisir une selle de vélo confortable",
            user_profile={"sport": "cyclisme", "level": 1},
        )
        assert result["level"] == 1
        assert len(result["concepts"]) == 2
        # Ultimate fallback concepts
        assert "physiologie/systemes-energetiques" in result["concepts"]
        assert "seances/endurance-fondamentale" in result["concepts"]
