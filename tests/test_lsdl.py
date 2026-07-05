"""Comprehensive tests for LSDL parser and evaluator.

Tests cover:
1. Parser tests - parsing valid and invalid input
2. Evaluator tests - evaluating expressions and computing geometry
3. Semantic validation - constraint checking
"""

import contextlib
from pathlib import Path

import pytest

from lsdl.evaluator import (
    BoundingBox,
    ComposedElement,
    EvaluationError,
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
VALID_FILES_WITH_KNOWN_PARSER_ISSUES: dict[str, str] = {}
INVALID_SYNTAX_WITH_LENIENT_PARSING: dict[str, str] = {}
INVALID_SEMANTIC_WITH_LENIENT_PARSING: dict[str, str] = {}


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

    def test_lig_requires_exactly_two_children(self) -> None:
        """Test LIG requires exactly 2 expression children."""
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
        err = str(exc_info.value).lower()
        # Error should identify the specific violation
        assert "ascender=3" in err and "cap-top=5" in err and ">=" in err

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

    def test_max_eval_depth_limit(self) -> None:
        """Test that MAX_EVAL_DEPTH limit is enforced during evaluation."""
        # Build deeply nested expression: STACK(STACK(STACK(...)))
        # MAX_EVAL_DEPTH is 100, so 101 levels should trigger the error
        nested = "stem"
        for _ in range(101):
            nested = f"STACK({nested}, stem)"

        source = f"""@lsdl 1.0
@elem stem
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
anchors: top=[6,4] base=[6,8]
@end
x LATIN-SMALL-X = {nested}
"""
        result = parse(source)
        with pytest.raises(EvaluationError) as exc_info:
            evaluate(result)
        assert "depth" in str(exc_info.value).lower() or "deep" in str(exc_info.value).lower()

    def test_max_tokens_limit(self) -> None:
        """Test that MAX_TOKENS limit is enforced during tokenization."""
        import lsdl.parser as parser_module

        original_max = parser_module.MAX_TOKENS
        try:
            # Temporarily lower the limit for testing
            parser_module.MAX_TOKENS = 10
            # Generate source that would produce more than 10 tokens
            source = "@lsdl 1.0\n" + "stem " * 20
            tokens = parser_module._tokenize(source)
            # Verify last token is ERROR with limit message
            assert tokens[-1].type == "ERROR"
            assert "token limit" in tokens[-1].value.lower()
            # Verify token list is truncated
            assert len(tokens) == parser_module.MAX_TOKENS + 1  # 10 tokens + 1 ERROR
        finally:
            parser_module.MAX_TOKENS = original_max

    def test_alias_cycle_at_evaluation_time(self) -> None:
        """Test that alias cycles are detected at evaluation time."""
        from lsdl.model import AliasDefinition, CharacterDefinition, LSDLFile, Metrics, RefExpr

        # Manually construct an LSDLFile with an alias cycle
        # This bypasses parser validation to test the evaluator's safeguard
        lsdl_file = LSDLFile(
            filename="<test>",
            aliases={
                "a": AliasDefinition(name="a", target="b", line=1, col=1),
                "b": AliasDefinition(name="b", target="a", line=2, col=1),  # cycle: a -> b -> a
            },
            characters={
                "x": CharacterDefinition(
                    char="x",
                    name="LATIN-SMALL-X",
                    expression=RefExpr(name="a", line=3, col=1),
                    line=3,
                    col=1,
                ),
            },
            metrics=Metrics(),
        )
        with pytest.raises(EvaluationError) as exc_info:
            evaluate(lsdl_file)
        assert "cycle" in str(exc_info.value).lower()

    def test_validation_types(self) -> None:
        """Test Severity, ValidationIssue, and ValidationError types."""
        from lsdl.validate import Severity, ValidationError, ValidationIssue

        # Test Severity enum values
        assert Severity.ERROR.value == "error"
        assert Severity.WARNING.value == "warning"
        assert Severity.INFO.value == "info"

        # Test ValidationIssue __str__
        issue1 = ValidationIssue(Severity.ERROR, "test message")
        assert str(issue1) == "error: test message"

        issue2 = ValidationIssue(Severity.WARNING, "msg", location="file.lsdl:10")
        assert "warning" in str(issue2)
        assert "file.lsdl:10" in str(issue2)

        issue3 = ValidationIssue(Severity.INFO, "info msg", code="I001")
        assert "[I001]" in str(issue3)

        # Test ValidationError
        issues = [
            ValidationIssue(Severity.ERROR, "error 1"),
            ValidationIssue(Severity.WARNING, "warning 1"),
            ValidationIssue(Severity.ERROR, "error 2"),
        ]
        err = ValidationError(issues)
        assert err.issues == issues
        assert "2 error" in str(err)  # 2 errors

    def test_metrics_as_dict(self) -> None:
        """Test Metrics.as_dict() produces correct hyphen-keyed dictionary."""
        metrics = Metrics(
            cap_top=0,
            ascender=1,
            cap_height=2,
            x_top=4,
            baseline=8,
            descender=10,
            desc_limit=12,
        )
        d = metrics.as_dict()
        assert d["cap-top"] == 0
        assert d["ascender"] == 1
        assert d["cap-height"] == 2
        assert d["x-top"] == 4
        assert d["baseline"] == 8
        assert d["descender"] == 10
        assert d["desc-limit"] == 12
        assert len(d) == 7

    def test_bounding_box_standard_and_center(self) -> None:
        """Test BoundingBox.standard() and center_x/center_y properties."""
        # Test standard() factory
        std = BoundingBox.standard()
        assert std.x_min == 0
        assert std.y_min == 0
        assert std.x_max == 12
        assert std.y_max == 12
        assert std.width == 12
        assert std.height == 12

        # Test center_x/center_y
        assert std.center_x == 6.0
        assert std.center_y == 6.0

        # Test with non-standard box
        box = BoundingBox(x_min=2, y_min=4, x_max=10, y_max=8)
        assert box.center_x == 6.0
        assert box.center_y == 6.0
        assert box.width == 8
        assert box.height == 4

    def test_element_definition_base_name(self) -> None:
        """Test ElementDefinition.base_name strips variant tags."""
        from lsdl.model import ElementDefinition

        # No variant
        elem1 = ElementDefinition(name="stem", line=1, col=1)
        assert elem1.base_name == "stem"

        # Single variant
        elem2 = ElementDefinition(name="stem.left", line=1, col=1)
        assert elem2.base_name == "stem"

        # Multiple variants
        elem3 = ElementDefinition(name="bowl.upper.wide", line=1, col=1)
        assert elem3.base_name == "bowl"

    def test_lsdl_error_formatting(self) -> None:
        """Test LSDLError and subclasses format with line/col/filename."""
        from lsdl.model import LSDLError

        # Test base LSDLError
        err = LSDLError("test message", line=10, col=5, filename="test.lsdl")
        assert err.message == "test message"
        assert err.line == 10
        assert err.col == 5
        assert err.filename == "test.lsdl"
        assert str(err) == "test.lsdl:10:5: test message"

        # Test with defaults
        err2 = LSDLError("no location")
        assert str(err2) == "<string>:0:0: no location"

        # Test EvaluationError (subclass)
        eval_err = EvaluationError("eval failed", line=20, col=3, filename="expr.lsdl")
        assert str(eval_err) == "expr.lsdl:20:3: eval failed"

        # Test ParseError (subclass)
        parse_err = ParseError("parse failed", line=5, col=12, filename="input.lsdl")
        assert str(parse_err) == "input.lsdl:5:12: parse failed"

    def test_bounding_box_skew(self) -> None:
        """Test BoundingBox.skew() method."""
        # Full-grid box with positive x-skew
        box = BoundingBox(0, 0, 12, 12)
        skewed = box.skew(kx=6, ky=0)
        # kx_factor = 0.5, new_x_min = 0 + (0-6)*0.5 = -3
        # new_x_max = 12 + (12-6)*0.5 = 15
        assert skewed.x_min == -3
        assert skewed.x_max == 15
        assert skewed.y_min == 0
        assert skewed.y_max == 12

        # Negative x-skew produces same width bounds
        skewed_neg = box.skew(kx=-6, ky=0)
        assert skewed_neg.x_min == -3
        assert skewed_neg.x_max == 15

        # Y-skew with custom center
        box2 = BoundingBox(2, 2, 10, 10)
        skewed2 = box2.skew(kx=0, ky=6, cx=6, cy=6)
        # ky_factor = 0.5, new_y_min = 2 + (2-6)*0.5 = 2-2 = 0
        # new_y_max = 10 + (10-6)*0.5 = 10+2 = 12
        assert skewed2.y_min == 0
        assert skewed2.y_max == 12
        assert skewed2.x_min == 2
        assert skewed2.x_max == 10

    def test_positioned_path_point_curve_types(self) -> None:
        """Test PositionedPathPoint.is_line/is_quadratic/is_cubic properties."""
        from lsdl.evaluator import PositionedCoordinate, PositionedPathPoint

        pt = PositionedCoordinate(0, 0)
        c1 = PositionedCoordinate(1, 2)
        c2 = PositionedCoordinate(3, 4)

        # Line: no control points
        line = PositionedPathPoint(endpoint=pt)
        assert line.is_line is True
        assert line.is_quadratic is False
        assert line.is_cubic is False

        # Quadratic: only control1
        quad = PositionedPathPoint(endpoint=pt, control1=c1)
        assert quad.is_line is False
        assert quad.is_quadratic is True
        assert quad.is_cubic is False

        # Cubic: both control points
        cubic = PositionedPathPoint(endpoint=pt, control1=c1, control2=c2)
        assert cubic.is_line is False
        assert cubic.is_quadratic is False
        assert cubic.is_cubic is True

    def test_deprecated_aliases(self) -> None:
        """Test deprecated aliases trigger warnings and return correct types."""
        import warnings as w

        import lsdl
        from lsdl.model import CharacterDefinition, ElementDefinition, LSDLFile

        # Test Document -> LSDLFile
        with w.catch_warnings(record=True) as caught:
            w.simplefilter("always")
            alias = lsdl.Document
            assert alias is LSDLFile
            assert len(caught) == 1
            assert issubclass(caught[0].category, DeprecationWarning)
            assert "Document is deprecated" in str(caught[0].message)

        # Test GlyphDef -> CharacterDefinition
        with w.catch_warnings(record=True) as caught:
            w.simplefilter("always")
            alias = lsdl.GlyphDef
            assert alias is CharacterDefinition
            assert len(caught) == 1

        # Test StrokeDef -> ElementDefinition
        with w.catch_warnings(record=True) as caught:
            w.simplefilter("always")
            alias = lsdl.StrokeDef
            assert alias is ElementDefinition
            assert len(caught) == 1

        # Unknown attribute raises AttributeError
        with pytest.raises(AttributeError, match="no attribute"):
            _ = lsdl.NonExistent

    def test_merge_anchors_precedence(self) -> None:
        """Test merge_anchors() gives precedence to earlier elements."""
        from lsdl.evaluator import (
            PositionedAnchor,
            PositionedCoordinate,
            merge_anchors,
        )

        # Create anchors with different positions
        anchor1_top = PositionedAnchor("top", PositionedCoordinate(0, 0))
        anchor1_bottom = PositionedAnchor("bottom", PositionedCoordinate(0, 12))
        anchor2_top = PositionedAnchor(
            "top", PositionedCoordinate(6, 0)
        )  # Same name, different pos

        # Create minimal PositionedElement instances
        elem1 = PositionedElement(
            name="e1",
            path_points=[],
            close=False,
            width=1,
            anchors=[anchor1_top, anchor1_bottom],
            bbox=BoundingBox.standard(),
        )
        elem2 = PositionedElement(
            name="e2",
            path_points=[],
            close=False,
            width=1,
            anchors=[anchor2_top],
            bbox=BoundingBox.standard(),
        )

        merged = merge_anchors([elem1, elem2])

        # Should have 2 anchors: top (from elem1) and bottom
        assert len(merged) == 2
        names = [a.name for a in merged]
        assert "top" in names
        assert "bottom" in names

        # top anchor should have elem1's position (0, 0), not elem2's (6, 0)
        top_anchor = next(a for a in merged if a.name == "top")
        assert top_anchor.position.x == 0

    def test_evaluate_character_no_expr_or_zone(self) -> None:
        """Test evaluate_character errors when neither expression nor zone."""
        from lsdl.evaluator import EvaluationContext, evaluate_character
        from lsdl.model import CharacterDefinition, LSDLFile, Metrics

        # Character with neither expression nor zone
        char_def = CharacterDefinition(
            name="A",
            char="A",
            line=5,
            col=3,
            expression=None,
            zone=None,
        )
        metrics = Metrics()
        file = LSDLFile(
            filename="test.lsdl",
            characters={"A": char_def},
            metrics=metrics,
        )
        ctx = EvaluationContext(file, metrics)

        with pytest.raises(EvaluationError) as exc_info:
            evaluate_character(char_def, ctx)

        assert "has neither expression nor path form" in str(exc_info.value)
        assert exc_info.value.line == 5
        assert exc_info.value.col == 3

    def test_element_get_anchor(self) -> None:
        """Test PositionedElement.get_anchor() and ComposedElement.get_anchor()."""
        from lsdl.evaluator import (
            ComposedElement,
            PositionedAnchor,
            PositionedCoordinate,
        )

        top = PositionedAnchor("top", PositionedCoordinate(6, 0))
        bottom = PositionedAnchor("bottom", PositionedCoordinate(6, 12))

        # PositionedElement
        elem = PositionedElement(
            name="stem",
            path_points=[],
            close=False,
            width=1,
            anchors=[top, bottom],
            bbox=BoundingBox.standard(),
        )
        assert elem.get_anchor("top") is top
        assert elem.get_anchor("bottom") is bottom
        assert elem.get_anchor("nonexistent") is None

        # ComposedElement
        composed = ComposedElement(
            operator="LR", children=[], bbox=BoundingBox.standard(), anchors=[top, bottom]
        )
        assert composed.get_anchor("top") is top
        assert composed.get_anchor("bottom") is bottom
        assert composed.get_anchor("nonexistent") is None

    def test_positioned_coordinate_transforms(self) -> None:
        """Test PositionedCoordinate translate/scale/skew methods."""
        from lsdl.evaluator import PositionedCoordinate

        pt = PositionedCoordinate(3, 4)

        # translate
        t = pt.translate(2, -1)
        assert t.x == 5
        assert t.y == 3

        # scale around default center (6, 6)
        s = pt.scale(2, 2)
        # x: 6 + (3-6)*2 = 6 - 6 = 0
        # y: 6 + (4-6)*2 = 6 - 4 = 2
        assert s.x == 0
        assert s.y == 2

        # skew with x-shear
        sk = pt.skew(kx=12, ky=0)
        # x: 3 + (4-6)*(12/12) = 3 + (-2)*1 = 1
        # y: 4 + (3-6)*(0/12) = 4
        assert sk.x == 1
        assert sk.y == 4

    def test_evaluate_expr_unknown_type(self) -> None:
        """Test evaluate_expr raises on unknown expression type."""
        from typing import cast

        from lsdl.evaluator import EvaluationContext, _evaluate_expr_impl
        from lsdl.model import Expr, LSDLFile, Metrics

        # Create a mock object that isn't a real Expr type
        class FakeExpr:
            line = 42
            col = 7

        fake = cast(Expr, FakeExpr())
        metrics = Metrics()
        file = LSDLFile(filename="test.lsdl", metrics=metrics)
        ctx = EvaluationContext(file, metrics)

        with pytest.raises(EvaluationError) as exc_info:
            _evaluate_expr_impl(fake, ctx)

        assert "Unknown expression type" in str(exc_info.value)
        assert exc_info.value.line == 42
        assert exc_info.value.col == 7

    def test_evaluate_expr_error_expr(self) -> None:
        """Test evaluate_expr raises for ErrorExpr (parse error placeholder)."""
        from lsdl.evaluator import EvaluationContext, evaluate_expr
        from lsdl.model import ErrorExpr, LSDLFile, Metrics

        err = ErrorExpr(message="expected )", line=10, col=15)
        metrics = Metrics()
        file = LSDLFile(filename="test.lsdl", metrics=metrics)
        ctx = EvaluationContext(file, metrics)

        with pytest.raises(EvaluationError) as exc_info:
            evaluate_expr(err, ctx)

        assert "parse error" in str(exc_info.value)
        assert "expected )" in str(exc_info.value)
        assert exc_info.value.line == 10
        assert exc_info.value.col == 15

    def test_evaluation_context_caching(self) -> None:
        """Test EvaluationContext caches element evaluations."""
        from lsdl.evaluator import EvaluationContext, evaluate_element
        from lsdl.model import Coordinate, ElementDefinition, LSDLFile, Metrics, PathPoint, Zone

        # Create element with path form
        elem = ElementDefinition(
            name="stem",
            line=1,
            col=1,
            zone=Zone.CAP,
            path_points=[
                PathPoint(endpoint=Coordinate(6, 0)),
                PathPoint(endpoint=Coordinate(6, 8)),
            ],
        )
        metrics = Metrics()
        file = LSDLFile(filename="test.lsdl", elements={"stem": elem}, metrics=metrics)
        ctx = EvaluationContext(file, metrics)

        # First evaluation
        result1 = evaluate_element(elem, ctx)

        # Second evaluation should return same object (cached)
        result2 = evaluate_element(elem, ctx)

        assert result1 is result2
        assert "stem" in ctx._cache

    def test_get_element_alias_resolution(self) -> None:
        """Test LSDLFile.get_element() resolves aliases and detects cycles."""
        from lsdl.model import AliasDefinition, ElementDefinition, LSDLFile, Metrics

        stem = ElementDefinition(name="stem", line=1, col=1)
        alias_v = AliasDefinition(name="vertical", target="stem", line=2, col=1)
        alias_a = AliasDefinition(name="a", target="b", line=3, col=1)
        alias_b = AliasDefinition(name="b", target="a", line=4, col=1)

        file = LSDLFile(
            filename="test.lsdl",
            elements={"stem": stem},
            aliases={"vertical": alias_v, "a": alias_a, "b": alias_b},
            metrics=Metrics(),
        )

        # Direct element lookup
        assert file.get_element("stem") is stem

        # Alias resolution
        assert file.get_element("vertical") is stem

        # Not found
        assert file.get_element("nonexistent") is None

        # Cycle detection
        with pytest.raises(ValueError, match="Alias cycle"):
            file.get_element("a")

    def test_evaluate_transform_unknown_operator(self) -> None:
        """Test evaluate_transform raises for unknown operator."""
        from lsdl.evaluator import EvaluationContext, evaluate_transform
        from lsdl.model import LSDLFile, Metrics, RefExpr, TransformExpr

        # Unknown transform operator
        expr = TransformExpr(
            op="unknown_op",
            child=RefExpr(name="stem", line=1, col=1),
            params={},
            line=5,
            col=10,
        )
        metrics = Metrics()
        file = LSDLFile(filename="test.lsdl", metrics=metrics)
        ctx = EvaluationContext(file, metrics)

        with pytest.raises(EvaluationError) as exc_info:
            evaluate_transform(expr, ctx)

        assert "Unknown transform operator" in str(exc_info.value)
        assert exc_info.value.line == 5
        assert exc_info.value.col == 10

    def test_evaluate_compose_unknown_operator(self) -> None:
        """Test evaluate_compose raises for unknown operator."""
        from lsdl.evaluator import EvaluationContext, evaluate_compose
        from lsdl.model import ComposeExpr, LSDLFile, Metrics, RefExpr

        # Unknown compose operator
        expr = ComposeExpr(
            op="UNKNOWN_OP",
            children=[RefExpr(name="a", line=1, col=1)],
            line=3,
            col=7,
        )
        metrics = Metrics()
        file = LSDLFile(filename="test.lsdl", metrics=metrics)
        ctx = EvaluationContext(file, metrics)

        with pytest.raises(EvaluationError) as exc_info:
            evaluate_compose(expr, ctx)

        assert "Unknown composition operator" in str(exc_info.value)
        assert exc_info.value.line == 3
        assert exc_info.value.col == 7

    def test_create_placeholder_element_warning(self) -> None:
        """Test create_placeholder_element emits warning."""
        import warnings as w

        from lsdl.evaluator import EvaluationContext, create_placeholder_element
        from lsdl.model import LSDLFile, Metrics

        metrics = Metrics()
        file = LSDLFile(filename="test.lsdl", metrics=metrics)
        ctx = EvaluationContext(file, metrics)

        with w.catch_warnings(record=True) as caught:
            w.simplefilter("always")
            result = create_placeholder_element("missing_element", ctx, line=10, col=5)

            assert len(caught) == 1
            assert "missing_element" in str(caught[0].message)
            assert "10:5" in str(caught[0].message)
            assert issubclass(caught[0].category, UserWarning)

        # Result should be a valid placeholder
        assert result.name == "missing_element"
        assert result.path_points == []

    def test_evaluate_path_form_missing_zone(self) -> None:
        """Test evaluate_path_form raises when zone is None."""
        from lsdl.evaluator import EvaluationContext, evaluate_path_form
        from lsdl.model import ElementDefinition, LSDLFile, Metrics

        elem = ElementDefinition(name="test", line=5, col=3, zone=None)
        metrics = Metrics()
        file = LSDLFile(filename="test.lsdl", metrics=metrics)
        ctx = EvaluationContext(file, metrics)

        with pytest.raises(EvaluationError) as exc_info:
            evaluate_path_form(elem, ctx)

        assert "requires zone" in str(exc_info.value)
        assert exc_info.value.line == 5
        assert exc_info.value.col == 3

    def test_model_str_methods(self) -> None:
        """Test __str__ methods on model dataclasses."""
        from lsdl.model import (
            Anchor,
            ComposeExpr,
            Coordinate,
            ErrorExpr,
            PathPoint,
            RefExpr,
            TransformExpr,
            WildcardExpr,
        )

        # Coordinate
        c = Coordinate(3, 4)
        assert str(c) == "[3,4]"

        # PathPoint - line
        pp_line = PathPoint(endpoint=Coordinate(6, 8))
        assert str(pp_line) == "[6,8]"

        # PathPoint - quadratic
        pp_quad = PathPoint(endpoint=Coordinate(6, 8), control1=Coordinate(4, 5))
        assert "C(" in str(pp_quad)

        # PathPoint - cubic
        pp_cubic = PathPoint(
            endpoint=Coordinate(6, 8), control1=Coordinate(3, 4), control2=Coordinate(5, 6)
        )
        assert "C(" in str(pp_cubic)

        # Anchor
        anchor = Anchor(name="top", position=Coordinate(6, 0))
        assert str(anchor) == "top=[6,0]"

        # RefExpr
        ref = RefExpr(name="stem", line=1, col=1)
        assert str(ref) == "stem"

        # ComposeExpr
        comp = ComposeExpr(op="LR", children=[ref], line=1, col=1)
        assert "LR(" in str(comp)

        # TransformExpr
        trans = TransformExpr(op="sc", child=ref, params={"sx": 6}, line=1, col=1)
        assert "sc(" in str(trans)

        # WildcardExpr
        wild = WildcardExpr(line=1, col=1)
        assert str(wild) == "*"

        # ErrorExpr
        err = ErrorExpr(message="test error", line=1, col=1)
        assert "error" in str(err)

    def test_evaluate_character_path_form(self) -> None:
        """Test evaluate_character with path-form (zone but no expression)."""
        from lsdl.evaluator import EvaluationContext, evaluate_character
        from lsdl.model import CharacterDefinition, Coordinate, LSDLFile, Metrics, PathPoint, Zone

        char_def = CharacterDefinition(
            name="A",
            char="A",
            line=1,
            col=1,
            expression=None,
            zone=Zone.CAP,
            path_points={
                "p1": PathPoint(endpoint=Coordinate(0, 0)),
                "p2": PathPoint(endpoint=Coordinate(6, 8)),
            },
            path_ids=["p1", "p2"],
        )
        metrics = Metrics()
        file = LSDLFile(filename="test.lsdl", characters={"A": char_def}, metrics=metrics)
        ctx = EvaluationContext(file, metrics)

        result = evaluate_character(char_def, ctx)

        assert result.name == "A"
        assert len(result.path_points) == 2

    def test_position_path_point_grid_scaling(self) -> None:
        """Test position_path_point scales for /24 grid."""
        from lsdl.evaluator import position_path_point
        from lsdl.model import Coordinate, PathPoint

        # Default /12 grid: no scaling
        pp12 = PathPoint(endpoint=Coordinate(12, 12))
        result12 = position_path_point(pp12, grid=12)
        assert result12.endpoint.x == 12.0
        assert result12.endpoint.y == 12.0

        # /24 grid: scales by 0.5
        pp24 = PathPoint(endpoint=Coordinate(24, 24))
        result24 = position_path_point(pp24, grid=24)
        assert result24.endpoint.x == 12.0
        assert result24.endpoint.y == 12.0

        # Invalid grid falls back to 12
        pp_invalid = PathPoint(endpoint=Coordinate(12, 12))
        result_invalid = position_path_point(pp_invalid, grid=48)
        assert result_invalid.endpoint.x == 12.0

    def test_skew_element(self) -> None:
        """Test skew_element transforms element coordinates."""
        from lsdl.evaluator import (
            PositionedAnchor,
            PositionedCoordinate,
            PositionedPathPoint,
            skew_element,
        )

        # Create element at center (6,6) - no skew effect
        pt = PositionedCoordinate(6, 6)
        pp = PositionedPathPoint(endpoint=pt)
        anchor = PositionedAnchor("center", pt)
        elem = PositionedElement(
            name="test",
            path_points=[pp],
            close=False,
            width=1,
            anchors=[anchor],
            bbox=BoundingBox.standard(),
        )

        # Skew with kx=12, ky=0 (strong x-skew)
        skewed = skew_element(elem, kx=12, ky=0)

        # Point at center should be unchanged
        assert isinstance(skewed, PositionedElement)
        assert skewed.path_points[0].endpoint.x == 6.0
        assert skewed.path_points[0].endpoint.y == 6.0

    def test_transform_helpers_unknown_type(self) -> None:
        """Test translate/scale/skew_element raise RuntimeError on unknown types."""
        from typing import cast

        from lsdl.evaluator import (
            EvaluatedExpr,
            scale_element,
            skew_element,
            translate_element,
        )

        class FakeElement:
            pass

        fake = cast(EvaluatedExpr, FakeElement())

        with pytest.raises(RuntimeError, match="Cannot translate"):
            translate_element(fake, 1, 1)

        with pytest.raises(RuntimeError, match="Cannot scale"):
            scale_element(fake, 1, 1)

        with pytest.raises(RuntimeError, match="Cannot skew"):
            skew_element(fake, 1, 1)

    def test_transform_composed_element(self) -> None:
        """Test translate/scale_element work with ComposedElement."""
        from lsdl.evaluator import (
            ComposedElement,
            PositionedAnchor,
            PositionedCoordinate,
            PositionedPathPoint,
            scale_element,
            translate_element,
        )

        # Create child element
        pt = PositionedCoordinate(3, 4)
        pp = PositionedPathPoint(endpoint=pt)
        child = PositionedElement(
            name="child",
            path_points=[pp],
            close=False,
            width=1,
            anchors=[],
            bbox=BoundingBox(0, 0, 6, 8),
        )

        # Create composed element
        anchor = PositionedAnchor("test", PositionedCoordinate(3, 4))
        composed = ComposedElement(
            operator="LR", children=[child], bbox=BoundingBox(0, 0, 6, 8), anchors=[anchor]
        )

        # Translate
        translated = translate_element(composed, dx=2, dy=3)
        assert isinstance(translated, ComposedElement)
        assert translated.bbox.x_min == 2
        assert translated.bbox.y_min == 3
        assert translated.anchors[0].position.x == 5

        # Scale (around center 6,6)
        scaled = scale_element(composed, sx=2, sy=2)
        assert isinstance(scaled, ComposedElement)

    def test_evaluate_path_form_missing_path_point(self) -> None:
        """Test evaluate_path_form raises when path_ids reference undefined point."""
        from lsdl.evaluator import EvaluationContext, evaluate_path_form
        from lsdl.model import Coordinate, ElementDefinition, LSDLFile, Metrics, PathPoint, Zone

        # path_ids references point 99 which doesn't exist
        elem = ElementDefinition(
            name="test",
            line=5,
            col=3,
            zone=Zone.CAP,
            path_points={"p1": PathPoint(endpoint=Coordinate(0, 0))},
            path_ids=["p1", "p99"],  # p99 is not defined
        )
        metrics = Metrics()
        file = LSDLFile(filename="test.lsdl", metrics=metrics)
        ctx = EvaluationContext(file, metrics)

        with pytest.raises(EvaluationError) as exc_info:
            evaluate_path_form(elem, ctx)

        assert "p99" in str(exc_info.value)
        assert "not defined" in str(exc_info.value)

    def test_get_anchor_helper(self) -> None:
        """Test get_anchor() helper function."""
        from typing import cast

        from lsdl.evaluator import (
            EvaluatedExpr,
            PositionedAnchor,
            PositionedCoordinate,
            get_anchor,
        )

        anchor = PositionedAnchor("top", PositionedCoordinate(6, 0))
        elem = PositionedElement(
            name="test",
            path_points=[],
            close=False,
            width=1,
            anchors=[anchor],
            bbox=BoundingBox.standard(),
        )

        # Found
        assert get_anchor(elem, "top") is anchor

        # Not found
        assert get_anchor(elem, "bottom") is None

        # Unknown type returns None
        class FakeExpr:
            pass

        assert get_anchor(cast(EvaluatedExpr, FakeExpr()), "top") is None

    def test_evaluate_ovr(self) -> None:
        """Test evaluate_ovr overlays two elements."""
        from lsdl.evaluator import EvaluationContext, evaluate_ovr

        metrics = Metrics()
        file = LSDLFile(filename="test.lsdl", metrics=metrics)
        ctx = EvaluationContext(file, metrics)

        base = PositionedElement(
            name="base",
            path_points=[],
            close=False,
            width=1,
            anchors=[],
            bbox=BoundingBox(0, 0, 12, 12),
        )
        overlay = PositionedElement(
            name="overlay",
            path_points=[],
            close=False,
            width=1,
            anchors=[],
            bbox=BoundingBox(0, 0, 6, 6),
        )

        result = evaluate_ovr([base, overlay], ctx)

        assert result.operator == "OVR"
        assert len(result.children) == 2

        # Test wrong child count
        with pytest.raises(EvaluationError, match="exactly 2"):
            evaluate_ovr([base], ctx)

    def test_evaluate_apex(self) -> None:
        """Test evaluate_apex (alias for FRAME)."""
        from lsdl.evaluator import (
            EvaluationContext,
            PositionedAnchor,
            PositionedCoordinate,
            evaluate_apex,
        )

        metrics = Metrics()
        file = LSDLFile(filename="test.lsdl", metrics=metrics)
        ctx = EvaluationContext(file, metrics)

        # Create elements with anchors for frame alignment
        anchor = PositionedAnchor("apex", PositionedCoordinate(6, 0))
        elem1 = PositionedElement(
            name="diag1",
            path_points=[],
            close=False,
            width=1,
            anchors=[anchor],
            bbox=BoundingBox(0, 0, 6, 8),
        )
        elem2 = PositionedElement(
            name="diag2",
            path_points=[],
            close=False,
            width=1,
            anchors=[anchor],
            bbox=BoundingBox(6, 0, 12, 8),
        )

        result = evaluate_apex([elem1, elem2], ctx)

        assert result.operator == "FRAME"
        assert len(result.children) == 2

    def test_evaluate_lr3(self) -> None:
        """Test LR3 operator (alias for LR with 3+ children)."""
        from lsdl.evaluator import EvaluationContext, evaluate_lr

        metrics = Metrics()
        file = LSDLFile(filename="test.lsdl", metrics=metrics)
        ctx = EvaluationContext(file, metrics)

        # Create elements
        elem1 = PositionedElement(
            name="a",
            path_points=[],
            close=False,
            width=1,
            anchors=[],
            bbox=BoundingBox(0, 0, 4, 12),
        )
        elem2 = PositionedElement(
            name="b",
            path_points=[],
            close=False,
            width=1,
            anchors=[],
            bbox=BoundingBox(0, 0, 4, 12),
        )
        elem3 = PositionedElement(
            name="c",
            path_points=[],
            close=False,
            width=1,
            anchors=[],
            bbox=BoundingBox(0, 0, 4, 12),
        )

        # LR3 uses same evaluate_lr function
        result = evaluate_lr([elem1, elem2, elem3], split=None, ctx=ctx)

        assert result.operator == "LR"
        assert len(result.children) == 3

    def test_evaluate_stack_anchor_alignment(self) -> None:
        """Test evaluate_stack with anchor-based and fallback alignment."""
        from lsdl.evaluator import (
            EvaluationContext,
            PositionedAnchor,
            PositionedCoordinate,
            evaluate_stack,
        )

        metrics = Metrics()
        file = LSDLFile(filename="test.lsdl", metrics=metrics)
        ctx = EvaluationContext(file, metrics)

        # Elements with base/top anchors for anchor-based alignment
        elem1 = PositionedElement(
            name="top",
            path_points=[],
            close=False,
            width=1,
            anchors=[PositionedAnchor("base", PositionedCoordinate(6, 4))],
            bbox=BoundingBox(0, 0, 12, 4),
        )
        elem2 = PositionedElement(
            name="bottom",
            path_points=[],
            close=False,
            width=1,
            anchors=[PositionedAnchor("top", PositionedCoordinate(6, 0))],
            bbox=BoundingBox(0, 0, 12, 4),
        )

        result = evaluate_stack([elem1, elem2], ctx)
        assert result.operator == "STACK"
        assert len(result.children) == 2

        # Fallback: no anchors - stacks by bounding boxes
        elem_no_anchor1 = PositionedElement(
            name="a",
            path_points=[],
            close=False,
            width=1,
            anchors=[],
            bbox=BoundingBox(0, 0, 12, 4),
        )
        elem_no_anchor2 = PositionedElement(
            name="b",
            path_points=[],
            close=False,
            width=1,
            anchors=[],
            bbox=BoundingBox(0, 0, 12, 4),
        )

        result2 = evaluate_stack([elem_no_anchor1, elem_no_anchor2], ctx)
        assert result2.operator == "STACK"

        # Error: less than 2 children
        with pytest.raises(EvaluationError, match="at least 2"):
            evaluate_stack([elem1], ctx)

    def test_evaluate_dia_anchor_fallback(self) -> None:
        """Test evaluate_dia with anchor fallbacks when mark-above/below missing."""
        from lsdl.evaluator import EvaluationContext, evaluate_dia

        metrics = Metrics()
        file = LSDLFile(filename="test.lsdl", metrics=metrics)
        ctx = EvaluationContext(file, metrics)

        # Base without mark anchors (will use fallback)
        base = PositionedElement(
            name="base",
            path_points=[],
            close=False,
            width=1,
            anchors=[],
            bbox=BoundingBox(0, 4, 12, 8),
        )

        # Diacritic above (no attach anchor - uses center fallback)
        mark_above = PositionedElement(
            name="mark",
            path_points=[],
            close=False,
            width=1,
            anchors=[],
            bbox=BoundingBox(4, 0, 8, 3),
        )

        result = evaluate_dia([base, mark_above], anchor_override=None, ctx=ctx)
        assert result.operator == "DIA"
        assert len(result.children) == 2

        # Error: wrong number of children
        with pytest.raises(EvaluationError, match="exactly 2"):
            evaluate_dia([base], anchor_override=None, ctx=ctx)

    def test_evaluate_dia2_mixed_direction(self) -> None:
        """Test evaluate_dia2 with mixed direction (one above, one below)."""
        from lsdl.evaluator import EvaluationContext, evaluate_dia2

        metrics = Metrics()
        file = LSDLFile(filename="test.lsdl", metrics=metrics)
        ctx = EvaluationContext(file, metrics)

        # Base in middle
        base = PositionedElement(
            name="base",
            path_points=[],
            close=False,
            width=1,
            anchors=[],
            bbox=BoundingBox(0, 4, 12, 8),
        )

        # Mark above
        mark1 = PositionedElement(
            name="mark1",
            path_points=[],
            close=False,
            width=1,
            anchors=[],
            bbox=BoundingBox(4, 0, 8, 3),
        )

        # Mark below
        mark2 = PositionedElement(
            name="mark2",
            path_points=[],
            close=False,
            width=1,
            anchors=[],
            bbox=BoundingBox(4, 9, 8, 12),
        )

        result = evaluate_dia2([base, mark1, mark2], ctx)
        assert result.operator == "DIA2"
        assert len(result.children) == 3

        # Error: wrong number of children
        with pytest.raises(EvaluationError, match="exactly 3"):
            evaluate_dia2([base, mark1], ctx)

    def test_evaluate_dia2_zone_based_direction(self) -> None:
        """Test evaluate_dia2 uses zone lookup for direction even after transforms."""
        from lsdl.evaluator import EvaluationContext, evaluate_dia2, is_mark_above
        from lsdl.model import ElementDefinition

        metrics = Metrics()
        # Create element definitions with explicit zones
        acute_def = ElementDefinition(name="acute", line=1, col=1, zone=Zone.DIACRITIC_ABOVE)
        cedilla_def = ElementDefinition(name="cedilla", line=2, col=1, zone=Zone.DIACRITIC_BELOW)
        file = LSDLFile(
            filename="test.lsdl",
            elements={"acute": acute_def, "cedilla": cedilla_def},
            metrics=metrics,
        )
        ctx = EvaluationContext(file, metrics)

        # Create marks with bboxes that would mislead bbox heuristic after transform
        # acute: placed LOW (y=9-12) but zone says above
        mark_above = PositionedElement(
            name="acute",
            path_points=[],
            close=False,
            width=1,
            anchors=[],
            bbox=BoundingBox(4, 9, 8, 12),  # Low position
        )
        # cedilla: placed HIGH (y=0-3) but zone says below
        mark_below = PositionedElement(
            name="cedilla",
            path_points=[],
            close=False,
            width=1,
            anchors=[],
            bbox=BoundingBox(4, 0, 8, 3),  # High position
        )
        # Base in middle
        base = PositionedElement(
            name="base",
            path_points=[],
            close=False,
            width=1,
            anchors=[],
            bbox=BoundingBox(0, 4, 12, 8),  # center_y = 6
        )

        # Test is_mark_above helper directly
        assert is_mark_above(mark_above, ctx) is True  # Zone says above
        assert is_mark_above(mark_below, ctx) is False  # Zone says below
        assert is_mark_above(base, ctx) is None  # No zone info

        # DIA2 should use zone-based direction, not bbox
        result = evaluate_dia2([base, mark_above, mark_below], ctx)
        assert result.operator == "DIA2"
        assert len(result.children) == 3

    def test_is_mark_above_variants_and_characters(self) -> None:
        """Test is_mark_above handles variant names and character zones."""
        from lsdl.evaluator import EvaluationContext, is_mark_above
        from lsdl.model import CharacterDefinition, ElementDefinition

        metrics = Metrics()
        # Base element definition (no variant)
        acute_def = ElementDefinition(name="acute", line=1, col=1, zone=Zone.DIACRITIC_ABOVE)
        # Character with zone (path-form)
        char_mark = CharacterDefinition(
            char="x", name="COMBINING-X", line=2, col=1, zone=Zone.DIACRITIC_BELOW
        )
        file = LSDLFile(
            filename="test.lsdl",
            elements={"acute": acute_def},
            characters={"x": char_mark},
            metrics=metrics,
        )
        ctx = EvaluationContext(file, metrics)

        # Variant name should resolve to base element
        variant_mark = PositionedElement(
            name="acute.heavy",
            path_points=[],
            close=False,
            width=1,
            anchors=[],
            bbox=BoundingBox(4, 9, 8, 12),  # Low position (would be "below" by bbox)
        )
        assert is_mark_above(variant_mark, ctx) is True  # Resolves to 'acute' zone

        # Character zone lookup
        char_elem = PositionedElement(
            name="x",
            path_points=[],
            close=False,
            width=1,
            anchors=[],
            bbox=BoundingBox(4, 0, 8, 3),  # High position (would be "above" by bbox)
        )
        assert is_mark_above(char_elem, ctx) is False  # Character zone says below

        # Unknown element returns None
        unknown = PositionedElement(
            name="unknown",
            path_points=[],
            close=False,
            width=1,
            anchors=[],
            bbox=BoundingBox(0, 0, 12, 12),
        )
        assert is_mark_above(unknown, ctx) is None

    def test_evaluate_frame_anchor_matching(self) -> None:
        """Test evaluate_frame with find_anchor_match."""
        from lsdl.evaluator import (
            EvaluationContext,
            PositionedAnchor,
            PositionedCoordinate,
            evaluate_frame,
            find_anchor_match,
        )

        metrics = Metrics()
        file = LSDLFile(filename="test.lsdl", metrics=metrics)
        ctx = EvaluationContext(file, metrics)

        # Element with right anchor
        elem1 = PositionedElement(
            name="left",
            path_points=[],
            close=False,
            width=1,
            anchors=[PositionedAnchor("right", PositionedCoordinate(6, 4))],
            bbox=BoundingBox(0, 0, 6, 8),
        )

        # Element with left anchor - should match
        elem2 = PositionedElement(
            name="right",
            path_points=[],
            close=False,
            width=1,
            anchors=[PositionedAnchor("left", PositionedCoordinate(0, 4))],
            bbox=BoundingBox(0, 0, 6, 8),
        )

        result = evaluate_frame([elem1, elem2], ctx)
        assert result.operator == "FRAME"
        assert len(result.children) == 2

        # Test find_anchor_match directly
        match = find_anchor_match([elem1], elem2)
        assert match is not None
        assert match[0].name == "right"
        assert match[1].name == "left"

        # No match case
        elem_no_match = PositionedElement(
            name="solo",
            path_points=[],
            close=False,
            width=1,
            anchors=[],
            bbox=BoundingBox(0, 0, 6, 8),
        )
        assert find_anchor_match([elem1], elem_no_match) is None

    def test_evaluate_lig_merge_strategies(self) -> None:
        """Test evaluate_lig with various merge strategies."""
        import warnings as w

        from lsdl.evaluator import EvaluationContext, evaluate_lig

        metrics = Metrics()
        file = LSDLFile(filename="test.lsdl", metrics=metrics)
        ctx = EvaluationContext(file, metrics)

        elem1 = PositionedElement(
            name="a", path_points=[], close=False, width=1, anchors=[], bbox=BoundingBox(0, 0, 6, 8)
        )
        elem2 = PositionedElement(
            name="b", path_points=[], close=False, width=1, anchors=[], bbox=BoundingBox(0, 0, 6, 8)
        )

        # Default/adjacent strategy -> LR
        result = evaluate_lig([elem1, elem2], merge_strategy=None, ctx=ctx)
        assert result.operator == "LR"

        # stem-shared strategy
        result2 = evaluate_lig([elem1, elem2], merge_strategy="stem-shared", ctx=ctx)
        assert result2.operator == "LIG"

        # hook-tittle strategy
        result3 = evaluate_lig([elem1, elem2], merge_strategy="hook-tittle", ctx=ctx)
        assert result3.operator == "LIG"

        # Unknown strategy warns and falls back
        with w.catch_warnings(record=True) as caught:
            w.simplefilter("always")
            result4 = evaluate_lig([elem1, elem2], merge_strategy="unknown", ctx=ctx)
            assert result4.operator == "LR"
            assert len(caught) == 1
            assert "Unknown LIG merge strategy" in str(caught[0].message)

        # Error: wrong number of children
        with pytest.raises(EvaluationError, match="exactly 2"):
            evaluate_lig([elem1], merge_strategy=None, ctx=ctx)

    def test_apply_style(self) -> None:
        """Test apply_style applies transform to expression."""
        from lsdl.evaluator import EvaluationContext, apply_style
        from lsdl.model import (
            Coordinate,
            ElementDefinition,
            PathPoint,
            RefExpr,
            TransformExpr,
            WildcardExpr,
            Zone,
        )

        metrics = Metrics()
        elem = ElementDefinition(
            name="stem",
            line=1,
            col=1,
            zone=Zone.CAP,
            path_points={"p1": PathPoint(endpoint=Coordinate(6, 0))},
            path_ids=["p1"],
        )
        file = LSDLFile(filename="test.lsdl", elements={"stem": elem}, metrics=metrics)
        ctx = EvaluationContext(file, metrics)

        # Style transform with wildcard
        style = TransformExpr(
            op="sh", child=WildcardExpr(line=1, col=1), params={"dx": 2, "dy": 0}, line=1, col=1
        )

        # Apply to reference
        ref = RefExpr(name="stem", line=1, col=1)
        result = apply_style(ref, style, ctx)

        # Should be shifted
        assert result.path_points[0].endpoint.x == 8.0  # 6 + 2

    def test_cli_validate_json_output(self, tmp_path: Path) -> None:
        """Test cli/validate.py --json output format."""
        import json
        import sys
        from io import StringIO

        from lsdl.cli.validate import main as validate_main

        # Create valid LSDL file
        lsdl_file = tmp_path / "test.lsdl"
        lsdl_file.write_text("meta: name=test\n")

        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        with contextlib.suppress(SystemExit):
            validate_main([str(lsdl_file), "--json"])

        output = sys.stdout.getvalue()
        sys.stdout = old_stdout

        # Parse JSON output
        data = json.loads(output)
        assert "files" in data
        assert "summary" in data
        assert data["summary"]["total_files"] == 1

    def test_cli_validate_stdin(self) -> None:
        """Test cli/validate.py with stdin input."""
        import json
        import sys
        from io import StringIO

        from lsdl.cli.validate import main as validate_main

        # Mock stdin and stdout
        old_stdin = sys.stdin
        old_stdout = sys.stdout
        sys.stdin = StringIO("meta: name=stdin-test\n")
        sys.stdout = StringIO()

        with contextlib.suppress(SystemExit):
            validate_main(["-", "--json"])

        output = sys.stdout.getvalue()
        sys.stdin = old_stdin
        sys.stdout = old_stdout

        data = json.loads(output)
        assert data["files"][0]["path"] == "<stdin>"

    def test_cli_validate_file_errors(self, tmp_path: Path) -> None:
        """Test cli/validate.py file error paths."""
        import sys
        from io import StringIO

        from lsdl.cli.validate import main as validate_main

        # Test file not found
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        exit_code = None
        try:
            validate_main([str(tmp_path / "nonexistent.lsdl")])
        except SystemExit as e:
            exit_code = e.code

        stderr_output = sys.stderr.getvalue()
        sys.stderr = old_stderr

        assert "not found" in stderr_output.lower() or exit_code != 0

        # Test directory path
        sys.stderr = StringIO()
        with contextlib.suppress(SystemExit):
            validate_main([str(tmp_path)])  # tmp_path is a directory

        stderr_output = sys.stderr.getvalue()
        sys.stderr = old_stderr
        assert "directory" in stderr_output.lower() or len(stderr_output) > 0

    def test_cli_dump_formats(self, tmp_path: Path) -> None:
        """Test cli/dump.py main() with different output formats."""
        import json
        import sys
        from io import StringIO

        from lsdl.cli.dump import main as dump_main

        # Create valid LSDL file with element
        lsdl_file = tmp_path / "test.lsdl"
        lsdl_file.write_text("""@elem stem
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
anchors: top=[6,4] base=[6,8]
""")

        # Test tree format (default)
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        with contextlib.suppress(SystemExit):
            dump_main([str(lsdl_file)])
        tree_output = sys.stdout.getvalue()
        sys.stdout = old_stdout
        assert "stem" in tree_output

        # Test JSON format
        sys.stdout = StringIO()
        with contextlib.suppress(SystemExit):
            dump_main([str(lsdl_file), "--format", "json"])
        json_output = sys.stdout.getvalue()
        sys.stdout = old_stdout

        data = json.loads(json_output)
        assert "elements" in data

        # Test stats format
        sys.stdout = StringIO()
        with contextlib.suppress(SystemExit):
            dump_main([str(lsdl_file), "--stats"])
        stats_output = sys.stdout.getvalue()
        sys.stdout = old_stdout
        assert "element" in stats_output.lower() or len(stats_output) > 0

    def test_cli_render_svg(self) -> None:
        """Test cli/render.py render_character_svg function."""
        pytest.importorskip("svgwrite")

        from lsdl.cli.render import render_character_svg
        from lsdl.evaluator import PositionedCoordinate, PositionedPathPoint

        # Create minimal positioned element
        pp = PositionedPathPoint(endpoint=PositionedCoordinate(6, 0))
        pp2 = PositionedPathPoint(endpoint=PositionedCoordinate(6, 8))
        elem = PositionedElement(
            name="test",
            path_points=[pp, pp2],
            close=False,
            width=1,
            anchors=[],
            bbox=BoundingBox.standard(),
        )

        svg_content = render_character_svg("a", elem, size=120)

        assert "<svg" in svg_content
        assert "viewBox" in svg_content
        assert "</svg>" in svg_content

    def test_style_block_invalid_fields(self) -> None:
        """Test that invalid fields in @style blocks produce errors."""
        # zone: not valid in @style
        source = """@lsdl 1.0
@style italic
zone: x-height
transform: sk(*, kx=3)
@end
"""
        with pytest.raises(ParseError) as exc_info:
            parse(source)
        assert "not valid in @style" in str(exc_info.value).lower()

        # path: not valid in @style
        source2 = """@lsdl 1.0
@style bold
path: p1 p2
transform: sc(*, sx=12)
@end
"""
        with pytest.raises(ParseError) as exc_info:
            parse(source2)
        assert "not valid in @style" in str(exc_info.value).lower()

        # anchors: not valid in @style
        source3 = """@lsdl 1.0
@style condensed
anchors: top=[6,0]
transform: sc(*, sx=8, sy=12)
@end
"""
        with pytest.raises(ParseError) as exc_info:
            parse(source3)
        assert "not valid in @style" in str(exc_info.value).lower()

        # metadata fields not valid in @style
        source4 = """@lsdl 1.0
@style light
script:Latn
transform: sc(*, sx=10)
@end
"""
        with pytest.raises(ParseError) as exc_info:
            parse(source4)
        assert (
            "metadata" in str(exc_info.value).lower() or "not valid" in str(exc_info.value).lower()
        )

    def test_close_width_missing_values(self) -> None:
        """Test that close:/width: without values produce errors."""
        # close: with no value
        source = """@lsdl 1.0
@elem bad
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
close:
anchors: top=[6,4] base=[6,8]
@end
"""
        with pytest.raises(ParseError) as exc_info:
            parse(source)
        assert (
            "close:" in str(exc_info.value).lower()
            or "true or false" in str(exc_info.value).lower()
        )

        # width: with no value
        source2 = """@lsdl 1.0
@elem bad2
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
width:
anchors: top=[6,4] base=[6,8]
@end
"""
        with pytest.raises(ParseError) as exc_info:
            parse(source2)
        assert "width" in str(exc_info.value).lower() or "expected" in str(exc_info.value).lower()

        # close: in @char block with no value
        source3 = """@lsdl 1.0
@char X LATIN-CAPITAL-X
zone: cap
path: p1 p2
p1 = [0,0]
p2 = [12,8]
close:
anchors: top=[6,0] base=[6,8]
@end
"""
        with pytest.raises(ParseError) as exc_info:
            parse(source3)
        assert (
            "close:" in str(exc_info.value).lower()
            or "true or false" in str(exc_info.value).lower()
        )

    def test_get_definition_method(self) -> None:
        """Test LSDLFile.get_definition() for character lookup with alias resolution."""
        from lsdl.model import (
            AliasDefinition,
            CharacterDefinition,
            ElementDefinition,
            LSDLFile,
            Metrics,
            RefExpr,
        )

        stem = ElementDefinition(name="stem", line=1, col=1)
        char_a = CharacterDefinition(
            char="a",
            name="LATIN-SMALL-A",
            line=2,
            col=1,
            expression=RefExpr(name="stem", line=2, col=20),
        )
        alias_x = AliasDefinition(name="x", target="a", line=3, col=1)
        alias_cycle1 = AliasDefinition(name="c1", target="c2", line=4, col=1)
        alias_cycle2 = AliasDefinition(name="c2", target="c1", line=5, col=1)

        file = LSDLFile(
            filename="test.lsdl",
            elements={"stem": stem},
            characters={"a": char_a},
            aliases={"x": alias_x, "c1": alias_cycle1, "c2": alias_cycle2},
            metrics=Metrics(),
        )

        # Direct character lookup
        assert file.get_definition("a") is char_a

        # Alias resolution to character
        assert file.get_definition("x") is char_a

        # Not found returns None
        assert file.get_definition("nonexistent") is None

        # Cycle detection
        with pytest.raises(ValueError, match="Alias cycle"):
            file.get_definition("c1")
