"""LSDL Stroke Order Linter

Checks LSDL files for stroke-order convention violations.

Convention rules from docs/stroke-order-convention.md:
- FRAME/LR/STACK child order = stroke sequence
- Pull over push: downstrokes and rightward strokes preferred
- Top-to-bottom: vertical strokes descend
- Left-to-right: horizontal strokes move rightward
- Main stroke first: primary structural element before details
- For H-pattern: crossbar should be last (stems first)
- For T-pattern: stem should be first
- Base-diacritic: in DIA(x, y), x should be the base letter
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from lsdl.model import DIACRITIC_REGISTRY, ComposeExpr, Expr, RefExpr, TransformExpr
from lsdl.validate import Severity, ValidationIssue

if TYPE_CHECKING:
    from lsdl.model import LSDLFile

__all__ = ["check_stroke_order", "StrokeOrderChecker"]


# Element classifications for stroke-order analysis
STEM_ELEMENTS = frozenset(
    {
        "stem",
        "ascender",
        "descender",
        "full-stem",
    }
)

CROSSBAR_ELEMENTS = frozenset(
    {
        "crossbar",
        "bar",
    }
)

ARM_ELEMENTS = frozenset(
    {
        "arm",
    }
)

DIAGONAL_ELEMENTS = frozenset(
    {
        "diagonal",
        "leg",
    }
)

BOWL_ELEMENTS = frozenset(
    {
        "bowl",
        "arc",
        "counter",
    }
)

# Use centralized diacritic registry from model.py
DIACRITIC_ELEMENTS = DIACRITIC_REGISTRY | frozenset({"tittle"})

DOT_ELEMENTS = frozenset(
    {
        "tittle",
        "dot",
        "dot-above",
        "dot-below",
    }
)


def _get_base_name(name: str) -> str:
    """Extract base element name from qualified name (e.g., 'stem.l' -> 'stem')."""
    return name.split(".")[0]


def _is_element_type(ref: Expr, element_set: frozenset[str]) -> bool:
    """Check if expression is a reference to an element in the given set."""
    if not isinstance(ref, RefExpr):
        return False
    return _get_base_name(ref.name) in element_set


def _is_stem(ref: Expr) -> bool:
    return _is_element_type(ref, STEM_ELEMENTS)


def _is_crossbar(ref: Expr) -> bool:
    return _is_element_type(ref, CROSSBAR_ELEMENTS)


def _is_arm(ref: Expr) -> bool:
    return _is_element_type(ref, ARM_ELEMENTS)


def _is_diagonal(ref: Expr) -> bool:
    return _is_element_type(ref, DIAGONAL_ELEMENTS)


def _is_bowl(ref: Expr) -> bool:
    return _is_element_type(ref, BOWL_ELEMENTS)


def _is_dot(ref: Expr) -> bool:
    return _is_element_type(ref, DOT_ELEMENTS)


def _is_diacritic(ref: Expr) -> bool:
    return _is_element_type(ref, DIACRITIC_ELEMENTS)


@dataclass
class StrokeOrderChecker:
    """Checker for stroke-order convention violations."""

    def check_frame_h_pattern(self, expr: ComposeExpr, context: str) -> list[ValidationIssue]:
        """Check H-pattern: FRAME with two stems and a crossbar.

        Convention: crossbar should be last (stem.l, stem.r, crossbar).
        """
        issues = []
        children = expr.children

        if len(children) != 3:
            return issues

        # Count stems and crossbars
        stems = [i for i, c in enumerate(children) if _is_stem(c)]
        crossbars = [i for i, c in enumerate(children) if _is_crossbar(c)]

        if len(stems) == 2 and len(crossbars) == 1:
            crossbar_idx = crossbars[0]
            # Crossbar should be last (index 2)
            if crossbar_idx != 2:
                crossbar_name = (
                    children[crossbar_idx].name
                    if isinstance(children[crossbar_idx], RefExpr)
                    else "crossbar"
                )
                issues.append(
                    ValidationIssue(
                        severity=Severity.WARNING,
                        message=(
                            f"H-pattern stroke order: {crossbar_name} at position "
                            f"{crossbar_idx + 1} should be last (position 3)"
                        ),
                        location=context,
                        code="stroke-order-h-pattern",
                    )
                )

        return issues

    def check_frame_t_pattern(self, expr: ComposeExpr, context: str) -> list[ValidationIssue]:
        """Check T-pattern: FRAME with stem and bar.top.

        Convention: stem should be first.
        """
        issues = []
        children = expr.children

        if len(children) != 2:
            return issues

        # Check for bar.top + stem pattern
        has_bar_top = False
        has_stem = False
        stem_idx = -1
        bar_idx = -1

        for i, c in enumerate(children):
            if isinstance(c, RefExpr):
                if c.name.startswith("bar.top") or c.name == "bar.top":
                    has_bar_top = True
                    bar_idx = i
                if _is_stem(c):
                    has_stem = True
                    stem_idx = i

        if has_bar_top and has_stem and stem_idx > bar_idx:
            stem_name = (
                children[stem_idx].name if isinstance(children[stem_idx], RefExpr) else "stem"
            )
            bar_name = (
                children[bar_idx].name if isinstance(children[bar_idx], RefExpr) else "bar.top"
            )
            issues.append(
                ValidationIssue(
                    severity=Severity.WARNING,
                    message=(
                        f"T-pattern stroke order: {stem_name} should come before "
                        f"{bar_name} (stem first, then crossbar)"
                    ),
                    location=context,
                    code="stroke-order-t-pattern",
                )
            )

        return issues

    def check_dia_base_first(self, expr: ComposeExpr, context: str) -> list[ValidationIssue]:
        """Check DIA pattern: base should come before diacritic.

        Convention: in DIA(x, y), x should be the base letter.
        """
        issues = []

        if expr.op != "DIA":
            return issues

        children = expr.children
        if len(children) != 2:
            return issues

        first, second = children

        # Check if first is a diacritic and second is not
        first_is_diacritic = _is_diacritic(first)
        second_is_diacritic = _is_diacritic(second)

        if first_is_diacritic and not second_is_diacritic:
            first_name = first.name if isinstance(first, RefExpr) else "diacritic"
            second_name = second.name if isinstance(second, RefExpr) else "base"
            issues.append(
                ValidationIssue(
                    severity=Severity.WARNING,
                    message=(
                        f"DIA stroke order: base ({second_name}) should come "
                        f"before diacritic ({first_name})"
                    ),
                    location=context,
                    code="stroke-order-dia-base",
                )
            )

        return issues

    def check_stack_tittle_pattern(self, expr: ComposeExpr, context: str) -> list[ValidationIssue]:
        """Check STACK with tittle: note that visual order differs from stroke order.

        This is informational - STACK is a visual ordering operator, so having
        tittle first is correct for visual layout but stroke order would be stem first.
        """
        issues = []

        if expr.op != "STACK":
            return issues

        children = expr.children
        if len(children) < 2:
            return issues

        # Check if first child is a tittle/dot element
        first = children[0]
        if _is_dot(first):
            # This is expected for visual layout (tittle above stem)
            # but worth noting that stroke order differs
            first_name = first.name if isinstance(first, RefExpr) else "tittle"
            issues.append(
                ValidationIssue(
                    severity=Severity.INFO,
                    message=(
                        f"STACK visual order: {first_name} first is correct for layout, "
                        f"but stroke order would be stem-first (STACK is visual operator)"
                    ),
                    location=context,
                    code="stroke-order-stack-visual",
                )
            )

        return issues

    def check_expression(self, expr: Expr, context: str) -> list[ValidationIssue]:
        """Check an expression tree for stroke-order violations."""
        issues: list[ValidationIssue] = []

        if isinstance(expr, ComposeExpr):
            # Check this expression
            if expr.op == "FRAME":
                issues.extend(self.check_frame_h_pattern(expr, context))
                issues.extend(self.check_frame_t_pattern(expr, context))
            elif expr.op == "DIA":
                issues.extend(self.check_dia_base_first(expr, context))
            elif expr.op == "STACK":
                issues.extend(self.check_stack_tittle_pattern(expr, context))

            # Recursively check children
            for child in expr.children:
                issues.extend(self.check_expression(child, context))

        elif isinstance(expr, TransformExpr):
            # Recurse into transformed child
            issues.extend(self.check_expression(expr.child, context))

        return issues


def check_stroke_order(doc: LSDLFile) -> list[ValidationIssue]:
    """Check an LSDL document for stroke-order convention violations.

    Args:
        doc: Parsed LSDL document

    Returns:
        List of validation issues (warnings/info for convention violations)
    """
    checker = StrokeOrderChecker()
    issues: list[ValidationIssue] = []

    # Check element definitions
    for name, elem in doc.elements.items():
        if elem.expression:
            context = f"element {name} (line {elem.line})"
            issues.extend(checker.check_expression(elem.expression, context))

    # Check character definitions
    for char, char_def in doc.characters.items():
        if char_def.expression:
            context = f"character {char} {char_def.name} (line {char_def.line})"
            issues.extend(checker.check_expression(char_def.expression, context))

    return issues
