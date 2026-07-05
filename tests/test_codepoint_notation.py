"""Tests for U+XXXX codepoint notation in character definitions."""

import pytest

from lsdl.parser import ParseError, parse_string


def test_codepoint_block_form():
    """@char U+XXXX NAME block form."""
    src = """@lsdl 1.0
@char U+0041 LATIN-CAPITAL-A
build: from_expr
stem.l
@end
"""
    doc = parse_string(src)
    assert "A" in doc.characters
    assert doc.characters["A"].char == "A"
    assert doc.characters["A"].name == "LATIN-CAPITAL-A"


def test_codepoint_inline_form():
    """U+XXXX NAME = EXPR inline form."""
    src = """@lsdl 1.0
U+2070 SUPERSCRIPT-ZERO = stem.l cp:U+2070
"""
    doc = parse_string(src)
    assert "⁰" in doc.characters
    char_def = doc.characters["⁰"]
    assert char_def.char == "⁰"
    assert char_def.name == "SUPERSCRIPT-ZERO"
    assert char_def.metadata.cp == "U+2070"


def test_codepoint_non_bmp():
    """Codepoints outside BMP (U+10000+)."""
    src = """@lsdl 1.0
U+10400 DESERET-CAPITAL-LONG-I = stem.l cp:U+10400
"""
    doc = parse_string(src)
    assert "\U00010400" in doc.characters
    assert doc.characters["\U00010400"].char == "\U00010400"


def test_mixed_literal_and_codepoint():
    """Mix of literal chars and codepoint notation."""
    src = """@lsdl 1.0
A LATIN-CAPITAL-A = stem.l
U+0042 LATIN-CAPITAL-B = stem.l
"""
    doc = parse_string(src)
    assert "A" in doc.characters
    assert "B" in doc.characters


def test_codepoint_max_valid():
    """U+10FFFF is the maximum valid Unicode codepoint."""
    src = """@lsdl 1.0
U+10FFFF MAX-CODEPOINT = stem.l
"""
    doc = parse_string(src)
    assert "\U0010ffff" in doc.characters


def test_codepoint_exceeds_unicode_max():
    """U+110000 exceeds Unicode maximum, should raise ParseError."""
    src = """@lsdl 1.0
U+110000 INVALID-CODEPOINT = stem.l
"""
    with pytest.raises(ParseError) as exc_info:
        parse_string(src)
    assert "exceeds U+10FFFF" in str(exc_info.value)


def test_codepoint_six_digit_invalid():
    """U+FFFFFF is a 6-digit codepoint that exceeds Unicode max."""
    src = """@lsdl 1.0
U+FFFFFF INVALID-CODEPOINT = stem.l
"""
    with pytest.raises(ParseError) as exc_info:
        parse_string(src)
    assert "exceeds U+10FFFF" in str(exc_info.value)


def test_codepoint_surrogate_rejected():
    """Surrogate codepoints (U+D800-U+DFFF) are invalid Unicode scalars."""
    src = """@lsdl 1.0
U+D800 SURROGATE = stem.l
"""
    with pytest.raises(ParseError) as exc_info:
        parse_string(src)
    assert "surrogate" in str(exc_info.value).lower()


def test_codepoint_null():
    """U+0000 (null) is a valid codepoint."""
    src = """@lsdl 1.0
U+0000 NULL = stem.l
"""
    doc = parse_string(src)
    assert "\x00" in doc.characters
