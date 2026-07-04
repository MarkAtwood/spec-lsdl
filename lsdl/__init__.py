"""LSDL - Latin Script Description Language

Reference implementation of the LSDL parser (Level 1 conformance).
Validates syntax and all 23 semantic constraints from Section 12.9.

Usage:
    from lsdl import parse_file, parse_string

    # Parse a file
    doc = parse_file("example.lsdl")

    # Parse a string
    doc = parse_string('''
    @lsdl 1.0
    b  LATIN-SMALL-B = STACK(ascender, bowl.r)
    ''')

See the LSDL Specification for full grammar and semantics.
"""

import warnings
from typing import cast

from lsdl.evaluator import (
    BoundingBox,
    ComposedElement,
    EvaluatedExpr,
    EvaluationContext,
    EvaluationError,
    PositionedAnchor,
    PositionedCoordinate,
    PositionedElement,
    PositionedPathPoint,
    apply_style,
    evaluate,
    evaluate_character,
    evaluate_element,
    evaluate_expr,
)
from lsdl.model import (
    DIACRITIC_REGISTRY,
    ELEMENT_REGISTRY,
    FULL_ELEMENT_REGISTRY,
    ZONE_NAMES,
    AliasDefinition,
    Anchor,
    CaseMapping,
    CharacterDefinition,
    ComposeExpr,
    Coordinate,
    ElementDefinition,
    Expr,
    LSDLError,
    LSDLFile,
    Metadata,
    Metrics,
    PathPoint,
    RefExpr,
    StyleDefinition,
    TransformExpr,
    WildcardExpr,
    Zone,
)
from lsdl.parser import (
    ParseError,
    parse,
    parse_file,
    parse_string,
)

__version__ = "1.0.0"

# Deprecated aliases mapping: old_name -> (new_name, removal_version)
_DEPRECATED_ALIASES = {
    "Document": ("LSDLFile", "2.0"),
    "GlyphDef": ("CharacterDefinition", "2.0"),
    "StrokeDef": ("ElementDefinition", "2.0"),
}

__all__ = [
    # === STABLE PUBLIC API ===
    # Version
    "__version__",
    # Base exception
    "LSDLError",
    # Parser functions
    "parse",
    "parse_file",
    "parse_string",
    "ParseError",
    # Evaluator functions
    "evaluate",
    "evaluate_character",
    "evaluate_element",
    "evaluate_expr",
    "apply_style",
    "EvaluationError",
    "EvaluationContext",
    # File-level structures
    "LSDLFile",
    "Metrics",
    # Definitions (parser output)
    "ElementDefinition",
    "CharacterDefinition",
    "AliasDefinition",
    "CaseMapping",
    "StyleDefinition",
    # Input types
    "Coordinate",
    "PathPoint",
    "Anchor",
    "Metadata",
    "Zone",
    "ZONE_NAMES",
    # Registries
    "ELEMENT_REGISTRY",
    "DIACRITIC_REGISTRY",
    "FULL_ELEMENT_REGISTRY",
    # === INTERNAL (may change without notice) ===
    # Evaluation output types - internal representation, may change
    "BoundingBox",
    "PositionedElement",
    "ComposedElement",
    "EvaluatedExpr",
    "PositionedAnchor",
    "PositionedCoordinate",
    "PositionedPathPoint",
    # Expression types - AST internals
    "Expr",
    "RefExpr",
    "ComposeExpr",
    "TransformExpr",
    "WildcardExpr",
    # === DEPRECATED (will be removed in v2.0) ===
    "Document",
    "GlyphDef",
    "StrokeDef",
]


def __getattr__(name: str) -> type:
    """Provide deprecated aliases with runtime warnings.

    Deprecated aliases (will be removed in v2.0):
        Document -> LSDLFile
        GlyphDef -> CharacterDefinition
        StrokeDef -> ElementDefinition
    """
    if name in _DEPRECATED_ALIASES:
        new_name, removal_version = _DEPRECATED_ALIASES[name]
        warnings.warn(
            f"{name} is deprecated, use {new_name}. Will be removed in v{removal_version}.",
            DeprecationWarning,
            stacklevel=2,
        )
        # ponytail: cast needed because globals() returns Any; actual values are type objects
        return cast(type, globals()[new_name])
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
