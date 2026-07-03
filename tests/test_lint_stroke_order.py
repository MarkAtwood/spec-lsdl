"""Tests for the stroke-order linter."""

from lsdl.lint_stroke_order import check_stroke_order
from lsdl.parser import parse
from lsdl.validate import Severity


def test_h_pattern_correct():
    """H-pattern with crossbar last should not trigger a warning."""
    source = """
@lsdl 1.0
H  LATIN-CAPITAL-H = FRAME(stem.l, stem.r, crossbar.cap) script:Latn
@case H H
"""
    doc = parse(source)
    issues = check_stroke_order(doc)
    h_pattern_issues = [i for i in issues if i.code == "stroke-order-h-pattern"]
    assert len(h_pattern_issues) == 0


def test_h_pattern_violation():
    """H-pattern with crossbar in middle should trigger a warning."""
    source = """
@lsdl 1.0

@elem h_bad
zone: cap
build: from_expr
FRAME(stem.l, crossbar.cap, stem.r)
@end
"""
    doc = parse(source)
    issues = check_stroke_order(doc)
    h_pattern_issues = [i for i in issues if i.code == "stroke-order-h-pattern"]
    assert len(h_pattern_issues) == 1
    assert h_pattern_issues[0].severity == Severity.WARNING
    assert "crossbar.cap at position 2" in h_pattern_issues[0].message


def test_t_pattern_correct():
    """T-pattern with stem first should not trigger a warning."""
    source = """
@lsdl 1.0
T  LATIN-CAPITAL-T = FRAME(stem, bar.top) script:Latn
@case T T
"""
    doc = parse(source)
    issues = check_stroke_order(doc)
    t_pattern_issues = [i for i in issues if i.code == "stroke-order-t-pattern"]
    assert len(t_pattern_issues) == 0


def test_t_pattern_violation():
    """T-pattern with bar first should trigger a warning."""
    source = """
@lsdl 1.0

@elem t_bad
zone: cap
build: from_expr
FRAME(bar.top, stem)
@end
"""
    doc = parse(source)
    issues = check_stroke_order(doc)
    t_pattern_issues = [i for i in issues if i.code == "stroke-order-t-pattern"]
    assert len(t_pattern_issues) == 1
    assert t_pattern_issues[0].severity == Severity.WARNING
    assert "stem should come before bar.top" in t_pattern_issues[0].message


def test_dia_base_first_correct():
    """DIA with base first should not trigger a warning."""
    source = """
@lsdl 1.0

@elem n_tilde
zone: x-height
build: from_expr
DIA(n, tilde)
@end
"""
    doc = parse(source)
    issues = check_stroke_order(doc)
    dia_issues = [i for i in issues if i.code == "stroke-order-dia-base"]
    assert len(dia_issues) == 0


def test_dia_base_first_violation():
    """DIA with diacritic first should trigger a warning."""
    source = """
@lsdl 1.0

@elem bad_tilde
zone: x-height
build: from_expr
DIA(tilde, n)
@end
"""
    doc = parse(source)
    issues = check_stroke_order(doc)
    dia_issues = [i for i in issues if i.code == "stroke-order-dia-base"]
    assert len(dia_issues) == 1
    assert dia_issues[0].severity == Severity.WARNING
    assert "base (n) should come before diacritic (tilde)" in dia_issues[0].message


def test_stack_tittle_info():
    """STACK with tittle first should trigger an info message."""
    source = """
@lsdl 1.0
i  LATIN-SMALL-I = STACK(tittle, stem) script:Latn
@case i i
"""
    doc = parse(source)
    issues = check_stroke_order(doc)
    stack_issues = [i for i in issues if i.code == "stroke-order-stack-visual"]
    assert len(stack_issues) == 1
    assert stack_issues[0].severity == Severity.INFO
    assert "tittle first is correct for layout" in stack_issues[0].message


def test_no_issues_for_simple_elements():
    """Simple element references should not trigger any stroke-order issues."""
    source = """
@lsdl 1.0
I  LATIN-CAPITAL-I = stem.l script:Latn
O  LATIN-CAPITAL-O = bowl.cap script:Latn
@case I O
"""
    doc = parse(source)
    issues = check_stroke_order(doc)
    # Only info messages are allowed for this simple file
    warnings_errors = [i for i in issues if i.severity in (Severity.WARNING, Severity.ERROR)]
    assert len(warnings_errors) == 0


def test_nested_compositions():
    """Nested compositions should be checked recursively."""
    source = """
@lsdl 1.0

@elem nested_bad
zone: cap
build: from_expr
LR(FRAME(bar.top, stem), bowl.r, 5/7)
@end
"""
    doc = parse(source)
    issues = check_stroke_order(doc)
    t_pattern_issues = [i for i in issues if i.code == "stroke-order-t-pattern"]
    # The FRAME(bar.top, stem) inside LR should be flagged
    assert len(t_pattern_issues) == 1
