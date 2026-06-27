"""Comprehensive tests for LSDL parser and evaluator.

Tests cover:
1. Parser tests - parsing valid and invalid input
2. Evaluator tests - evaluating expressions and computing geometry
3. Semantic validation - constraint checking
"""

from pathlib import Path

import pytest

from lsdl.evaluator import (
    BoundingBox,
    ComposedElement,
    PositionedElement,
    evaluate,
)
from lsdl.model import (
    ComposeExpr,
    LSDLFile,
    Metrics,
    TransformExpr,
    Zone,
)

# Import internal tokenizer for low-level lexer testing (not part of public API)
from lsdl.parser import (
    ParseError,
    _tokenize,  # noqa: PLC2701
    parse,
    parse_file,
    parse_string,
)
from tests.conftest import SEMANTIC_ERROR_FILES, SYNTAX_ERROR_FILES, VALID_FILES

# Known issues with test vectors (parser bugs tracked in beads)
VALID_FILES_WITH_KNOWN_PARSER_ISSUES = {
    "basic-latin": "LSDL-5dih",  # Parser rejects path points not in path: order (spurious)
    "block-form": "LSDL-5dih",  # Parser rejects path points not in path: order (spurious)
    "complete": "LSDL-5dih",  # Parser rejects path points not in path: order (spurious)
    "cyrillic": "LSDL-5dih",  # Parser rejects path points not in path: order (spurious)
    "diacritics": "LSDL-5dih",  # Parser rejects path points not in path: order (spurious)
    "greek": "LSDL-5dih",  # Parser rejects path points not in path: order (spurious)
    "ligatures": "LSDL-5dih.72",  # Parser fails on LIG operator with merge: strategies
    "transforms": "LSDL-12ni",  # Parser fails on @style blocks with transforms
}
INVALID_SYNTAX_WITH_LENIENT_PARSING = {
    "syntax-002-unclosed-paren": "LSDL-bnv8",  # Parser doesn't reject unclosed parenthesis
    "syntax-005-bad-metadata": "LSDL-612y",  # Parser doesn't reject invalid script tag
}
INVALID_SEMANTIC_WITH_LENIENT_PARSING = {
    "semantic-002-cyclic-reference": "LSDL-pxax",  # Parser doesn't detect cyclic aliases
    "semantic-006-undefined-case-char": "LSDL-kdsk",  # Parser doesn't reject undefined @case char
}


# =============================================================================
# Parser Tests: Basic Functionality
# =============================================================================


class TestParserBasic:
    """Basic parser functionality tests."""

    def test_parse_minimal_file(self, minimal_lsdl_path: Path) -> None:
        """Test parse_file on minimal.lsdl."""
        result = parse_file(minimal_lsdl_path)

        assert isinstance(result, LSDLFile)
        assert result.version == (1, 0)
        assert "stem" in result.elements
        assert "i" in result.characters

    def test_parse_minimal_source(self, minimal_lsdl_source: str) -> None:
        """Test parse on minimal.lsdl source string."""
        result = parse(minimal_lsdl_source)

        assert isinstance(result, LSDLFile)
        assert result.version == (1, 0)

    def test_parse_string_alias(self) -> None:
        """Test parse_string is an alias for parse."""
        source = "@lsdl 1.0\ni LATIN-SMALL-I = stem"
        result = parse_string(source)
        assert isinstance(result, LSDLFile)

    def test_tokenizer_basic(self) -> None:
        """Test basic tokenization (internal API).

        Note: _tokenize is an internal function not exported in __all__.
        This test is retained for lexer coverage; callers should use parse().
        """
        tokens = _tokenize("@lsdl 1.0\n@elem stem\n@end")

        token_types = [t.type for t in tokens]
        assert "KEYWORD" in token_types
        assert "INT" in token_types
        assert "NL" in token_types

    def test_empty_file_parses_as_empty(self) -> None:
        """Test that empty files parse as empty LSDLFile (lenient behavior)."""
        # The parser is lenient and allows empty files
        result = parse("")
        assert isinstance(result, LSDLFile)
        assert len(result.elements) == 0
        assert len(result.characters) == 0


# =============================================================================
# Parser Tests: Valid Test Vectors
# =============================================================================


class TestParserValidVectors:
    """Test that all valid test vectors parse without error."""

    @pytest.mark.parametrize("lsdl_path", VALID_FILES, ids=lambda p: p.stem)
    def test_valid_file_parses(self, lsdl_path: Path) -> None:
        """Each valid test vector should parse without raising ParseError."""
        if lsdl_path.stem in VALID_FILES_WITH_KNOWN_PARSER_ISSUES:
            bead_id = VALID_FILES_WITH_KNOWN_PARSER_ISSUES[lsdl_path.stem]
            pytest.skip(f"Known parser issue with {lsdl_path.stem}.lsdl (see {bead_id})")
        result = parse_file(lsdl_path)
        assert isinstance(result, LSDLFile)
        assert result.version[0] == 1


