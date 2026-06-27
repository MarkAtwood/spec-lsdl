"""LSDL Evaluator

Level 2 conformant evaluator for Latin Script Description Language.
Evaluates expressions to produce positioned element geometry.

Per Section 2.2 (Level 2 Renderer), this module:
- Resolves all element references to their definitions
- Computes bounding boxes for all nodes in the expression DAG
- Resolves anchor point alignment between composed elements
- Places child nodes within parent bounding boxes according to
  composition operator semantics and anchor resolution rules
- Emits element geometry as positioned path segments with width values
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from typing import Union

from lsdl.model import (
    CharacterDefinition,
    ComposeExpr,
    ElementDefinition,
    ErrorExpr,
    Expr,
    LSDLError,
    LSDLFile,
    Metrics,
    PathPoint,
    RefExpr,
    TransformExpr,
    WildcardExpr,
    Zone,
)

# =============================================================================
# Evaluation Output Types
# =============================================================================


@dataclass
class BoundingBox:
    """Axis-aligned bounding box in grid coordinates.

    The grid is 12x12 (or 24x24 for /24 elements).
    Origin [0,0] is top-left, [12,12] is bottom-right.
    """

    x_min: float
    y_min: float
    x_max: float
    y_max: float

    @property
    def width(self) -> float:
        return self.x_max - self.x_min

    @property
    def height(self) -> float:
        return self.y_max - self.y_min

    @property
    def center_x(self) -> float:
        return (self.x_min + self.x_max) / 2

    @property
    def center_y(self) -> float:
        return (self.y_min + self.y_max) / 2

    def union(self, other: BoundingBox) -> BoundingBox:
        """Return the smallest box enclosing both boxes."""
        return BoundingBox(
            x_min=min(self.x_min, other.x_min),
            y_min=min(self.y_min, other.y_min),
            x_max=max(self.x_max, other.x_max),
            y_max=max(self.y_max, other.y_max),
        )

    def translate(self, dx: float, dy: float) -> BoundingBox:
        """Return a new box translated by (dx, dy)."""
        return BoundingBox(
            x_min=self.x_min + dx,
            y_min=self.y_min + dy,
            x_max=self.x_max + dx,
            y_max=self.y_max + dy,
        )

    def scale(self, sx: float, sy: float, cx: float = 6.0, cy: float = 6.0) -> BoundingBox:
        """Scale relative to center point (cx, cy). sx, sy are factors (1.0 = 100%)."""
        return BoundingBox(
            x_min=cx + (self.x_min - cx) * sx,
            y_min=cy + (self.y_min - cy) * sy,
            x_max=cx + (self.x_max - cx) * sx,
            y_max=cy + (self.y_max - cy) * sy,
        )

    def skew(self, kx: float, ky: float, cx: float = 6.0, cy: float = 6.0) -> BoundingBox:
        """Apply skew transform. kx/ky are in grid units.

        Optimization: For axis-aligned bounding boxes, we only need to compute
        the 2 corners that determine min/max for each axis, not all 4.

        For x-skew (kx != 0): new_x = x + (y - cy) * (kx / 12.0)
        - min_x comes from combining x_min with whichever y gives smallest offset
        - max_x comes from combining x_max with whichever y gives largest offset

        For y-skew (ky != 0): new_y = y + (x - cx) * (ky / 12.0)
        - Same logic applies for y bounds
        """
        kx_factor = kx / 12.0
        ky_factor = ky / 12.0

        # For x-bounds: pick the y that minimizes/maximizes the offset
        y_for_min_offset = self.y_min if kx_factor >= 0 else self.y_max
        y_for_max_offset = self.y_max if kx_factor >= 0 else self.y_min

        new_x_min = self.x_min + (y_for_min_offset - cy) * kx_factor
        new_x_max = self.x_max + (y_for_max_offset - cy) * kx_factor

        # For y-bounds: pick the x that minimizes/maximizes the offset
        x_for_min_offset = self.x_min if ky_factor >= 0 else self.x_max
        x_for_max_offset = self.x_max if ky_factor >= 0 else self.x_min

        new_y_min = self.y_min + (x_for_min_offset - cx) * ky_factor
        new_y_max = self.y_max + (x_for_max_offset - cx) * ky_factor

        return BoundingBox(new_x_min, new_y_min, new_x_max, new_y_max)

    @classmethod
    def from_zone(cls, zone: Zone, metrics: Metrics) -> BoundingBox:
        """Create a bounding box from a zone and metrics."""
        zone_bounds = {
            Zone.CAP: (metrics.cap_top, metrics.baseline),
            Zone.X_HEIGHT: (metrics.x_top, metrics.baseline),
            Zone.ASCENDER: (metrics.ascender, metrics.baseline),
            Zone.DESCENDER: (metrics.x_top, metrics.descender),
            Zone.FULL: (metrics.cap_top, metrics.desc_limit),
            Zone.DIACRITIC_ABOVE: (metrics.cap_top, metrics.cap_height),
            Zone.DIACRITIC_BELOW: (metrics.baseline + 1, metrics.desc_limit),
        }
        y_min, y_max = zone_bounds.get(zone, (0, 12))
        return cls(x_min=0, y_min=y_min, x_max=12, y_max=y_max)

    @classmethod
    def standard(cls) -> BoundingBox:
        """Standard 12x12 bounding box."""
        return cls(x_min=0, y_min=0, x_max=12, y_max=12)


@dataclass
class PositionedCoordinate:
    """A coordinate with its position in the output space."""

    x: float
    y: float

    def translate(self, dx: float, dy: float) -> PositionedCoordinate:
        return PositionedCoordinate(self.x + dx, self.y + dy)

    def scale(self, sx: float, sy: float, cx: float = 6.0, cy: float = 6.0) -> PositionedCoordinate:
        return PositionedCoordinate(
            cx + (self.x - cx) * sx,
            cy + (self.y - cy) * sy,
        )

    def skew(self, kx: float, ky: float, cx: float = 6.0, cy: float = 6.0) -> PositionedCoordinate:
        return PositionedCoordinate(
            self.x + (self.y - cy) * (kx / 12.0),
            self.y + (self.x - cx) * (ky / 12.0),
        )


@dataclass
class PositionedPathPoint:
    """A path point in positioned output space."""

    endpoint: PositionedCoordinate
    control1: PositionedCoordinate | None = None
    control2: PositionedCoordinate | None = None

    @property
    def is_line(self) -> bool:
        return self.control1 is None

    @property
    def is_quadratic(self) -> bool:
        return self.control1 is not None and self.control2 is None

    @property
    def is_cubic(self) -> bool:
        return self.control1 is not None and self.control2 is not None


@dataclass
class PositionedAnchor:
    """An anchor with its resolved position."""

    name: str
    position: PositionedCoordinate


@dataclass
class PositionedElement:
    """A leaf element with resolved geometry.

    This is the output of evaluating a primitive element reference.
    Contains the actual path geometry positioned in the output coordinate space.
    """

    name: str
    path_points: list[PositionedPathPoint]
    close: bool
    width: int
    anchors: list[PositionedAnchor]
    bbox: BoundingBox

    def get_anchor(self, name: str) -> PositionedAnchor | None:
        """Get anchor by name."""
        for anchor in self.anchors:
            if anchor.name == name:
                return anchor
        return None


@dataclass
class ComposedElement:
    """A composition of multiple elements.

    This is the output of evaluating a composition expression.
    Contains child elements (which may themselves be composed or leaf elements)
    positioned relative to each other.
    """

    operator: str
    children: list[EvaluatedExpr]
    bbox: BoundingBox
    # Merged anchors from children (for propagation to parent compositions)
    anchors: list[PositionedAnchor] = field(default_factory=list)

    def get_anchor(self, name: str) -> PositionedAnchor | None:
        """Get anchor by name from merged anchors."""
        for anchor in self.anchors:
            if anchor.name == name:
                return anchor
        return None


# Union type for all evaluated expressions
EvaluatedExpr = Union[PositionedElement, ComposedElement]


# =============================================================================
# Evaluator Context
# =============================================================================


@dataclass
class EvaluationContext:
    """Context for expression evaluation."""

    file: LSDLFile
    metrics: Metrics
    # Cache of evaluated elements (name -> evaluated result)
    _cache: dict[str, EvaluatedExpr] = field(default_factory=dict)


class EvaluationError(LSDLError):
    """Raised when evaluation fails.

    Inherits from LSDLError for uniform exception handling.
    """

    pass


# =============================================================================
# Evaluator Implementation
# =============================================================================


def evaluate(file: LSDLFile) -> dict[str, EvaluatedExpr]:
    """Evaluate all character definitions in an LSDL file.

    Args:
        file: Parsed LSDL file

    Returns:
        Dictionary mapping character literals to their evaluated geometry

    Raises:
        EvaluationError: If evaluation fails
    """
    ctx = EvaluationContext(file=file, metrics=file.metrics)
    results = {}

    for char, char_def in file.characters.items():
        results[char] = evaluate_character(char_def, ctx)

    return results


def evaluate_character(char_def: CharacterDefinition, ctx: EvaluationContext) -> EvaluatedExpr:
    """Evaluate a single character definition.

    Handles two forms of character definitions:

    1. Expression-form characters: Characters defined with a composition expression
       (e.g., `'A' = APEX(diag.left, diag.right, crossbar)`). The expression is
       recursively evaluated to produce a ComposedElement or PositionedElement.

    2. Path-form characters: Characters defined directly with path geometry
       (e.g., `'A' zone:cap { ... }`). These have no expression but specify a zone,
       path points, and anchors inline. For path-form characters, evaluate_path_form()
       converts the raw geometry into a PositionedElement containing:
       - Positioned path points (scaled to the 12-unit grid)
       - Resolved anchors with absolute coordinates
       - A bounding box derived from the zone

    Args:
        char_def: The character definition to evaluate
        ctx: Evaluation context containing the file and metrics

    Returns:
        PositionedElement for path-form characters, or the result of evaluating
        the expression (PositionedElement or ComposedElement) for expression-form.

    Raises:
        EvaluationError: If the character has neither an expression nor path form
    """
    if char_def.expression:
        return evaluate_expr(char_def.expression, ctx)
    elif char_def.zone:
        # Path-form character: convert inline geometry to a PositionedElement.
        # The zone determines the bounding box; path_points and anchors are
        # positioned directly without composition.
        return evaluate_path_form(char_def, ctx)
    else:
        raise EvaluationError(
            f"Character {char_def.char} has neither expression nor path form",
            char_def.line,
            char_def.col,
        )


def evaluate_element(elem_def: ElementDefinition, ctx: EvaluationContext) -> EvaluatedExpr:
    """Evaluate an element definition."""
    # Check cache
    if elem_def.name in ctx._cache:
        return ctx._cache[elem_def.name]

    if elem_def.expression:
        result = evaluate_expr(elem_def.expression, ctx)
    else:
        result = evaluate_path_form_element(elem_def, ctx)

    ctx._cache[elem_def.name] = result
    return result


def evaluate_path_form(
    defn: ElementDefinition | CharacterDefinition, ctx: EvaluationContext
) -> PositionedElement:
    """Evaluate a path-form definition (element or character)."""
    if defn.zone is None:
        raise EvaluationError("Path form requires zone", defn.line, defn.col)

    bbox = BoundingBox.from_zone(defn.zone, ctx.metrics)

    # Convert path points to positioned coordinates
    path_points = []
    if defn.path_points and defn.path_ids:
        for pid in defn.path_ids:
            if pid not in defn.path_points:
                raise EvaluationError(f"Path point {pid} not defined", defn.line, defn.col)
            pp = defn.path_points[pid]
            positioned = position_path_point(pp, defn.grid)
            path_points.append(positioned)

    # Convert anchors to positioned anchors
    anchors = []
    for anchor in defn.anchors:
        pos = PositionedCoordinate(float(anchor.position.x), float(anchor.position.y))
        anchors.append(PositionedAnchor(name=anchor.name, position=pos))

    # ElementDefinition uses name; CharacterDefinition uses char for identity
    name = defn.name if isinstance(defn, ElementDefinition) else defn.char
    return PositionedElement(
        name=name,
        path_points=path_points,
        close=defn.close,
        width=defn.width,
        anchors=anchors,
        bbox=bbox,
    )


def evaluate_path_form_element(
    elem_def: ElementDefinition, ctx: EvaluationContext
) -> PositionedElement:
    """Evaluate a path-form element definition."""
    return evaluate_path_form(elem_def, ctx)


def position_path_point(pp: PathPoint, grid: int = 12) -> PositionedPathPoint:
    """Convert a PathPoint to a PositionedPathPoint."""
    # Scale coordinates if using /24 grid
    scale = 12.0 / grid

    endpoint = PositionedCoordinate(float(pp.endpoint.x) * scale, float(pp.endpoint.y) * scale)

    control1 = None
    if pp.control1:
        control1 = PositionedCoordinate(float(pp.control1.x) * scale, float(pp.control1.y) * scale)

    control2 = None
    if pp.control2:
        control2 = PositionedCoordinate(float(pp.control2.x) * scale, float(pp.control2.y) * scale)

    return PositionedPathPoint(endpoint=endpoint, control1=control1, control2=control2)


def evaluate_expr(expr: Expr, ctx: EvaluationContext) -> EvaluatedExpr:
    """Evaluate an expression to positioned geometry."""
    if isinstance(expr, RefExpr):
        return evaluate_ref(expr, ctx)
    elif isinstance(expr, ComposeExpr):
        return evaluate_compose(expr, ctx)
    elif isinstance(expr, TransformExpr):
        return evaluate_transform(expr, ctx)
    elif isinstance(expr, WildcardExpr):
        raise EvaluationError(
            "Wildcard (*) cannot be evaluated outside @style context",
            expr.line,
            expr.col,
        )
    elif isinstance(expr, ErrorExpr):
        raise EvaluationError(
            f"Cannot evaluate expression due to parse error: {expr.message}",
            expr.line,
            expr.col,
        )
    else:
        # All Expr subtypes have line/col; use getattr for safety with unexpected types
        line = getattr(expr, "line", 0)
        col = getattr(expr, "col", 0)
        raise EvaluationError(f"Unknown expression type: {type(expr)}", line, col)


def evaluate_ref(ref: RefExpr, ctx: EvaluationContext) -> EvaluatedExpr:
    """Evaluate an element/character reference."""
    name = ref.name

    # Check if it's a character reference
    if name in ctx.file.characters:
        return evaluate_character(ctx.file.characters[name], ctx)

    # Check if it's an element reference
    if name in ctx.file.elements:
        return evaluate_element(ctx.file.elements[name], ctx)

    # Check if it's an alias
    if name in ctx.file.aliases:
        target = ctx.file.aliases[name].target
        return evaluate_ref(RefExpr(name=target, line=ref.line, col=ref.col), ctx)

    # Element not found - create a placeholder (for standard elements not defined in file)
    # In a full implementation, standard elements would be pre-defined
    return create_placeholder_element(name, ctx)


def create_placeholder_element(name: str, ctx: EvaluationContext) -> PositionedElement:
    """Create a placeholder for standard library elements not explicitly defined.

    In a production implementation, the standard element library would be loaded.
    This placeholder allows evaluation to proceed for testing.

    Emits a warning to alert users that an element was not found and a placeholder
    with empty geometry is being used instead.
    """
    # Use stacklevel=1 (this function) rather than attempting to point to user code.
    # The call depth between user code and this function varies (e.g., direct evaluation
    # vs. nested compositions, alias resolution, transform chains), making a fixed
    # stacklevel unreliable. The element name in the message provides sufficient context.
    warnings.warn(
        f"Element '{name}' not found; using placeholder with empty geometry",
        category=UserWarning,
        stacklevel=1,
    )

    # Determine zone based on element name
    zone = Zone.X_HEIGHT
    if name in ("ascender", "ascender.curved"):
        zone = Zone.ASCENDER
    elif name in ("descender",):
        zone = Zone.DESCENDER
    elif "diacritic" in name or name in (
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
    ):
        zone = Zone.DIACRITIC_ABOVE
    elif name in (
        "cedilla",
        "ogonek",
        "dot-below",
        "comma-below",
        "macron-below",
        "line-below",
        "breve-below",
        "ring-below",
    ):
        zone = Zone.DIACRITIC_BELOW

    bbox = BoundingBox.from_zone(zone, ctx.metrics)

    # Anchor positioning constants
    grid_center = 6.0  # Horizontal center of the 12-unit LSDL grid
    diacritic_clearance = 1.0  # Vertical spacing for diacritic attachment points

    # Create standard anchors at grid center
    anchors = [
        PositionedAnchor("top", PositionedCoordinate(grid_center, bbox.y_min)),
        PositionedAnchor("base", PositionedCoordinate(grid_center, bbox.y_max)),
        PositionedAnchor("mid", PositionedCoordinate(grid_center, bbox.center_y)),
        PositionedAnchor(
            "mark-above", PositionedCoordinate(grid_center, bbox.y_min - diacritic_clearance)
        ),
        PositionedAnchor(
            "mark-below", PositionedCoordinate(grid_center, bbox.y_max + diacritic_clearance)
        ),
        PositionedAnchor("attach", PositionedCoordinate(grid_center, bbox.center_y)),
    ]

    return PositionedElement(
        name=name,
        path_points=[],  # No geometry for placeholders
        close=False,
        width=1,
        anchors=anchors,
        bbox=bbox,
    )


# =============================================================================
# Composition Operator Evaluation
# =============================================================================


def evaluate_compose(expr: ComposeExpr, ctx: EvaluationContext) -> ComposedElement:
    """Evaluate a composition operator expression."""
    op = expr.op

    # Evaluate all children first
    children = [evaluate_expr(child, ctx) for child in expr.children]

    # Dispatch to operator-specific handlers. An if/elif chain is used rather than
    # a dict dispatch table because each handler requires different parameters from
    # the ComposeExpr (split, anchor_override, merge_strategy). A dict would need
    # lambdas or a wrapper layer, adding indirection without improving clarity.
    if op == "STACK":
        return evaluate_stack(children, ctx)
    elif op == "LR":
        return evaluate_lr(children, expr.split, ctx)
    elif op == "LR3":
        return evaluate_lr(children, expr.split, ctx)  # LR3 is just LR with 3+ children
    elif op == "DIA":
        return evaluate_dia(children, expr.anchor_override, ctx)
    elif op == "DIA2":
        return evaluate_dia2(children, ctx)
    elif op == "OVR":
        return evaluate_ovr(children, ctx)
    elif op == "FRAME":
        return evaluate_frame(children, ctx)
    elif op == "LIG":
        return evaluate_lig(children, expr.merge_strategy, ctx)
    elif op == "APEX":
        return evaluate_apex(children, ctx)
    else:
        raise EvaluationError(f"Unknown composition operator: {op}", expr.line, expr.col)


def evaluate_stack(children: list[EvaluatedExpr], ctx: EvaluationContext) -> ComposedElement:
    """Evaluate STACK operator - vertical stacking.

    Per Section 8.2: Stacks elements along a shared vertical axis, top to bottom.
    The first element's `base` anchor aligns with the second element's `top` anchor.
    """
    if len(children) < 2:
        raise EvaluationError(f"STACK requires at least 2 children, got {len(children)}")

    # Process first child separately to initialize combined_bbox,
    # avoiding BoundingBox | None union for mypy
    first_child = children[0]
    positioned_children: list[EvaluatedExpr] = [first_child]
    combined_bbox = first_child.bbox

    for child in children[1:]:
        # Align this child's top to previous child's base
        prev_child = positioned_children[-1]
        prev_base = get_anchor(prev_child, "base")
        curr_top = get_anchor(child, "top")

        if prev_base and curr_top:
            # Shift current child so its top aligns with prev's base
            dy = prev_base.position.y - curr_top.position.y
            shifted = translate_element(child, 0, dy)
            positioned_children.append(shifted)
            combined_bbox = combined_bbox.union(shifted.bbox)
        else:
            # Fallback: stack based on bounding boxes
            dy = combined_bbox.y_max - child.bbox.y_min
            shifted = translate_element(child, 0, dy)
            positioned_children.append(shifted)
            combined_bbox = combined_bbox.union(shifted.bbox)

    # Collect merged anchors from all children
    merged_anchors = merge_anchors(positioned_children)

    return ComposedElement(
        operator="STACK",
        children=positioned_children,
        bbox=combined_bbox,
        anchors=merged_anchors,
    )


def evaluate_lr(
    children: list[EvaluatedExpr], split: list[int] | None, ctx: EvaluationContext
) -> ComposedElement:
    """Evaluate LR operator - left-right horizontal layout.

    Per Section 8.3: Places elements side by side, left to right, aligned on baseline.
    Split values are proportional; renderer divides parent box according to ratio.
    """
    if not children or len(children) == 0:
        # Empty children list: return a placeholder composed element
        # with a standard bounding box to allow evaluation to proceed
        return ComposedElement(
            operator="LR",
            children=[],
            bbox=BoundingBox.standard(),
            anchors=[],
        )

    # Determine split proportions
    if split:
        proportions = split
    else:
        # Default: equal split
        n = len(children)
        proportions = [12 // n] * n

    # Normalize proportions to sum to 12
    # Guard against zero total (e.g., split=[0,0,0]) by using minimum of 1
    total = max(sum(proportions), 1)
    widths = [12.0 * p / total for p in proportions]

    positioned_children: list[EvaluatedExpr] = []
    current_x = 0.0
    # Initialize combined_bbox to first child's bbox as fallback,
    # ensuring we never leave it as None even if widths is empty
    combined_bbox = children[0].bbox if children else BoundingBox.standard()

    for _i, (child, width) in enumerate(zip(children, widths)):
        # Scale child horizontally to fit allocated width
        # Use minimum width of 1 grid unit to avoid division by zero or extreme scaling
        child_width = max(child.bbox.width, 1.0)
        scale_x = width / child_width
        scaled = scale_element(child, scale_x, 1.0, child.bbox.center_x, child.bbox.center_y)

        # Translate to current x position
        dx = current_x - scaled.bbox.x_min
        shifted = translate_element(scaled, dx, 0)

        positioned_children.append(shifted)

        combined_bbox = shifted.bbox if combined_bbox is None else combined_bbox.union(shifted.bbox)

        current_x += width

    merged_anchors = merge_anchors(positioned_children)

    return ComposedElement(
        operator="LR",
        children=positioned_children,
        bbox=combined_bbox,
        anchors=merged_anchors,
    )


def evaluate_dia(
    children: list[EvaluatedExpr], anchor_override: str | None, ctx: EvaluationContext
) -> ComposedElement:
    """Evaluate DIA operator - diacritic attachment.

    Per Section 8.5 and 7.3:
    - Diacritic's `attach` anchor aligns with base's `mark-above` or `mark-below`
    - Direction inferred from diacritic's zone
    - attach: parameter can override the target anchor
    """
    if len(children) < 2:
        raise EvaluationError("DIA requires at least 2 arguments")

    base = children[0]
    mark = children[1]

    # Get diacritic's attach anchor
    mark_attach = get_anchor(mark, "attach")
    if not mark_attach:
        # Fallback: use center of diacritic
        mark_attach = PositionedAnchor(
            "attach", PositionedCoordinate(mark.bbox.center_x, mark.bbox.center_y)
        )

    # Determine target anchor on base
    if anchor_override:
        target_anchor_name = anchor_override
    else:
        # Infer direction from mark position (above or below base)
        if mark.bbox.center_y < base.bbox.center_y:
            target_anchor_name = "mark-above"
        else:
            target_anchor_name = "mark-below"

    base_target = get_anchor(base, target_anchor_name)
    if not base_target:
        # Fallback: center horizontally, position at edge vertically
        if target_anchor_name == "mark-above":
            base_target = PositionedAnchor(
                target_anchor_name,
                PositionedCoordinate(base.bbox.center_x, base.bbox.y_min),
            )
        else:
            base_target = PositionedAnchor(
                target_anchor_name,
                PositionedCoordinate(base.bbox.center_x, base.bbox.y_max),
            )

    # Translate mark so its attach anchor aligns with base's target anchor
    dx = base_target.position.x - mark_attach.position.x
    dy = base_target.position.y - mark_attach.position.y
    positioned_mark = translate_element(mark, dx, dy)

    # Combined bounding box expands to include diacritic (per Section 15.3.4)
    combined_bbox = base.bbox.union(positioned_mark.bbox)

    # Merge anchors, preferring base's anchors
    merged_anchors = merge_anchors([base, positioned_mark])

    return ComposedElement(
        operator="DIA",
        children=[base, positioned_mark],
        bbox=combined_bbox,
        anchors=merged_anchors,
    )


def evaluate_dia2(children: list[EvaluatedExpr], ctx: EvaluationContext) -> ComposedElement:
    """Evaluate DIA2 operator - double diacritic attachment.

    Per Section 8.6 and 15.4:
    - First mark attaches closest to base
    - Second mark stacks outward from first mark (not from base's anchor)

    For two above-marks: mark2's attach aligns to mark1's y-minimum, centered horizontally.
    For two below-marks: mark2's attach aligns to mark1's y-maximum, centered horizontally.
    For mixed (above+below): each attaches independently to base's mark-above/mark-below.

    Returns a ComposedElement with children [base, positioned_mark1, positioned_mark2]
    representing all 3 original inputs appropriately positioned.
    """
    if len(children) != 3:
        raise EvaluationError("DIA2 requires exactly 3 arguments")

    base = children[0]
    mark1 = children[1]
    mark2 = children[2]

    # First, attach mark1 to base using standard DIA logic
    dia1_result = evaluate_dia([base, mark1], None, ctx)
    positioned_mark1 = dia1_result.children[1]

    # Determine mark directions (above or below base)
    mark1_above = mark1.bbox.center_y < base.bbox.center_y
    mark2_above = mark2.bbox.center_y < base.bbox.center_y

    # Get mark2's attach anchor
    mark2_attach = get_anchor(mark2, "attach")
    if not mark2_attach:
        mark2_attach = PositionedAnchor(
            "attach", PositionedCoordinate(mark2.bbox.center_x, mark2.bbox.center_y)
        )

    # Position mark2 based on direction combination
    if mark1_above and mark2_above:
        # Two above-marks: mark2 stacks above mark1
        # Per spec 15.4: align to mark1's y-minimum, centered horizontally on mark1
        target_x = positioned_mark1.bbox.center_x
        target_y = positioned_mark1.bbox.y_min
    elif not mark1_above and not mark2_above:
        # Two below-marks: mark2 stacks below mark1
        # Per spec 15.4: align to mark1's y-maximum, centered horizontally on mark1
        target_x = positioned_mark1.bbox.center_x
        target_y = positioned_mark1.bbox.y_max
    else:
        # Mixed directions: mark2 attaches independently to base
        # Use standard DIA positioning for mark2 relative to base
        if mark2_above:
            base_target = get_anchor(base, "mark-above")
            if not base_target:
                base_target = PositionedAnchor(
                    "mark-above", PositionedCoordinate(base.bbox.center_x, base.bbox.y_min)
                )
        else:
            base_target = get_anchor(base, "mark-below")
            if not base_target:
                base_target = PositionedAnchor(
                    "mark-below", PositionedCoordinate(base.bbox.center_x, base.bbox.y_max)
                )
        target_x = base_target.position.x
        target_y = base_target.position.y

    # Translate mark2 so its attach anchor aligns with target position
    dx = target_x - mark2_attach.position.x
    dy = target_y - mark2_attach.position.y
    positioned_mark2 = translate_element(mark2, dx, dy)

    # Build flattened children list: base, positioned_mark1, positioned_mark2
    # All three are now in consistent coordinate space
    flattened_children = [dia1_result.children[0], positioned_mark1, positioned_mark2]

    # Compute combined bounding box
    combined_bbox = dia1_result.bbox.union(positioned_mark2.bbox)

    # Merge anchors from all three elements
    merged_anchors = merge_anchors(flattened_children)

    return ComposedElement(
        operator="DIA2",
        children=flattened_children,
        bbox=combined_bbox,
        anchors=merged_anchors,
    )


def evaluate_ovr(children: list[EvaluatedExpr], ctx: EvaluationContext) -> ComposedElement:
    """Evaluate OVR operator - overlay.

    Per Section 8.7: Places child b on top of child a within same bounding box.
    Both children occupy the full parent box.
    """
    if len(children) != 2:
        raise EvaluationError("OVR requires exactly 2 children")

    base = children[0]
    overlay = children[1]

    # Center overlay on base's bounding box
    dx = base.bbox.center_x - overlay.bbox.center_x
    dy = base.bbox.center_y - overlay.bbox.center_y
    positioned_overlay = translate_element(overlay, dx, dy)

    # Use base's bounding box (both share it)
    combined_bbox = base.bbox

    merged_anchors = merge_anchors([base, positioned_overlay])

    return ComposedElement(
        operator="OVR",
        children=[base, positioned_overlay],
        bbox=combined_bbox,
        anchors=merged_anchors,
    )


def evaluate_frame(children: list[EvaluatedExpr], ctx: EvaluationContext) -> ComposedElement:
    """Evaluate FRAME operator - assembled from attachment points.

    Per Section 8.8: Assembles character from named parts positioned at their
    defined anchor points, without imposing a single axis of composition.
    """
    if len(children) < 2:
        raise EvaluationError("FRAME requires at least 2 children")

    # For FRAME, we position children based on matching anchors
    # This is more complex - we need to find compatible anchor pairs
    positioned_children: list[EvaluatedExpr] = [children[0]]
    combined_bbox = children[0].bbox

    for child in children[1:]:
        # Find a matching anchor between this child and already-positioned children
        best_match = find_anchor_match(positioned_children, child)

        if best_match:
            placed_anchor, child_anchor = best_match
            dx = placed_anchor.position.x - child_anchor.position.x
            dy = placed_anchor.position.y - child_anchor.position.y
            shifted = translate_element(child, dx, dy)
        else:
            # No matching anchor found - place adjacent
            dx = combined_bbox.x_max - child.bbox.x_min
            shifted = translate_element(child, dx, 0)

        positioned_children.append(shifted)
        combined_bbox = combined_bbox.union(shifted.bbox)

    merged_anchors = merge_anchors(positioned_children)

    return ComposedElement(
        operator="FRAME",
        children=positioned_children,
        bbox=combined_bbox,
        anchors=merged_anchors,
    )


def evaluate_lig(
    children: list[EvaluatedExpr], merge_strategy: str | None, ctx: EvaluationContext
) -> ComposedElement:
    """Evaluate LIG operator - ligature composition.

    Per Section 14: Merges two complete characters into a combined form.
    The merge: parameter specifies the structural joining strategy.
    Default is horizontal adjacency (like LR).
    """
    if len(children) < 2:
        raise EvaluationError("LIG requires at least 2 children")

    # Default behavior: horizontal adjacency (like LR without scaling)
    if not merge_strategy or merge_strategy == "adjacent":
        return evaluate_lr(children, None, ctx)

    # For specific merge strategies, we need to adjust positioning
    # This is a simplified implementation - full implementation would
    # handle each merge strategy specifically

    if merge_strategy == "stem-shared":
        # Shared stem: second character overlaps first's right edge
        return _lig_stem_shared(children, ctx)
    elif merge_strategy == "hook-tittle":
        # f+i: f's hook replaces i's tittle
        return _lig_overlap(children, overlap=2, ctx=ctx)
    elif merge_strategy == "hook-ascender":
        # f+l: f's hook merges into l's ascender
        return _lig_overlap(children, overlap=2, ctx=ctx)
    elif merge_strategy == "bowl-stem":
        # O+E: O's right curve merges into E's stem
        return _lig_overlap(children, overlap=3, ctx=ctx)
    else:
        # Unknown strategy - fall back to horizontal adjacency
        return evaluate_lr(children, None, ctx)


def _lig_stem_shared(children: list[EvaluatedExpr], ctx: EvaluationContext) -> ComposedElement:
    """Ligature with shared stem (like AE)."""
    base = children[0]
    second = children[1]

    # Overlap so stem is shared - shift second left by some amount
    overlap = 3  # Approximate stem width
    dx = base.bbox.x_max - second.bbox.x_min - overlap
    shifted = translate_element(second, dx, 0)

    combined_bbox = base.bbox.union(shifted.bbox)
    merged_anchors = merge_anchors([base, shifted])

    return ComposedElement(
        operator="LIG",
        children=[base, shifted],
        bbox=combined_bbox,
        anchors=merged_anchors,
    )


def _lig_overlap(
    children: list[EvaluatedExpr], overlap: float, ctx: EvaluationContext
) -> ComposedElement:
    """Ligature with specified overlap amount."""
    positioned = [children[0]]
    combined_bbox = children[0].bbox

    for child in children[1:]:
        dx = combined_bbox.x_max - child.bbox.x_min - overlap
        shifted = translate_element(child, dx, 0)
        positioned.append(shifted)
        combined_bbox = combined_bbox.union(shifted.bbox)

    merged_anchors = merge_anchors(positioned)

    return ComposedElement(
        operator="LIG",
        children=positioned,
        bbox=combined_bbox,
        anchors=merged_anchors,
    )


def evaluate_apex(children: list[EvaluatedExpr], ctx: EvaluationContext) -> ComposedElement:
    """Evaluate APEX operator - diagonal meeting point.

    Per Section 8.9: Semantic alias for FRAME with convention that first two
    arguments are diagonal stems meeting at top, subsequent arguments are horizontal.
    """
    # APEX is essentially FRAME with the convention that elements meet at apex
    return evaluate_frame(children, ctx)


# =============================================================================
# Transform Operator Evaluation
# =============================================================================


def evaluate_transform(expr: TransformExpr, ctx: EvaluationContext) -> EvaluatedExpr:
    """Evaluate a transform operator expression.

    Per Section 9.1: Evaluation proceeds inside-out (standard function composition).
    """
    # First evaluate the child (inside-out)
    child = evaluate_expr(expr.child, ctx)

    op = expr.op
    params = expr.params

    if op == "sc":
        # Scale: sx, sy are fractions of 12 (12 = 100%)
        sx = params.get("sx", 12) / 12.0
        sy = params.get("sy", 12) / 12.0
        return scale_element(child, sx, sy)
    elif op == "sh":
        # Shift: dx, dy are grid units
        dx = float(params.get("dx", 0))
        dy = float(params.get("dy", 0))
        return translate_element(child, dx, dy)
    elif op == "sk":
        # Skew: kx, ky tilt the coordinate space
        kx = float(params.get("kx", 0))
        ky = float(params.get("ky", 0))
        return skew_element(child, kx, ky)
    else:
        raise EvaluationError(f"Unknown transform operator: {op}", expr.line, expr.col)


# =============================================================================
# Element Transformation Helpers
# =============================================================================

# NOTE: translate_element, scale_element, and skew_element share parallel structure.
# Kept separate intentionally: each is self-contained and readable. A generic
# _transform_element helper would add indirection without meaningful simplification.


def translate_element(elem: EvaluatedExpr, dx: float, dy: float) -> EvaluatedExpr:
    """Translate an element by (dx, dy)."""
    if isinstance(elem, PositionedElement):
        new_points = [
            PositionedPathPoint(
                endpoint=pp.endpoint.translate(dx, dy),
                control1=pp.control1.translate(dx, dy) if pp.control1 else None,
                control2=pp.control2.translate(dx, dy) if pp.control2 else None,
            )
            for pp in elem.path_points
        ]
        new_anchors = [PositionedAnchor(a.name, a.position.translate(dx, dy)) for a in elem.anchors]
        return PositionedElement(
            name=elem.name,
            path_points=new_points,
            close=elem.close,
            width=elem.width,
            anchors=new_anchors,
            bbox=elem.bbox.translate(dx, dy),
        )
    elif isinstance(elem, ComposedElement):
        new_children = [translate_element(c, dx, dy) for c in elem.children]
        new_anchors = [PositionedAnchor(a.name, a.position.translate(dx, dy)) for a in elem.anchors]
        return ComposedElement(
            operator=elem.operator,
            children=new_children,
            bbox=elem.bbox.translate(dx, dy),
            anchors=new_anchors,
        )
    else:
        raise EvaluationError(f"Cannot translate {type(elem)}")


def scale_element(
    elem: EvaluatedExpr, sx: float, sy: float, cx: float = 6.0, cy: float = 6.0
) -> EvaluatedExpr:
    """Scale an element by (sx, sy) relative to center (cx, cy)."""
    if isinstance(elem, PositionedElement):
        new_points = [
            PositionedPathPoint(
                endpoint=pp.endpoint.scale(sx, sy, cx, cy),
                control1=pp.control1.scale(sx, sy, cx, cy) if pp.control1 else None,
                control2=pp.control2.scale(sx, sy, cx, cy) if pp.control2 else None,
            )
            for pp in elem.path_points
        ]
        new_anchors = [
            PositionedAnchor(a.name, a.position.scale(sx, sy, cx, cy)) for a in elem.anchors
        ]
        return PositionedElement(
            name=elem.name,
            path_points=new_points,
            close=elem.close,
            width=elem.width,
            anchors=new_anchors,
            bbox=elem.bbox.scale(sx, sy, cx, cy),
        )
    elif isinstance(elem, ComposedElement):
        new_children = [scale_element(c, sx, sy, cx, cy) for c in elem.children]
        new_anchors = [
            PositionedAnchor(a.name, a.position.scale(sx, sy, cx, cy)) for a in elem.anchors
        ]
        return ComposedElement(
            operator=elem.operator,
            children=new_children,
            bbox=elem.bbox.scale(sx, sy, cx, cy),
            anchors=new_anchors,
        )
    else:
        raise EvaluationError(f"Cannot scale {type(elem)}")


def skew_element(
    elem: EvaluatedExpr, kx: float, ky: float, cx: float = 6.0, cy: float = 6.0
) -> EvaluatedExpr:
    """Apply skew transform to an element."""
    if isinstance(elem, PositionedElement):
        new_points = [
            PositionedPathPoint(
                endpoint=pp.endpoint.skew(kx, ky, cx, cy),
                control1=pp.control1.skew(kx, ky, cx, cy) if pp.control1 else None,
                control2=pp.control2.skew(kx, ky, cx, cy) if pp.control2 else None,
            )
            for pp in elem.path_points
        ]
        new_anchors = [
            PositionedAnchor(a.name, a.position.skew(kx, ky, cx, cy)) for a in elem.anchors
        ]
        return PositionedElement(
            name=elem.name,
            path_points=new_points,
            close=elem.close,
            width=elem.width,
            anchors=new_anchors,
            bbox=elem.bbox.skew(kx, ky, cx, cy),
        )
    elif isinstance(elem, ComposedElement):
        new_children = [skew_element(c, kx, ky, cx, cy) for c in elem.children]
        new_anchors = [
            PositionedAnchor(a.name, a.position.skew(kx, ky, cx, cy)) for a in elem.anchors
        ]
        return ComposedElement(
            operator=elem.operator,
            children=new_children,
            bbox=elem.bbox.skew(kx, ky, cx, cy),
            anchors=new_anchors,
        )
    else:
        raise EvaluationError(f"Cannot skew {type(elem)}")


# =============================================================================
# Anchor Resolution Helpers
# =============================================================================


def get_anchor(elem: EvaluatedExpr, name: str) -> PositionedAnchor | None:
    """Get an anchor by name from an evaluated expression."""
    if isinstance(elem, (PositionedElement, ComposedElement)):
        return elem.get_anchor(name)
    return None


def merge_anchors(elements: list[EvaluatedExpr]) -> list[PositionedAnchor]:
    """Merge anchors from multiple elements.

    Earlier elements' anchors take precedence over later ones with the same name.
    This allows base elements to retain their anchor definitions when composed.
    """
    seen: set[str] = set()
    result: list[PositionedAnchor] = []

    for elem in elements:
        if isinstance(elem, (PositionedElement, ComposedElement)):
            for anchor in elem.anchors:
                # First occurrence wins (base element's anchors preferred)
                if anchor.name not in seen:
                    seen.add(anchor.name)
                    result.append(anchor)

    return result


def find_anchor_match(
    placed: list[EvaluatedExpr], new_elem: EvaluatedExpr
) -> tuple[PositionedAnchor, PositionedAnchor] | None:
    """Find matching anchors between placed elements and a new element.

    Returns tuple of (placed_anchor, new_elem_anchor) if a match is found.
    """
    # Common anchor pairs that typically connect
    anchor_pairs = [
        ("right", "left"),
        ("arm.right", "arm.left"),
        ("top", "base"),
        ("base", "top"),
    ]

    for placed_elem in placed:
        for placed_name, new_name in anchor_pairs:
            placed_anchor = get_anchor(placed_elem, placed_name)
            new_anchor = get_anchor(new_elem, new_name)
            if placed_anchor and new_anchor:
                return (placed_anchor, new_anchor)

    return None


# =============================================================================
# Style Transform Application
# =============================================================================


def apply_style(
    expr: Expr, style_transform: TransformExpr, ctx: EvaluationContext
) -> EvaluatedExpr:
    """Apply a named style transform to an expression.

    The style_transform's WildcardExpr (*) child is replaced by expr before
    evaluation. Requires a valid EvaluationContext with file and metrics.
    """
    # Create a new transform expression with the target replacing the wildcard
    applied_transform = TransformExpr(
        op=style_transform.op,
        child=expr,
        params=style_transform.params,
        line=style_transform.line,
        col=style_transform.col,
    )

    return evaluate_transform(applied_transform, ctx)
