"""LSDL Data Model

Data model classes for LSDL Level 1 conformance (per spec Section 4, 10-12).
Defines all node types, element registry, and zone enumeration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Union

# =============================================================================
# Base Exception
# =============================================================================


class LSDLError(Exception):
    """Base exception for all LSDL errors.

    Provides uniform exception handling for both parse-time and evaluation-time
    errors. Users can catch LSDLError to handle all LSDL-related exceptions.
    """

    def __init__(self, message: str, line: int = 0, col: int = 0, filename: str = "<string>"):
        super().__init__(message)
        self.message = message
        self.line = line
        self.col = col
        self.filename = filename

    def __str__(self) -> str:
        return f"{self.filename}:{self.line}:{self.col}: {self.message}"


# =============================================================================
# Zone Enumeration (Section 10.3)
# =============================================================================


class Zone(Enum):
    """Vertical metric zones for element placement."""

    CAP = "cap"
    X_HEIGHT = "x-height"
    ASCENDER = "ascender"
    DESCENDER = "descender"
    FULL = "full"
    DIACRITIC_ABOVE = "diacritic-above"
    DIACRITIC_BELOW = "diacritic-below"


ZONE_NAMES = {z.value for z in Zone}


# =============================================================================
# Element Registry (Section 6, Appendix B)
# =============================================================================

# Base element names - closed registry for v1.0
ELEMENT_REGISTRY: frozenset[str] = frozenset(
    {
        # Verticals (4)
        "stem",
        "ascender",
        "descender",
        "full-stem",
        # Curves (12)
        "bowl",
        "counter",
        "arc",
        "hook",
        "loop",
        "ear",
        "shoulder",
        "ogee",
        # Horizontals and Diagonals (13)
        "crossbar",
        "bar",
        "arm",
        "leg",
        "diagonal",
        "apex",
        "vertex",
        "spine",
        "tail",
        "stroke",
        # Terminals (7)
        "serif",
        "spur",
        "ball",
        "finial",
        "swash",
        "flag",
        "tittle",
        # Special (3)
        "dot",
        "caron",
        "comma",
    }
)

# Standard diacritics (Appendix C)
DIACRITIC_REGISTRY: frozenset[str] = frozenset(
    {
        # Above (13)
        "acute",
        "grave",
        "circumflex",
        "tilde",
        "diaeresis",
        "macron",
        "breve",
        "caron",
        "ring",
        "dot-above",
        "double-acute",
        "horn",
        "comma-above",
        # Below (8)
        "cedilla",
        "ogonek",
        "dot-below",
        "comma-below",
        "macron-below",
        "line-below",
        "breve-below",
        "ring-below",
        # Through (3)
        "oblique-stroke",
    }
)

# Combined registry (elements + diacritics)
FULL_ELEMENT_REGISTRY: frozenset[str] = ELEMENT_REGISTRY | DIACRITIC_REGISTRY


# =============================================================================
# Coordinate and Path Types
# =============================================================================


@dataclass
class Coordinate:
    """A 2D point in the LSDL grid coordinate system (12x12 or 24x24)."""

    x: int
    y: int

    def __str__(self) -> str:
        return f"[{self.x},{self.y}]"


@dataclass
class PathPoint:
    """A path segment endpoint with optional Bezier control points.

    Line-to: control1 and control2 are None.
    Quadratic curve: control1 set, control2 is None.
    Cubic curve: both control1 and control2 set.
    """

    endpoint: Coordinate
    control1: Coordinate | None = None  # For quadratic/cubic curves
    control2: Coordinate | None = None  # For cubic curves only

    @property
    def is_line(self) -> bool:
        return self.control1 is None

    @property
    def is_quadratic(self) -> bool:
        return self.control1 is not None and self.control2 is None

    @property
    def is_cubic(self) -> bool:
        return self.control1 is not None and self.control2 is not None

    def __str__(self) -> str:
        if self.is_line:
            return str(self.endpoint)
        elif self.is_quadratic:
            return f"C({self.control1} {self.endpoint})"
        else:
            return f"C({self.control1} {self.control2} {self.endpoint})"


@dataclass
class Anchor:
    """Named attachment point on an element for composition alignment."""

    name: str
    position: Coordinate

    def __str__(self) -> str:
        return f"{self.name}={self.position}"


# =============================================================================
# Expression AST Nodes (Section 12.5-12.7)
# =============================================================================


@dataclass
class RefExpr:
    """Reference expression to an element, alias, or character by name."""

    name: str
    line: int = 0
    col: int = 0

    def __str__(self) -> str:
        return self.name


@dataclass
class ComposeExpr:
    """Composition operator expression (STACK, LR, DIA, etc.).

    op: Operator name (STACK, LR, LR3, DIA, DIA2, OVR, FRAME, LIG, APEX).
    children: Child expressions to compose.
    split: Proportional widths for LR/LR3 operators.
    anchor_override: Target anchor for DIA (attach:ANCHOR).
    merge_strategy: Join strategy for LIG (merge:STRATEGY).
    """

    op: str  # STACK, LR, LR3, DIA, DIA2, OVR, FRAME, LIG, APEX
    children: list[Expr]
    split: list[int] | None = None  # For LR/LR3
    anchor_override: str | None = None  # For DIA: attach:ANCHOR
    merge_strategy: str | None = None  # For LIG: merge:STRATEGY
    line: int = 0
    col: int = 0

    def __str__(self) -> str:
        args = ", ".join(str(c) for c in self.children)
        if self.split:
            args += ", " + "/".join(str(s) for s in self.split)
        if self.anchor_override:
            args += f", attach:{self.anchor_override}"
        if self.merge_strategy:
            args += f", merge:{self.merge_strategy}"
        return f"{self.op}({args})"


@dataclass
class TransformExpr:
    """Transform operator expression (sc=scale, sh=shift, sk=skew).

    params: Transform parameters (sx/sy for scale, dx/dy for shift, kx/ky for skew).
    """

    op: str  # sc, sh, sk
    child: Expr
    params: dict[str, int]  # sx, sy, dx, dy, kx, ky
    line: int = 0
    col: int = 0

    def __str__(self) -> str:
        params = ", ".join(f"{k}={v}" for k, v in self.params.items())
        return f"{self.op}({self.child}, {params})"


@dataclass
class WildcardExpr:
    """Wildcard (*) placeholder in @style transforms, replaced at application time."""

    line: int = 0
    col: int = 0

    def __str__(self) -> str:
        return "*"


@dataclass
class ErrorExpr:
    """Placeholder for parse errors that allows AST construction to continue.

    When the parser encounters an error but needs to continue building the AST
    (e.g., to collect additional errors), it uses ErrorExpr instead of aborting.
    The evaluator detects ErrorExpr and raises a clear error citing the original
    parse failure.
    """

    message: str
    line: int = 0
    col: int = 0

    def __str__(self) -> str:
        return f"<error: {self.message}>"


# Union type for all expression nodes.
# NOTE: Expr is a static type alias enforced by type checkers (mypy, pyright),
# not at runtime. Python's Union does not perform runtime validation;
# callers passing arbitrary objects will not raise until the object is used
# in a context expecting one of the member types. This is standard Python
# typing behavior and is intentional—runtime validation would add overhead
# with minimal benefit given static analysis coverage.
Expr = Union[RefExpr, ComposeExpr, TransformExpr, WildcardExpr, ErrorExpr]


# =============================================================================
# Definition Types (Section 10, 11)
# =============================================================================


@dataclass
class Metadata:
    """Optional metadata fields for elements and characters.

    script: ISO 15924 script code (e.g., "Latn").
    ortho: ISO 639 language codes for orthographies using this element.
    block: Unicode block name.
    cp: Unicode code point (U+XXXX format).
    freq: Frequency rank (lower = more common).
    extensions: Custom x-* extension fields.
    """

    script: str | None = None  # ISO 15924 code
    ortho: list[str] | None = None  # ISO 639 codes
    block: str | None = None  # Unicode block name
    cp: str | None = None  # U+XXXX code point
    freq: int | None = None  # Frequency rank
    extensions: dict[str, str] = field(default_factory=dict)  # x-* fields


@dataclass
class ElementDefinition:
    """Element definition from an @elem block.

    Two forms: path-form (zone + path_points + anchors) or expression-form
    (build: from_expr + expression). Path-form defines geometry directly;
    expression-form composes from other elements.
    """

    name: str  # Full element name including variant tags
    zone: Zone | None = None  # Required for path form
    path_ids: list[str] | None = None  # Path point IDs in order
    path_points: dict[str, PathPoint] | None = None  # id -> PathPoint
    close: bool = False  # Whether path closes
    width: int = 1  # 0, 1, or 2
    anchors: list[Anchor] = field(default_factory=list)
    grid: int = 12  # 12 or 24
    # For expression form (build: from_expr)
    expression: Expr | None = None
    metadata: Metadata = field(default_factory=Metadata)
    line: int = 0
    col: int = 0

    @property
    def is_expr_form(self) -> bool:
        return self.expression is not None

    @property
    def base_name(self) -> str:
        """Get base element name without variant tags."""
        return self.name.split(".")[0]


@dataclass
class CharacterDefinition:
    """Character definition from inline syntax or @char block.

    char: The literal Unicode character (e.g., 'A').
    name: Unicode character name (e.g., LATIN-CAPITAL-LETTER-A).
    expression: Composition expression (most characters).
    zone/path_points/anchors: For rare path-form characters with inline geometry.
    """

    char: str  # Literal Unicode character
    name: str  # Unicode name with hyphens
    expression: Expr | None = None  # For composition form
    # For path form (rare)
    zone: Zone | None = None
    path_ids: list[str] | None = None
    path_points: dict[str, PathPoint] | None = None
    close: bool = False
    width: int = 1
    anchors: list[Anchor] = field(default_factory=list)
    grid: int = 12  # Grid resolution (12 or 24)
    metadata: Metadata = field(default_factory=Metadata)
    line: int = 0
    col: int = 0

    @property
    def is_path_form(self) -> bool:
        return self.zone is not None


@dataclass
class AliasDefinition:
    """Alias definition from @alias, mapping one name to another.

    Supports script-qualified names (e.g., Latn:H -> stem).
    """

    name: str  # Alias name (possibly script-qualified)
    target: str  # Target element/character name
    script_qualifier: str | None = None  # Script prefix if any
    line: int = 0
    col: int = 0


@dataclass
class CaseMapping:
    """Case mapping from @case, linking uppercase/lowercase character pairs."""

    upper: str  # Uppercase character
    lower: str  # Lowercase character
    final: str | None = None  # Optional final form
    line: int = 0
    col: int = 0


@dataclass
class StyleDefinition:
    """Named style preset from @style, containing a transform with * wildcard."""

    name: str  # Style name (lowercase ASCII)
    transform: TransformExpr  # Transform expression with * wildcard
    line: int = 0
    col: int = 0


@dataclass
class Metrics:
    """Vertical metric system from @metrics block.

    Values are grid row indices (0-12), must be monotonically non-decreasing.
    """

    cap_top: int = 0
    ascender: int = 1
    cap_height: int = 2
    x_top: int = 4
    baseline: int = 8
    descender: int = 10
    desc_limit: int = 12

    def as_dict(self) -> dict[str, int]:
        return {
            "cap-top": self.cap_top,
            "ascender": self.ascender,
            "cap-height": self.cap_height,
            "x-top": self.x_top,
            "baseline": self.baseline,
            "descender": self.descender,
            "desc-limit": self.desc_limit,
        }


# =============================================================================
# File-Level Structure
# =============================================================================


@dataclass
class LSDLFile:
    """Complete parsed LSDL file containing all definitions.

    This is the top-level container returned by parse() and parse_file().
    """

    version: tuple[int, int] = (1, 0)  # Major, minor
    metrics: Metrics = field(default_factory=Metrics)
    elements: dict[str, ElementDefinition] = field(default_factory=dict)
    characters: dict[str, CharacterDefinition] = field(default_factory=dict)
    aliases: dict[str, AliasDefinition] = field(default_factory=dict)
    case_mappings: list[CaseMapping] = field(default_factory=list)
    styles: dict[str, StyleDefinition] = field(default_factory=dict)

    def get_element(self, name: str, _seen: set[str] | None = None) -> ElementDefinition | None:
        """Get element by name, resolving aliases.

        Raises:
            ValueError: If an alias cycle is detected during resolution.
        """
        if name in self.elements:
            return self.elements[name]
        if name in self.aliases:
            if _seen is None:
                _seen = set()
            if name in _seen:
                raise ValueError(f"Alias cycle detected: {name}")
            _seen.add(name)
            return self.get_element(self.aliases[name].target, _seen)
        return None

    def get_definition(
        self, name: str, _seen: set[str] | None = None
    ) -> ElementDefinition | CharacterDefinition | None:
        """Get element or character by name, resolving aliases.

        Raises:
            ValueError: If an alias cycle is detected during resolution.
        """
        if name in self.elements:
            return self.elements[name]
        if name in self.characters:
            return self.characters[name]
        if name in self.aliases:
            if _seen is None:
                _seen = set()
            if name in _seen:
                raise ValueError(f"Alias cycle detected: {name}")
            _seen.add(name)
            return self.get_definition(self.aliases[name].target, _seen)
        return None


# Backward compatibility aliases (deprecated, use canonical names)
Document = LSDLFile  #: Deprecated alias for LSDLFile
GlyphDef = CharacterDefinition  #: Deprecated alias for CharacterDefinition
StrokeDef = ElementDefinition  #: Deprecated alias for ElementDefinition