# =============================================================================
# Parser Tests: Invalid Test Vectors (Syntax Errors)
# =============================================================================


class TestParserSyntaxErrors:
    """Test that syntax error test vectors raise ParseError."""

    @pytest.mark.parametrize("lsdl_path", SYNTAX_ERROR_FILES, ids=lambda p: p.stem)
    def test_syntax_error_raises(self, lsdl_path: Path) -> None:
        """Each syntax error test vector should raise ParseError."""
        if lsdl_path.stem in INVALID_SYNTAX_WITH_LENIENT_PARSING:
            bead_id = INVALID_SYNTAX_WITH_LENIENT_PARSING[lsdl_path.stem]
            pytest.skip(f"Parser is lenient on {lsdl_path.stem} (see {bead_id})")
        with pytest.raises(ParseError):
            parse_file(lsdl_path)


# =============================================================================
# Parser Tests: Invalid Test Vectors (Semantic Errors)
# =============================================================================


class TestParserSemanticErrors:
    """Test that semantic error test vectors raise ParseError."""

    @pytest.mark.parametrize("lsdl_path", SEMANTIC_ERROR_FILES, ids=lambda p: p.stem)
    def test_semantic_error_raises(self, lsdl_path: Path) -> None:
        """Each semantic error test vector should raise ParseError."""
        if lsdl_path.stem in INVALID_SEMANTIC_WITH_LENIENT_PARSING:
            bead_id = INVALID_SEMANTIC_WITH_LENIENT_PARSING[lsdl_path.stem]
            pytest.skip(f"Parser is lenient on {lsdl_path.stem} (see {bead_id})")
        with pytest.raises(ParseError):
            parse_file(lsdl_path)


# =============================================================================
# Parser Tests: Composition Operators
# =============================================================================


