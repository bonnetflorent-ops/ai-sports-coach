import pytest
from unittest.mock import MagicMock, patch
from src.engine.fact_extractor import extract_facts_from_messages


def test_extract_facts_empty_messages():
    """Empty message list should return empty facts."""
    result = extract_facts_from_messages([])
    assert result == []


def test_extract_facts_valid_json():
    """Valid JSON response should be parsed correctly."""
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content='[{"fact": "Test fact", "category": "entraînement", "importance": 0.8}]'))
    ]

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    messages = [{"role": "user", "content": "Je cours 3 fois par semaine"}]

    with patch("src.engine.fact_extractor._get_client", return_value=mock_client):
        facts = extract_facts_from_messages(messages)

    assert len(facts) == 1
    assert facts[0]["fact"] == "Test fact"
    assert facts[0]["category"] == "entraînement"
    assert facts[0]["importance"] == 0.8


def test_extract_facts_cleans_markdown_json():
    """JSON wrapped in markdown code blocks should be cleaned."""
    raw_json = '```json\n[{"fact": "Clean", "category": "blessure", "importance": 1.0}]\n```'
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content=raw_json))
    ]

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    messages = [{"role": "user", "content": "J'ai mal au genou"}]

    with patch("src.engine.fact_extractor._get_client", return_value=mock_client):
        facts = extract_facts_from_messages(messages)

    assert len(facts) == 1
    assert facts[0]["fact"] == "Clean"


def test_extract_facts_api_error_returns_empty():
    """API errors should return empty list (graceful degradation)."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = Exception("API error")

    messages = [{"role": "user", "content": "Test"}]

    with patch("src.engine.fact_extractor._get_client", return_value=mock_client):
        facts = extract_facts_from_messages(messages)

    assert facts == []


def test_extract_facts_validates_fields():
    """Invalid fields should be cleaned/normalized."""
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content='[\n    {"fact": "Valid", "category": "entraînement", "importance": 0.7},\n    {"fact": "", "category": "test", "importance": 0.5},\n    {"fact": "Overcapped", "category": "invalid", "importance": 5.0}\n]'))
    ]

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    messages = [{"role": "user", "content": "Test"}]

    with patch("src.engine.fact_extractor._get_client", return_value=mock_client):
        facts = extract_facts_from_messages(messages)

    assert len(facts) == 2  # Empty fact skipped
    assert facts[0]["fact"] == "Valid"
    assert facts[1]["fact"] == "Overcapped"
    assert facts[1]["category"] == "autre"  # Normalized
    assert facts[1]["importance"] == 1.0  # Capped
