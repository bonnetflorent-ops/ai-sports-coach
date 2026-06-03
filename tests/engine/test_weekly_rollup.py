"""Tests for weekly_rollup.py."""
import json
import pytest
from src.engine.weekly_rollup import validate_rollup_json, get_week_label
from datetime import date


def test_get_week_label():
    # 2026-06-03 is a Wednesday → belongs to week 23
    label = get_week_label(date(2026, 6, 3))
    assert label == "2026-W23"


def test_validate_valid_rollup():
    rollup = {
        "week": "2026-W22",
        "start_date": "2026-05-26",
        "end_date": "2026-06-01",
        "nb_sessions": 5,
        "total_volume_h": 7.5,
        "summary": "Bonne semaine de reprise.",
        "avg_rpe": 6.2,
        "avg_ctl": 62,
        "avg_tsb": -8,
        "key_metrics": [
            {"name": "FTP estimé", "value": 265, "unit": "W", "trend": "stable"}
        ],
        "injuries_active": [],
        "injuries_resolved": [],
        "goals_progress": "En bonne voie.",
        "coach_notes": "Continuer.",
    }
    assert validate_rollup_json(rollup) is True


def test_validate_missing_fields():
    assert validate_rollup_json({"week": "2026-W22"}) is False


def test_validate_bad_metric():
    rollup = {
        "week": "2026-W22",
        "start_date": "2026-05-26",
        "end_date": "2026-06-01",
        "nb_sessions": 5,
        "total_volume_h": 7.5,
        "summary": "...",
        "avg_rpe": 6.2,
        "avg_ctl": 62,
        "avg_tsb": -8,
        "key_metrics": [{"name": "FTP"}],  # missing value, unit, trend
        "injuries_active": [],
        "injuries_resolved": [],
        "goals_progress": "...",
        "coach_notes": "...",
    }
    assert validate_rollup_json(rollup) is False