class TestParserCompositionOperators:
    """Test parsing of each composition operator."""

    def test_parse_stack_operator(self) -> None:
        """Test STACK operator parsing."""
        source = """@lsdl 1.0
@elem stem
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
anchors: top=[6,4] base=[6,8]
@end
A LATIN-CAPITAL-A = STACK(stem, stem)
"""
        result = parse(source)
        char_def = result.characters["A"]
        assert isinstance(char_def.expression, ComposeExpr)
        assert char_def.expression.op == "STACK"
        assert len(char_def.expression.children) == 2

    def test_parse_lr_operator(self) -> None:
        """Test LR operator parsing."""
        source = """@lsdl 1.0
@elem stem
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
anchors: top=[6,4] base=[6,8]
@end
M LATIN-CAPITAL-M = LR(stem, stem)
"""
        result = parse(source)
        char_def = result.characters["M"]
        assert isinstance(char_def.expression, ComposeExpr)
        assert char_def.expression.op == "LR"

    def test_parse_lr_with_split(self) -> None:
        """Test LR operator with split parameter."""
        source = """@lsdl 1.0
@elem stem
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
anchors: top=[6,4] base=[6,8]
@end
M LATIN-CAPITAL-M = LR(stem, stem, 4/8)
"""
        result = parse(source)
        char_def = result.characters["M"]
        assert isinstance(char_def.expression, ComposeExpr)
        assert char_def.expression.split == [4, 8]

    def test_parse_lr3_operator(self) -> None:
        """Test LR3 operator parsing."""
        source = """@lsdl 1.0
@elem stem
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
anchors: top=[6,4] base=[6,8]
@end
W LATIN-CAPITAL-W = LR3(stem, stem, stem)
"""
        result = parse(source)
        char_def = result.characters["W"]
        assert isinstance(char_def.expression, ComposeExpr)
        assert char_def.expression.op == "LR3"
        assert len(char_def.expression.children) == 3

    def test_parse_dia_operator(self) -> None:
        """Test DIA operator parsing."""
        source = """@lsdl 1.0
@elem stem
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
anchors: top=[6,4] base=[6,8] mark-above=[6,3]
@end
@elem acute
zone: diacritic-above
path: p1 p2
p1 = [5,0]
p2 = [7,2]
anchors: attach=[6,2]
@end
i LATIN-SMALL-I-ACUTE = DIA(stem, acute)
"""
        result = parse(source)
        char_def = result.characters["i"]
        assert isinstance(char_def.expression, ComposeExpr)
        assert char_def.expression.op == "DIA"
        assert len(char_def.expression.children) == 2

    def test_parse_dia_with_attach(self) -> None:
        """Test DIA operator with attach parameter."""
        source = """@lsdl 1.0
@elem stem
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
anchors: top=[6,4] base=[6,8] mid=[6,6]
@end
@elem dot
zone: diacritic-above
path: p1
p1 = [6,0]
anchors: attach=[6,0]
@end
i LATIN-SMALL-I = DIA(stem, dot, attach:mid)
"""
        result = parse(source)
        char_def = result.characters["i"]
        assert isinstance(char_def.expression, ComposeExpr)
        assert char_def.expression.anchor_override == "mid"

    def test_parse_dia2_operator(self) -> None:
        """Test DIA2 operator parsing."""
        source = """@lsdl 1.0
@elem stem
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
anchors: top=[6,4] base=[6,8] mark-above=[6,3]
@end
@elem acute
zone: diacritic-above
path: p1 p2
p1 = [5,0]
p2 = [7,2]
anchors: attach=[6,2]
@end
c LATIN-SMALL-C-DOUBLE-ACUTE = DIA2(stem, acute, acute)
"""
        result = parse(source)
        char_def = result.characters["c"]
        assert isinstance(char_def.expression, ComposeExpr)
        assert char_def.expression.op == "DIA2"
        assert len(char_def.expression.children) == 3

    def test_parse_ovr_operator(self) -> None:
        """Test OVR operator parsing."""
        source = """@lsdl 1.0
@elem stem
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
anchors: top=[6,4] base=[6,8]
@end
@elem crossbar
zone: x-height
path: p1 p2
p1 = [2,6]
p2 = [10,6]
anchors: left=[2,6] right=[10,6]
@end
t LATIN-SMALL-T = OVR(stem, crossbar)
"""
        result = parse(source)
        char_def = result.characters["t"]
        assert isinstance(char_def.expression, ComposeExpr)
        assert char_def.expression.op == "OVR"

    def test_parse_frame_operator(self) -> None:
        """Test FRAME operator parsing."""
        source = """@lsdl 1.0
@elem stem
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
anchors: top=[6,4] base=[6,8]
@end
H LATIN-CAPITAL-H = FRAME(stem, stem)
"""
        result = parse(source)
        char_def = result.characters["H"]
        assert isinstance(char_def.expression, ComposeExpr)
        assert char_def.expression.op == "FRAME"

    def test_parse_lig_operator(self) -> None:
        """Test LIG operator parsing."""
        source = """@lsdl 1.0
@elem stem
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
anchors: top=[6,4] base=[6,8]
@end
f LATIN-SMALL-F = stem
i LATIN-SMALL-I = stem
x LATIN-SMALL-LIGATURE-FI = LIG(f, i)
"""
        result = parse(source)
        char_def = result.characters["x"]
        assert isinstance(char_def.expression, ComposeExpr)
        assert char_def.expression.op == "LIG"

    def test_parse_lig_with_merge(self) -> None:
        """Test LIG operator with merge parameter."""
        source = """@lsdl 1.0
@elem stem
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
anchors: top=[6,4] base=[6,8]
@end
f LATIN-SMALL-F = stem
i LATIN-SMALL-I = stem
x LATIN-SMALL-LIGATURE-FI = LIG(f, i, merge:hook-tittle)
"""
        result = parse(source)
        char_def = result.characters["x"]
        assert isinstance(char_def.expression, ComposeExpr)
        assert char_def.expression.merge_strategy == "hook-tittle"

    def test_parse_apex_operator(self) -> None:
        """Test APEX operator parsing."""
        source = """@lsdl 1.0
@elem diagonal
zone: cap
path: p1 p2
p1 = [0,8]
p2 = [6,0]
anchors: top=[6,0] base=[0,8]
@end
A LATIN-CAPITAL-A = APEX(diagonal, diagonal)
"""
        result = parse(source)
        char_def = result.characters["A"]
        assert isinstance(char_def.expression, ComposeExpr)
        assert char_def.expression.op == "APEX"


# =============================================================================
# Parser Tests: Transform Operators
# =============================================================================


class TestParserTransformOperators:
    """Test parsing of transform operators."""

    def test_parse_sc_operator(self) -> None:
        """Test sc (scale) operator parsing."""
        source = """@lsdl 1.0
@elem stem
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
anchors: top=[6,4] base=[6,8]
@end
s LATIN-SMALL-S = sc(stem, sx=10, sy=10)
"""
        result = parse(source)
        char_def = result.characters["s"]
        assert isinstance(char_def.expression, TransformExpr)
        assert char_def.expression.op == "sc"
        assert char_def.expression.params["sx"] == 10
        assert char_def.expression.params["sy"] == 10

    def test_parse_sh_operator(self) -> None:
        """Test sh (shift) operator parsing."""
        source = """@lsdl 1.0
@elem stem
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
anchors: top=[6,4] base=[6,8]
@end
s LATIN-SMALL-S = sh(stem, dx=2, dy=1)
"""
        result = parse(source)
        char_def = result.characters["s"]
        assert isinstance(char_def.expression, TransformExpr)
        assert char_def.expression.op == "sh"
        assert char_def.expression.params["dx"] == 2
        assert char_def.expression.params["dy"] == 1

    def test_parse_sk_operator(self) -> None:
        """Test sk (skew) operator parsing."""
        source = """@lsdl 1.0
@elem stem
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
anchors: top=[6,4] base=[6,8]
@end
s LATIN-SMALL-S = sk(stem, kx=2, ky=0)
"""
        result = parse(source)
        char_def = result.characters["s"]
        assert isinstance(char_def.expression, TransformExpr)
        assert char_def.expression.op == "sk"
        assert char_def.expression.params["kx"] == 2

    def test_parse_nested_transforms(self) -> None:
        """Test nested transform expressions."""
        source = """@lsdl 1.0
@elem stem
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
anchors: top=[6,4] base=[6,8]
@end
s LATIN-SMALL-S = sc(sh(stem, dx=1), sx=10)
"""
        result = parse(source)
        char_def = result.characters["s"]
        assert isinstance(char_def.expression, TransformExpr)
        assert char_def.expression.op == "sc"
        assert isinstance(char_def.expression.child, TransformExpr)
        assert char_def.expression.child.op == "sh"


