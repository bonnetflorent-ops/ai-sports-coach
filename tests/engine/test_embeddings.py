import pytest
from unittest.mock import MagicMock, patch
from src.engine.embeddings import embed_text, EMBEDDING_DIM


def test_embed_text_returns_768d_vector():
    """embed_text should return a list of 768 floats."""
    mock_response = MagicMock()
    mock_response.data = [MagicMock(embedding=[0.1] * EMBEDDING_DIM)]

    mock_client = MagicMock()
    mock_client.embeddings.create.return_value = mock_response

    with patch("src.engine.embeddings._get_client", return_value=mock_client):
        result = embed_text("test text")

    assert len(result) == EMBEDDING_DIM
    assert all(isinstance(x, float) for x in result)


def test_embed_text_empty_returns_zeros():
    """Empty text should return zero vector without calling API."""
    result = embed_text("")
    assert len(result) == EMBEDDING_DIM
    assert all(x == 0.0 for x in result)


def test_embed_text_api_error_returns_zeros():
    """API errors should return zero vector (graceful degradation)."""
    mock_client = MagicMock()
    mock_client.embeddings.create.side_effect = Exception("API down")

    with patch("src.engine.embeddings._get_client", return_value=mock_client):
        result = embed_text("test")

    assert len(result) == EMBEDDING_DIM
    assert all(x == 0.0 for x in result)
