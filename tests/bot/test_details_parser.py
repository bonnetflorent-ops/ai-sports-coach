"""Tests for _parse_details function."""
import pytest
from src.bot.handlers.chat import _parse_details


class TestParseDetails:
    """Tests for optional details parser."""

    def test_full_details(self):
        """Full details: weight, height, age, gender, email."""
        text = "78kg 182cm 34 ans homme flotest@gmail.com"
        result = _parse_details(text)

        assert result["weight_kg"] == 78
        assert result["height_cm"] == 182
        assert result["age"] == 34
        assert result["gender"] == "H"
        assert result["email"] == "flotest@gmail.com"

    def test_height_format_french(self):
        """Height format '1,77m' → 177cm."""
        text = "1,77m 70kg 29 ans H"
        result = _parse_details(text)

        assert result["height_cm"] == 177

    def test_height_format_dot(self):
        """Height format '1.77' → 177cm."""
        text = "1.77 70kg 29 ans H"
        result = _parse_details(text)

        assert result["height_cm"] == 177

    def test_refusal_answers(self):
        """Refusal answers return empty dict."""
        refusals = ["non", "plus tard", "non merci", "pas maintenant", ".", "nan"]
        for refusal in refusals:
            result = _parse_details(refusal)
            assert result == {}, f"Expected empty dict for: '{refusal}'"

    def test_email_typo_correction(self):
        """Email typo correction (@gmial.com → @gmail.com)."""
        text = "florent@gmial.com 75kg 180cm"
        result = _parse_details(text)

        assert result["email"] == "florent@gmail.com"

    def test_email_typo_variants(self):
        """Various email typos are corrected."""
        typos = [
            ("test@gmial.com", "test@gmail.com"),
            ("test@gmal.com", "test@gmail.com"),
            ("test@gnail.com", "test@gmail.com"),
            ("test@hotmai.com", "test@hotmail.com"),
            ("test@yaho.com", "test@yahoo.com"),
            ("test@outloo.com", "test@outlook.com"),
        ]
        for original, expected in typos:
            result = _parse_details(f"75kg 180cm {original}")
            assert result["email"] == expected, f"Failed for: {original}"

    def test_invalid_weight_ignored(self):
        """Invalid weight (<30kg or >250kg) is ignored."""
        # Too low
        result = _parse_details("25kg 180cm 30 ans H")
        assert "weight_kg" not in result

        # Borderline: 30 is excluded (strictly > 30)
        result = _parse_details("30kg 180cm 30 ans H")
        assert "weight_kg" not in result

        # Too high: 250 is excluded (strictly < 250)
        result = _parse_details("251kg 180cm 30 ans H")
        assert "weight_kg" not in result

        # Valid weight
        result = _parse_details("75kg 180cm 30 ans H")
        assert result["weight_kg"] == 75

    def test_female_gender_detection(self):
        """Female gender detection via 'F' or 'femme'."""
        # Via 'F'
        result = _parse_details("60kg 165cm 28 ans F test@test.com")
        assert result["gender"] == "F"

        # Via 'femme'
        result = _parse_details("60kg 165cm 28 ans femme test@test.com")
        assert result["gender"] == "F"

        # Via 'féminin'
        result = _parse_details("60kg 165cm 28 ans féminin test@test.com")
        assert result["gender"] == "F"

    def test_only_partial_info(self):
        """Only partial info results in partial dict."""
        result = _parse_details("je pèse 68kg et j'ai 42 ans")
        assert result["weight_kg"] == 68
        assert result["age"] == 42
        assert "height_cm" not in result
        assert "gender" not in result