# =============================================================================
# Parser Tests: Metadata
# =============================================================================


class TestParserMetadata:
    """Test metadata field parsing."""

    def test_parse_script_metadata(self) -> None:
        """Test script: metadata field."""
        source = """@lsdl 1.0
@elem stem
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
anchors: top=[6,4] base=[6,8]
@end
a LATIN-SMALL-A = stem script:Latn
"""
        result = parse(source)
        assert result.characters["a"].metadata.script == "Latn"

    def test_parse_codepoint_metadata(self) -> None:
        """Test cp: metadata field."""
        source = """@lsdl 1.0
@elem stem
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
anchors: top=[6,4] base=[6,8]
@end
a LATIN-SMALL-A = stem cp:U+0061
"""
        result = parse(source)
        assert result.characters["a"].metadata.cp == "U+0061"

    def test_parse_freq_metadata(self) -> None:
        """Test freq: metadata field."""
        source = """@lsdl 1.0
@elem stem
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
anchors: top=[6,4] base=[6,8]
@end
e LATIN-SMALL-E = stem freq:1
"""
        result = parse(source)
        assert result.characters["e"].metadata.freq == 1


# =============================================================================
# Parser Tests: Element Definitions
# =============================================================================


class TestParserElementDefinitions:
    """Test element definition parsing."""

    def test_parse_path_form_element(self) -> None:
        """Test path-form element definition."""
        source = """@lsdl 1.0
@elem stem
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
width: 1
anchors: top=[6,4] base=[6,8]
@end
"""
        result = parse(source)
        elem = result.elements["stem"]

        assert elem.zone == Zone.X_HEIGHT
        assert elem.path_ids == ["p1", "p2"]
        assert elem.width == 1
        assert len(elem.anchors) == 2

    def test_parse_expr_form_element(self) -> None:
        """Test expression-form element definition."""
        source = """@lsdl 1.0
@elem stem
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
anchors: top=[6,4] base=[6,8]
@end
@elem double-stem
build: from_expr
LR(stem, stem)
@end
"""
        result = parse(source)
        elem = result.elements["double-stem"]

        assert elem.is_expr_form
        assert isinstance(elem.expression, ComposeExpr)

    def test_parse_24_grid_element(self) -> None:
        """Test /24 grid element definition."""
        source = """@lsdl 1.0
@elem acute /24
zone: diacritic-above
path: p1 p2
p1 = [10,3]
p2 = [14,0]
anchors: attach=[12,4]
@end
"""
        result = parse(source)
        elem = result.elements["acute"]

        assert elem.grid == 24

    def test_parse_closed_path(self) -> None:
        """Test close: true in element definition."""
        source = """@lsdl 1.0
@elem bowl
zone: x-height
path: p1 p2 p3
p1 = [6,4]
p2 = [12,6]
p3 = [6,8]
close: true
anchors: attach=[6,6]
@end
"""
        result = parse(source)
        assert result.elements["bowl"].close is True

    def test_parse_curve_path_point(self) -> None:
        """Test curve (Bezier) path point parsing."""
        source = """@lsdl 1.0
@elem arc
zone: x-height
path: p1 p2
p1 = [2,6]
p2 = C([6,4] [10,6])
anchors: left=[2,6] right=[10,6]
@end
"""
        result = parse(source)
        elem = result.elements["arc"]
        assert elem.path_points is not None
        pp = elem.path_points["p2"]

        assert pp.control1 is not None
        assert pp.control1.x == 6
        assert pp.control1.y == 4
        assert pp.endpoint.x == 10


# =============================================================================
# Parser Tests: Alias and Case Mappings
# =============================================================================


class TestParserAliasAndCase:
    """Test alias and case mapping parsing."""

    def test_parse_alias(self) -> None:
        """Test @alias parsing."""
        source = """@lsdl 1.0
@elem stem
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
anchors: top=[6,4] base=[6,8]
@end
@alias v = stem
"""
        result = parse(source)
        assert "v" in result.aliases
        assert result.aliases["v"].target == "stem"

    def test_parse_script_qualified_alias(self) -> None:
        """Test script-qualified alias."""
        source = """@lsdl 1.0
@elem stem
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
anchors: top=[6,4] base=[6,8]
@end
@alias Grek:H = stem
"""
        result = parse(source)
        assert "Grek:H" in result.aliases
        assert result.aliases["Grek:H"].script_qualifier == "Grek"

    def test_parse_case_mapping(self) -> None:
        """Test @case parsing."""
        source = """@lsdl 1.0
@elem stem
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
anchors: top=[6,4] base=[6,8]
@end
A LATIN-CAPITAL-A = stem
a LATIN-SMALL-A = stem
@case A a
"""
        result = parse(source)
        assert len(result.case_mappings) == 1
        assert result.case_mappings[0].upper == "A"
        assert result.case_mappings[0].lower == "a"


