import pytest
from src.engine.athlete_model import (
    create_initial_model,
    get_priority_value,
    merge_contradictions,
)


def test_create_initial_model():
    model = create_initial_model()
    assert "physique" in model
    assert "etat_actuel" in model
    assert "blessures" in model
    assert "patterns" in model
    assert "preferences" in model
    assert "objectifs" in model
    assert model["meta"]["version_modele"] == 1


def test_get_priority_value_human_over_measured():
    """corrigé par l'humain > mesuré"""
    existing = {"value": 265, "source": "measured", "date": "2026-05-01"}
    new = {"value": 258, "source": "corrected_by_human", "date": "2026-06-01"}
    result = get_priority_value(existing, new)
    assert result["value"] == 258
    assert result["source"] == "corrected_by_human"


def test_get_priority_value_measured_over_estimated():
    """mesuré > estimé"""
    existing = {"value": 54, "source": "estimated", "date": "2026-05-01"}
    new = {"value": 52, "source": "measured", "date": "2026-06-01"}
    result = get_priority_value(existing, new)
    assert result["value"] == 52
    assert result["source"] == "measured"


def test_get_priority_value_same_source_newer_wins():
    """Même source → le plus récent gagne"""
    existing = {"value": 260, "source": "estimated", "date": "2026-05-01"}
    new = {"value": 265, "source": "estimated", "date": "2026-06-01"}
    result = get_priority_value(existing, new)
    assert result["value"] == 265


def test_merge_contradictions_no_conflict():
    contradictions = []
    merge_contradictions(contradictions, "FTP", 265, "estimated", "2026-06-01")
    assert len(contradictions) == 0
