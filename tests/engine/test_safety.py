"""Tests for safety.py."""
import pytest
from src.engine.safety import (
    is_safety_trigger,
    get_safety_response,
    check_for_forbidden_content,
    SAFETY_SYSTEM_INJECTION,
)


def test_is_safety_trigger_pain():
    assert is_safety_trigger("J'ai une douleur au genou") is True


def test_is_safety_trigger_injury():
    assert is_safety_trigger("Je me suis blessé hier") is True


def test_is_safety_trigger_tendinite():
    assert is_safety_trigger("Je pense avoir une tendinite") is True


def test_is_safety_trigger_normal_message():
    assert is_safety_trigger("Quelle séance aujourd'hui ?") is False


def test_is_safety_trigger_empty():
    assert is_safety_trigger("") is False


def test_get_safety_response():
    resp = get_safety_response("cyclisme")
    assert resp["triggered"] is True
    assert len(resp["rules"]) == 4
    assert len(resp["forbidden"]) == 4
    assert "ÉTAPE 1" in resp["rules"][0]


def test_check_forbidden_content_diagnosis():
    violations = check_for_forbidden_content("C'est une tendinite rotulienne")
    assert len(violations) > 0


def test_check_forbidden_content_clean():
    violations = check_for_forbidden_content("Continue ton entraînement, tu progresses bien !")
    assert len(violations) == 0


def test_safety_injection_not_empty():
    assert len(SAFETY_SYSTEM_INJECTION) > 100
    assert "SÉCURITÉ" in SAFETY_SYSTEM_INJECTION