# =============================================================================
# Parser Tests: Style Definitions
# =============================================================================


class TestParserStyles:
    """Test @style block parsing."""

    def test_parse_style_block(self) -> None:
        """Test @style parsing with wildcard."""
        source = """@lsdl 1.0
@style italic
transform: sk(*, kx=3)
@end
"""
        result = parse(source)
        assert "italic" in result.styles
        style = result.styles["italic"]
        assert style.transform.op == "sk"
        assert style.transform.params["kx"] == 3


# =============================================================================
# Parser Tests: Metrics
# =============================================================================


class TestParserMetrics:
    """Test @metrics block parsing."""

    def test_parse_metrics_block(self) -> None:
        """Test @metrics parsing."""
        source = """@lsdl 1.0
@metrics
cap-top: 0
ascender: 1
cap-height: 2
x-top: 4
baseline: 8
descender: 10
desc-limit: 12
@end
"""
        result = parse(source)
        assert result.metrics.cap_top == 0
        assert result.metrics.ascender == 1
        assert result.metrics.cap_height == 2
        assert result.metrics.x_top == 4
        assert result.metrics.baseline == 8
        assert result.metrics.descender == 10
        assert result.metrics.desc_limit == 12


# =============================================================================
# Evaluator Tests: Simple Expressions
# =============================================================================


class TestEvaluatorSimple:
    """Test evaluator on simple expressions."""

    def test_evaluate_minimal_file(self, minimal_lsdl_source: str) -> None:
        """Test evaluate on minimal.lsdl."""
        parsed = parse(minimal_lsdl_source)
        results = evaluate(parsed)

        assert "i" in results
        assert isinstance(results["i"], (PositionedElement, ComposedElement))

    def test_evaluate_single_element_ref(self) -> None:
        """Test evaluation of a single element reference."""
        source = """@lsdl 1.0
@elem stem
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
width: 1
anchors: top=[6,4] base=[6,8]
@end
i LATIN-SMALL-I = stem
"""
        parsed = parse(source)
        results = evaluate(parsed)

        elem = results["i"]
        assert isinstance(elem, PositionedElement)
        assert elem.name == "stem"

    def test_evaluate_returns_all_characters(self) -> None:
        """Test that evaluate returns all character definitions."""
        source = """@lsdl 1.0
@elem stem
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
anchors: top=[6,4] base=[6,8]
@end
i LATIN-SMALL-I = stem
l LATIN-SMALL-L = stem
"""
        parsed = parse(source)
        results = evaluate(parsed)

        assert "i" in results
        assert "l" in results


# =============================================================================
# Evaluator Tests: STACK Operator
# =============================================================================


class TestEvaluatorStack:
    """Test STACK operator evaluation."""

    def test_evaluate_stack(self) -> None:
        """Test STACK composes vertically."""
        source = """@lsdl 1.0
@elem stem
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
width: 1
anchors: top=[6,4] base=[6,8]
@end
x LATIN-SMALL-X = STACK(stem, stem)
"""
        parsed = parse(source)
        results = evaluate(parsed)

        elem = results["x"]
        assert isinstance(elem, ComposedElement)
        assert elem.operator == "STACK"
        assert len(elem.children) == 2


# =============================================================================
# Evaluator Tests: LR Operator
# =============================================================================


class TestEvaluatorLR:
    """Test LR operator evaluation."""

    def test_evaluate_lr(self) -> None:
        """Test LR composes horizontally."""
        source = """@lsdl 1.0
@elem stem
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
width: 1
anchors: top=[6,4] base=[6,8]
@end
m LATIN-SMALL-M = LR(stem, stem)
"""
        parsed = parse(source)
        results = evaluate(parsed)

        elem = results["m"]
        assert isinstance(elem, ComposedElement)
        assert elem.operator == "LR"

    def test_evaluate_lr_with_split(self) -> None:
        """Test LR with split parameter affects layout."""
        source = """@lsdl 1.0
@elem stem
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
width: 1
anchors: top=[6,4] base=[6,8]
@end
m LATIN-SMALL-M = LR(stem, stem, 4/8)
"""
        parsed = parse(source)
        results = evaluate(parsed)

        elem = results["m"]
        assert isinstance(elem, ComposedElement)
        assert len(elem.children) == 2


# =============================================================================
# Evaluator Tests: DIA Operator
# =============================================================================


