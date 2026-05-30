"""Tests for _fix_markdown_entities() — Telegram markdown entity balancing."""

from src.bot.handlers.chat import _fix_markdown_entities


# ── Already-balanced: no-op ──────────────────────────────────────

def test_already_balanced_bold():
    assert _fix_markdown_entities("Hello **world** here") == "Hello **world** here"


def test_already_balanced_italic():
    assert _fix_markdown_entities("Hello *world* here") == "Hello *world* here"


def test_already_balanced_underline():
    assert _fix_markdown_entities("Hello __world__ here") == "Hello __world__ here"


def test_already_balanced_strikethrough():
    assert _fix_markdown_entities("Hello ~~world~~ here") == "Hello ~~world~~ here"


def test_already_balanced_spoiler():
    assert _fix_markdown_entities("Hello ||world|| here") == "Hello ||world|| here"


def test_already_balanced_code():
    assert _fix_markdown_entities("Hello `world` here") == "Hello `world` here"


def test_already_balanced_mixed():
    text = "**bold** and *italic* and `code` and __underline__"
    assert _fix_markdown_entities(text) == text


# ── Missing closing: appends missing entity(ies) ─────────────────

def test_missing_close_bold():
    assert _fix_markdown_entities("**Bold text not closed") == "**Bold text not closed**"


def test_missing_close_italic():
    assert _fix_markdown_entities("*Italic text not closed") == "*Italic text not closed*"


def test_missing_close_underline():
    assert _fix_markdown_entities("__Underline not closed") == "__Underline not closed__"


def test_missing_close_strikethrough():
    assert _fix_markdown_entities("~~Strike not closed") == "~~Strike not closed~~"


def test_missing_close_spoiler():
    assert _fix_markdown_entities("||Spoiler not closed") == "||Spoiler not closed||"


def test_missing_close_code():
    assert _fix_markdown_entities("`Code not closed") == "`Code not closed`"


# ── Multiple missing closes ──────────────────────────────────────

def test_missing_close_nested():
    text = "**bold *italic still bold"
    fixed = _fix_markdown_entities(text)
    assert fixed == "**bold *italic still bold***"


def test_missing_close_both():
    text = "**bold and *italic"
    fixed = _fix_markdown_entities(text)
    assert fixed == "**bold and *italic***"


# ── Missing opening (stray close): no change ─────────────────────

def test_stray_close_ignored():
    # A lone close marker is not an error by itself — Telegram accepts it
    text = "hello world** what"
    # The "**" doesn't have a matching open — but we can't know it was meant to close
    # so we leave it or open a new one. Opening a new one is safer than deleting.
    fixed = _fix_markdown_entities(text)
    # The lone ** is treated as an opener → closed at end
    assert fixed == "hello world** what**"


# ── Nested entities (* inside **) ────────────────────────────────

def test_nested_italic_in_bold():
    text = "**bold *italic inside* then more bold**"
    assert _fix_markdown_entities(text) == text


def test_nested_italic_in_underline():
    text = "__underline *italic inside* then more__"
    assert _fix_markdown_entities(text) == text


# ── Triple markers (*** ___**) ───────────────────────────────────

def test_triple_asterisk_balanced():
    text = "***bold italic***"
    # Should parse as ** + * ... * + ** (nested bold+italic)
    fixed = _fix_markdown_entities(text)
    # Check it's balanced: count of ** is even, count of * is even, *** at end is fine
    assert fixed.count("**") % 2 == 0
    assert fixed.count("*") % 2 == 0
    # The actual output may vary but must be balanced
    # Expected: ***bold italic*** → ** * bold italic * **  (balanced)


def test_triple_underscore_balanced():
    text = "___underline italic___"
    fixed = _fix_markdown_entities(text)
    assert fixed.count("__") % 2 == 0
    assert fixed.count("_") % 2 == 0


# ── Edge cases ───────────────────────────────────────────────────

def test_no_entities():
    assert _fix_markdown_entities("Plain text, no markup.") == "Plain text, no markup."


def test_empty_string():
    assert _fix_markdown_entities("") == ""


def test_escaped_entities_ignored():
    text = r"Escaped \*star\* and \*\*double\*\*"
    assert _fix_markdown_entities(text) == text


def test_real_llm_output_broken_bold():
    # Simulated LLM output: a single ** opens but is never closed
    text = "**Avec tes 73kg et ta FTP de 260W (3.6W/kg), ta zone endurance est à 145-170W"
    fixed = _fix_markdown_entities(text)
    assert fixed.count("**") % 2 == 0
    assert fixed == "**Avec tes 73kg et ta FTP de 260W (3.6W/kg), ta zone endurance est à 145-170W**"


def test_multiple_missing_closes_real():
    text = "**Point 1** sur le sujet\n**Point 2 qui n'est pas fermé\n*Point 3 en italique aussi pas fermé\n**Point 4"
    fixed = _fix_markdown_entities(text)
    assert fixed.count("**") % 2 == 0
    assert fixed.count("*") % 2 == 0


# ── Regression: already-correct real outputs pass through ────────

def test_regression_full_coach_message():
    text = (
        "Salut Florent ! 👋\n\n"
        "Voici ton **récap hebdo** :\n\n"
        "- *Endurance* : 2 sorties Zone 2 validées ✅\n"
        "- *Renforcement* : séance full-body faite 💪\n"
        "- ~~Sortie annulée~~ → reportée à demain\n\n"
        "Continue comme ça !"
    )
    assert _fix_markdown_entities(text) == text