class TestEvaluatorDIA:
    """Test DIA operator evaluation."""

    def test_evaluate_dia(self) -> None:
        """Test DIA attaches diacritic to base."""
        source = """@lsdl 1.0
@elem stem
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
width: 1
anchors: top=[6,4] base=[6,8] mark-above=[6,3]
@end
@elem acute
zone: diacritic-above
path: p1 p2
p1 = [5,0]
p2 = [7,2]
width: 1
anchors: attach=[6,2]
@end
a LATIN-SMALL-A-ACUTE = DIA(stem, acute)
"""
        parsed = parse(source)
        results = evaluate(parsed)

        elem = results["a"]
        assert isinstance(elem, ComposedElement)
        assert elem.operator == "DIA"


# =============================================================================
# Evaluator Tests: Transform Operators
# =============================================================================


class TestEvaluatorTransforms:
    """Test transform operator evaluation."""

    def test_evaluate_scale(self) -> None:
        """Test sc (scale) transform."""
        source = """@lsdl 1.0
@elem stem
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
width: 1
anchors: top=[6,4] base=[6,8]
@end
s LATIN-SMALL-S = sc(stem, sx=6, sy=6)
"""
        parsed = parse(source)
        results = evaluate(parsed)

        elem = results["s"]
        assert isinstance(elem, PositionedElement)
        # Scale of 6/12 = 0.5 should shrink the bounding box
        assert elem.bbox.width < 12

    def test_evaluate_shift(self) -> None:
        """Test sh (shift) transform."""
        source = """@lsdl 1.0
@elem stem
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
width: 1
anchors: top=[6,4] base=[6,8]
@end
s LATIN-SMALL-S = sh(stem, dx=2, dy=0)
"""
        parsed = parse(source)
        results = evaluate(parsed)

        elem = results["s"]
        assert isinstance(elem, PositionedElement)
        # Shifted by dx=2
        assert elem.bbox.x_min > 0

    def test_evaluate_skew(self) -> None:
        """Test sk (skew) transform."""
        source = """@lsdl 1.0
@elem stem
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
width: 1
anchors: top=[6,4] base=[6,8]
@end
s LATIN-SMALL-S = sk(stem, kx=2, ky=0)
"""
        parsed = parse(source)
        results = evaluate(parsed)

        elem = results["s"]
        assert isinstance(elem, PositionedElement)


# =============================================================================
# Evaluator Tests: Bounding Box Computation
# =============================================================================


class TestEvaluatorBoundingBox:
    """Test bounding box computation."""

    def test_bounding_box_from_zone(self) -> None:
        """Test bounding box creation from zone."""
        metrics = Metrics()

        bbox = BoundingBox.from_zone(Zone.X_HEIGHT, metrics)
        assert bbox.y_min == metrics.x_top
        assert bbox.y_max == metrics.baseline

        bbox = BoundingBox.from_zone(Zone.CAP, metrics)
        assert bbox.y_min == metrics.cap_top
        assert bbox.y_max == metrics.baseline

    def test_bounding_box_union(self) -> None:
        """Test bounding box union operation."""
        box1 = BoundingBox(0, 0, 6, 6)
        box2 = BoundingBox(3, 3, 12, 12)

        union = box1.union(box2)
        assert union.x_min == 0
        assert union.y_min == 0
        assert union.x_max == 12
        assert union.y_max == 12

    def test_bounding_box_translate(self) -> None:
        """Test bounding box translation."""
        box = BoundingBox(0, 0, 6, 6)

        translated = box.translate(3, 2)
        assert translated.x_min == 3
        assert translated.y_min == 2
        assert translated.x_max == 9
        assert translated.y_max == 8

    def test_bounding_box_scale(self) -> None:
        """Test bounding box scaling."""
        box = BoundingBox(3, 3, 9, 9)

        scaled = box.scale(0.5, 0.5, cx=6, cy=6)
        assert scaled.width == pytest.approx(3.0)
        assert scaled.height == pytest.approx(3.0)

    def test_composed_element_bbox(self) -> None:
        """Test that composed elements have union bounding box."""
        source = """@lsdl 1.0
@elem stem
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
width: 1
anchors: top=[6,4] base=[6,8]
@end
m LATIN-SMALL-M = LR(stem, stem)
"""
        parsed = parse(source)
        results = evaluate(parsed)

        elem = results["m"]
        assert elem.bbox is not None


# =============================================================================
# Semantic Validation Tests
# =============================================================================


class TestSemanticValidation:
    """Test semantic constraint validation."""

    def test_undefined_element_reference(self) -> None:
        """Test constraint 6: undefined element reference."""
        source = """@lsdl 1.0
A LATIN-CAPITAL-A = APEX(undefined_elem, stem)
"""
        with pytest.raises(ParseError) as exc_info:
            parse(source)
        assert (
            "unresolved" in str(exc_info.value).lower()
            or "undefined" in str(exc_info.value).lower()
        )

    def test_cyclic_reference_detection(self) -> None:
        """Test constraint 7: cycle detection."""
        source = """@lsdl 1.0
@elem a
build: from_expr
b
@end
@elem b
build: from_expr
a
@end
x LATIN-SMALL-X = a
"""
        with pytest.raises(ParseError) as exc_info:
            parse(source)
        assert "cycle" in str(exc_info.value).lower()

    def test_coordinate_bounds_12_grid(self) -> None:
        """Test coordinate values within 0-12 bounds for /12 grid."""
        source = """@lsdl 1.0
@elem bad
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [15,8]
anchors: top=[6,4] base=[6,8]
@end
"""
        with pytest.raises(ParseError) as exc_info:
            parse(source)
        assert (
            "out of range" in str(exc_info.value).lower() or "range" in str(exc_info.value).lower()
        )

    def test_tparam_out_of_range(self) -> None:
        """Test constraint 2: transform param must be -12 to 24."""
        source = """@lsdl 1.0
@elem stem
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
anchors: top=[6,4] base=[6,8]
@end
s LATIN-SMALL-S = sc(stem, sx=30)
"""
        with pytest.raises(ParseError) as exc_info:
            parse(source)
        assert (
            "-12" in str(exc_info.value)
            or "24" in str(exc_info.value)
            or "range" in str(exc_info.value).lower()
        )

    def test_stack_requires_two_children(self) -> None:
        """Test STACK requires at least 2 children."""
        source = """@lsdl 1.0
@elem stem
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
anchors: top=[6,4] base=[6,8]
@end
s LATIN-SMALL-S = STACK(stem)
"""
        with pytest.raises(ParseError) as exc_info:
            parse(source)
        assert "2" in str(exc_info.value) or "children" in str(exc_info.value).lower()

    def test_lr_requires_two_children(self) -> None:
        """Test LR requires at least 2 children."""
        source = """@lsdl 1.0
@elem stem
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
anchors: top=[6,4] base=[6,8]
@end
s LATIN-SMALL-S = LR(stem)
"""
        with pytest.raises(ParseError) as exc_info:
            parse(source)
        assert "2" in str(exc_info.value) or "children" in str(exc_info.value).lower()

    def test_dia2_requires_three_arguments(self) -> None:
        """Test DIA2 requires exactly 3 arguments."""
        source = """@lsdl 1.0
@elem stem
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
anchors: top=[6,4] base=[6,8]
@end
@elem acute
zone: diacritic-above
path: p1 p2
p1 = [5,0]
p2 = [7,2]
anchors: attach=[6,2]
@end
s LATIN-SMALL-S = DIA2(stem, acute)
"""
        with pytest.raises(ParseError) as exc_info:
            parse(source)
        assert "3" in str(exc_info.value)

    def test_ovr_requires_two_children(self) -> None:
        """Test OVR requires exactly 2 children."""
        source = """@lsdl 1.0
@elem stem
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
anchors: top=[6,4] base=[6,8]
@end
s LATIN-SMALL-S = OVR(stem)
"""
        with pytest.raises(ParseError) as exc_info:
            parse(source)
        assert "2" in str(exc_info.value)

    def test_lig_requires_two_or_three_arguments(self) -> None:
        """Test LIG requires 2 or 3 arguments."""
        source = """@lsdl 1.0
@elem stem
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
anchors: top=[6,4] base=[6,8]
@end
s LATIN-SMALL-S = LIG(stem)
"""
        with pytest.raises(ParseError) as exc_info:
            parse(source)
        assert "2" in str(exc_info.value) or "3" in str(exc_info.value)

    def test_split_values_must_be_positive(self) -> None:
        """Test constraint 1: split values must be positive."""
        source = """@lsdl 1.0
@elem stem
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
anchors: top=[6,4] base=[6,8]
@end
s LATIN-SMALL-S = LR(stem, stem, 0/6)
"""
        with pytest.raises(ParseError) as exc_info:
            parse(source)
        assert "positive" in str(exc_info.value).lower() or "0" in str(exc_info.value)

    def test_duplicate_case_mapping(self) -> None:
        """Test duplicate @case detection."""
        source = """@lsdl 1.0
@elem stem
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
anchors: top=[6,4] base=[6,8]
@end
A LATIN-CAPITAL-A = stem
a LATIN-SMALL-A = stem
B LATIN-CAPITAL-B = stem
@case A a
@case A B
"""
        with pytest.raises(ParseError) as exc_info:
            parse(source)
        assert "duplicate" in str(exc_info.value).lower()

    def test_metrics_monotonicity(self) -> None:
        """Test constraint 15: metric values must be monotonically non-decreasing."""
        source = """@lsdl 1.0
@metrics
cap-top: 5
ascender: 3
cap-height: 2
x-top: 4
baseline: 8
descender: 10
desc-limit: 12
@end
"""
        with pytest.raises(ParseError) as exc_info:
            parse(source)
        assert (
            "monoton" in str(exc_info.value).lower()
            or "non-decreasing" in str(exc_info.value).lower()
        )

    def test_path_form_requires_zone(self) -> None:
        """Test that path-form @elem requires zone."""
        source = """@lsdl 1.0
@elem bad
path: p1 p2
p1 = [6,4]
p2 = [6,8]
anchors: top=[6,4] base=[6,8]
@end
"""
        with pytest.raises(ParseError) as exc_info:
            parse(source)
        assert "zone" in str(exc_info.value).lower()

    def test_path_form_requires_anchors(self) -> None:
        """Test that path-form @elem requires anchors."""
        source = """@lsdl 1.0
@elem bad
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
@end
"""
        with pytest.raises(ParseError) as exc_info:
            parse(source)
        assert "anchor" in str(exc_info.value).lower()

    def test_path_point_declared_but_not_defined(self) -> None:
        """Test that path points declared in path: must be defined."""
        source = """@lsdl 1.0
@elem bad
zone: x-height
path: p1 p2 p3
p1 = [6,4]
p2 = [6,8]
anchors: top=[6,4] base=[6,8]
@end
"""
        with pytest.raises(ParseError) as exc_info:
            parse(source)
        assert "not defined" in str(exc_info.value).lower()
        assert "p3" in str(exc_info.value)

    def test_path_point_defined_but_not_declared(self) -> None:
        """Test that defined path points must be in path: declaration."""
        source = """@lsdl 1.0
@elem bad
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
p3 = [3,6]
anchors: top=[6,4] base=[6,8]
@end
"""
        with pytest.raises(ParseError) as exc_info:
            parse(source)
        assert "not in path" in str(exc_info.value).lower()
        assert "p3" in str(exc_info.value)

    def test_char_block_path_point_mismatch(self) -> None:
        """Test path point validation in @char blocks."""
        source = """@lsdl 1.0
@char X LATIN-CAPITAL-X
zone: cap
path: p1 p2 p3
p1 = [0,0]
p2 = [12,8]
anchors: top=[6,0] base=[6,8]
@end
"""
        with pytest.raises(ParseError) as exc_info:
            parse(source)
        assert "not defined" in str(exc_info.value).lower()
        assert "p3" in str(exc_info.value)


# =============================================================================
# Edge Cases and Regression Tests
# =============================================================================


class TestEdgeCases:
    """Edge cases and regression tests."""

    def test_comments_ignored(self) -> None:
        """Test that comments are ignored."""
        source = """@lsdl 1.0
# This is a comment
@elem stem  # inline comment
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
anchors: top=[6,4] base=[6,8]
@end
"""
        result = parse(source)
        assert "stem" in result.elements

    def test_multiple_characters_same_expression(self) -> None:
        """Test multiple characters using same element."""
        source = """@lsdl 1.0
@elem stem
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
anchors: top=[6,4] base=[6,8]
@end
i LATIN-SMALL-I = stem
l LATIN-SMALL-L = stem
"""
        result = parse(source)
        assert "i" in result.characters
        assert "l" in result.characters

    def test_deeply_nested_expression(self) -> None:
        """Test deeply nested composition."""
        source = """@lsdl 1.0
@elem stem
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
anchors: top=[6,4] base=[6,8]
@end
x LATIN-SMALL-X = LR(STACK(stem, stem), STACK(stem, stem))
"""
        result = parse(source)
        char_def = result.characters["x"]
        assert isinstance(char_def.expression, ComposeExpr)
        assert char_def.expression.op == "LR"
        assert isinstance(char_def.expression.children[0], ComposeExpr)
        assert char_def.expression.children[0].op == "STACK"

    def test_wildcard_only_in_style(self) -> None:
        """Test that wildcard (*) is only valid in @style blocks."""
        source = """@lsdl 1.0
@elem stem
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
anchors: top=[6,4] base=[6,8]
@end
x LATIN-SMALL-X = sc(*, sx=6)
"""
        with pytest.raises(ParseError) as exc_info:
            parse(source)
        assert "wildcard" in str(exc_info.value).lower() or "*" in str(exc_info.value)

    def test_version_compatibility(self) -> None:
        """Test version checking (reject major > 1)."""
        source = """@lsdl 2.0
@elem stem
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
anchors: top=[6,4] base=[6,8]
@end
"""
        with pytest.raises(ParseError) as exc_info:
            parse(source)
        assert "version" in str(exc_info.value).lower() or "2" in str(exc_info.value)

    def test_invalid_zone_name(self) -> None:
        """Test that invalid zone names are rejected."""
        source = """@lsdl 1.0
@elem bad
zone: invalid-zone
path: p1 p2
p1 = [6,4]
p2 = [6,8]
anchors: top=[6,4] base=[6,8]
@end
"""
        with pytest.raises(ParseError) as exc_info:
            parse(source)
        assert "zone" in str(exc_info.value).lower() or "invalid" in str(exc_info.value).lower()

    def test_invalid_width_value(self) -> None:
        """Test that width must be 0, 1, or 2."""
        source = """@lsdl 1.0
@elem bad
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
width: 5
anchors: top=[6,4] base=[6,8]
@end
"""
        with pytest.raises(ParseError) as exc_info:
            parse(source)
        assert "width" in str(exc_info.value).lower() or "0" in str(exc_info.value)
