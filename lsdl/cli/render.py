"""LSDL Render CLI

Command-line tool to render LSDL glyphs to SVG.

Usage:
    lsdl-render [OPTIONS] FILE [CHARACTERS...]

Examples:
    lsdl-render font.lsdl --all              # Render all characters
    lsdl-render font.lsdl a b c              # Render specific characters
    lsdl-render font.lsdl --show-grid A      # Render A with grid overlay
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lsdl.cli import get_version
from lsdl.evaluator import (
    ComposedElement,
    EvaluatedExpr,
    PositionedElement,
    PositionedPathPoint,
    evaluate,
)
from lsdl.parser import ParseError, parse_file

# Note: svgwrite is imported at runtime inside render_character_svg() and main()
# Type annotations use string literals (via `from __future__ import annotations`)
# so no TYPE_CHECKING import is needed.

__all__ = ["main"]


# Zone colors for --show-zones overlay
ZONE_COLORS = {
    "cap": "#ffdddd",
    "x-height": "#ddffdd",
    "ascender": "#ddddff",
    "descender": "#ffffdd",
    "full": "#ffddff",
    "diacritic-above": "#ddffff",
    "diacritic-below": "#ffeedd",
}


def _render_element_to_svg(
    elem: EvaluatedExpr,
    dwg: svgwrite.Drawing,
    group: Group,
    scale: float,
    stroke_color: str = "#000000",
) -> None:
    """Render an evaluated element to an SVG group.

    Internal helper - requires svgwrite to be installed.

    Args:
        elem: Evaluated element (PositionedElement or ComposedElement)
        dwg: SVG drawing object
        group: SVG group to render into
        scale: Coordinate scale factor (viewBox size / 12)
        stroke_color: Stroke color for paths
    """
    if isinstance(elem, PositionedElement):
        _render_positioned_element(elem, dwg, group, scale, stroke_color)
    elif isinstance(elem, ComposedElement):
        for child in elem.children:
            _render_element_to_svg(child, dwg, group, scale, stroke_color)


def _render_positioned_element(
    elem: PositionedElement,
    dwg: svgwrite.Drawing,
    group: Group,
    scale: float,
    stroke_color: str,
) -> None:
    """Render a positioned element's path to SVG."""
    if not elem.path_points:
        return

    # Build SVG path data
    path_data = _build_path_data(elem.path_points, scale)
    if elem.close:
        path_data += " Z"

    if not path_data.strip():
        return

    # Map width 0/1/2 to stroke widths
    stroke_widths = {0: 0.5, 1: 1.0, 2: 2.0}
    stroke_width = stroke_widths.get(elem.width, 1.0) * scale / 10

    group.add(
        dwg.path(
            d=path_data,
            stroke=stroke_color,
            stroke_width=stroke_width,
            fill="none" if not elem.close else stroke_color,
            stroke_linecap="round",
            stroke_linejoin="round",
        )
    )


def _build_path_data(points: list[PositionedPathPoint], scale: float) -> str:
    """Build SVG path data string from positioned path points."""
    if not points:
        return ""

    parts = []
    for i, pp in enumerate(points):
        x = pp.endpoint.x * scale
        y = pp.endpoint.y * scale

        if i == 0:
            # Move to first point
            parts.append(f"M {x:.2f} {y:.2f}")
        elif pp.is_line:
            parts.append(f"L {x:.2f} {y:.2f}")
        elif pp.is_quadratic:
            # is_quadratic guarantees control1 is not None
            assert pp.control1 is not None
            cx = pp.control1.x * scale
            cy = pp.control1.y * scale
            parts.append(f"Q {cx:.2f} {cy:.2f} {x:.2f} {y:.2f}")
        elif pp.is_cubic:
            # is_cubic guarantees both control points are not None
            assert pp.control1 is not None
            assert pp.control2 is not None
            c1x = pp.control1.x * scale
            c1y = pp.control1.y * scale
            c2x = pp.control2.x * scale
            c2y = pp.control2.y * scale
            parts.append(f"C {c1x:.2f} {c1y:.2f} {c2x:.2f} {c2y:.2f} {x:.2f} {y:.2f}")

    return " ".join(parts)


def _render_grid_overlay(dwg: svgwrite.Drawing, size: int) -> None:
    """Render 12x12 grid overlay. Internal helper - requires svgwrite."""
    cell = size / 12
    grid_group = dwg.g(id="grid", stroke="#cccccc", stroke_width=0.5)

    # Vertical lines
    for i in range(13):
        x = i * cell
        grid_group.add(dwg.line(start=(x, 0), end=(x, size)))

    # Horizontal lines
    for i in range(13):
        y = i * cell
        grid_group.add(dwg.line(start=(0, y), end=(size, y)))

    # Add coordinate labels
    for i in range(13):
        x = i * cell
        y = i * cell
        grid_group.add(
            dwg.text(
                str(i),
                insert=(x + 1, 8),
                font_size="6px",
                fill="#999999",
                font_family="sans-serif",
            )
        )
        if i > 0:
            grid_group.add(
                dwg.text(
                    str(i),
                    insert=(1, y + 6),
                    font_size="6px",
                    fill="#999999",
                    font_family="sans-serif",
                )
            )

    dwg.add(grid_group)


def _render_anchor_overlay(
    dwg: svgwrite.Drawing,
    elem: EvaluatedExpr,
    scale: float,
) -> None:
    """Render anchor point markers. Internal helper - requires svgwrite."""
    anchors_group = dwg.g(id="anchors")

    def collect_anchors(e: EvaluatedExpr) -> list:
        if isinstance(e, (PositionedElement, ComposedElement)):
            return e.anchors
        return []

    anchors = collect_anchors(elem)
    for anchor in anchors:
        x = anchor.position.x * scale
        y = anchor.position.y * scale

        # Anchor marker: small circle with label
        anchors_group.add(
            dwg.circle(
                center=(x, y),
                r=2,
                fill="#ff0000",
                stroke="none",
            )
        )
        anchors_group.add(
            dwg.text(
                anchor.name,
                insert=(x + 3, y - 2),
                font_size="5px",
                fill="#ff0000",
                font_family="sans-serif",
            )
        )

    dwg.add(anchors_group)


def _render_zone_overlay(
    dwg: svgwrite.Drawing,
    size: int,
    metrics: dict[str, int],
) -> None:
    """Render zone background colors based on metrics. Internal helper - requires svgwrite."""
    scale = size / 12
    zones_group = dwg.g(id="zones")

    # Define zones by their y-ranges
    zone_ranges = [
        ("diacritic-above", metrics.get("cap-top", 0), metrics.get("cap-height", 2)),
        ("cap", metrics.get("cap-top", 0), metrics.get("baseline", 8)),
        ("ascender", metrics.get("ascender", 1), metrics.get("baseline", 8)),
        ("x-height", metrics.get("x-top", 4), metrics.get("baseline", 8)),
        ("descender", metrics.get("x-top", 4), metrics.get("descender", 10)),
        ("diacritic-below", metrics.get("baseline", 8) + 1, metrics.get("desc-limit", 12)),
    ]

    for zone_name, y_min, y_max in zone_ranges:
        if y_max <= y_min:
            continue
        color = ZONE_COLORS.get(zone_name, "#eeeeee")
        zones_group.add(
            dwg.rect(
                insert=(0, y_min * scale),
                size=(size, (y_max - y_min) * scale),
                fill=color,
                fill_opacity=0.3,
            )
        )

    dwg.add(zones_group)


def render_character_svg(
    char: str,
    evaluated: EvaluatedExpr,
    size: int,
    show_grid: bool = False,
    show_anchors: bool = False,
    show_zones: bool = False,
    metrics: dict[str, int] | None = None,
) -> str:
    """Render a character to SVG string.

    Args:
        char: Character literal
        evaluated: Evaluated geometry for the character
        size: SVG viewBox size (width and height)
        show_grid: Whether to overlay 12x12 grid
        show_anchors: Whether to mark anchor points
        show_zones: Whether to color-code zones
        metrics: Metrics dict for zone overlay

    Returns:
        SVG content as string
    """
    import svgwrite  # type: ignore[import-untyped]

    dwg = svgwrite.Drawing(
        filename=f"{char}.svg",
        size=(f"{size}px", f"{size}px"),
        viewBox=f"0 0 {size} {size}",
    )

    scale = size / 12.0

    # Background
    dwg.add(dwg.rect(insert=(0, 0), size=(size, size), fill="white"))

    # Zone overlay (behind everything)
    if show_zones and metrics:
        _render_zone_overlay(dwg, size, metrics)

    # Grid overlay
    if show_grid:
        _render_grid_overlay(dwg, size)

    # Main glyph group
    glyph_group = dwg.g(id=f"glyph-{char}")
    _render_element_to_svg(evaluated, dwg, glyph_group, scale)
    dwg.add(glyph_group)

    # Anchor overlay (on top)
    if show_anchors:
        _render_anchor_overlay(dwg, evaluated, scale)

    return str(dwg.tostring())


def main(argv: list[str] | None = None) -> None:
    """Main entry point for lsdl-render command."""
    parser = argparse.ArgumentParser(
        prog="lsdl-render",
        description="Render LSDL glyphs to SVG output",
        epilog="Output: One SVG file per character (A.svg, b.svg, etc.)",
    )
    parser.add_argument(
        "file",
        type=Path,
        help="LSDL file to render",
    )
    parser.add_argument(
        "characters",
        nargs="*",
        help="Characters to render (default: none unless --all)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("."),
        help="Output directory (default: current directory)",
    )
    parser.add_argument(
        "--size",
        type=_positive_int,
        default=120,
        help="SVG viewBox size in pixels (default: 120)",
    )
    parser.add_argument(
        "--show-grid",
        action="store_true",
        help="Overlay 12x12 grid",
    )
    parser.add_argument(
        "--show-anchors",
        action="store_true",
        help="Mark anchor points",
    )
    parser.add_argument(
        "--show-zones",
        action="store_true",
        help="Color-code vertical zones",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        dest="render_all",
        help="Render all characters in file",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {get_version()}",
    )

    args = parser.parse_args(argv)

    # Check for optional svgwrite dependency
    try:
        import svgwrite  # noqa: F401
    except ImportError:
        print(
            "lsdl-render requires svgwrite. Install with: pip install lsdl[render]",
            file=sys.stderr,
        )
        sys.exit(1)

    # Validate arguments
    if not args.render_all and not args.characters:
        print(
            "lsdl-render: specify characters to render, or use --all",
            file=sys.stderr,
        )
        sys.exit(1)

    # Parse LSDL file
    try:
        lsdl_file = parse_file(args.file)
    except ParseError as e:
        print(f"lsdl-render: parse error: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"lsdl-render: file not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    # Determine which characters to render
    if args.render_all:
        chars_to_render = list(lsdl_file.characters.keys())
    else:
        chars_to_render = args.characters
        # Validate requested characters exist
        missing = [c for c in chars_to_render if c not in lsdl_file.characters]
        if missing:
            print(
                f"lsdl-render: characters not defined: {', '.join(missing)}",
                file=sys.stderr,
            )
            sys.exit(1)

    if not chars_to_render:
        print("lsdl-render: no characters to render", file=sys.stderr)
        return

    # Evaluate all characters
    # Import here to avoid circular import at module level
    from lsdl.evaluator import EvaluationError

    try:
        evaluated = evaluate(lsdl_file)
    except EvaluationError as e:
        print(f"lsdl-render: evaluation error: {e}", file=sys.stderr)
        sys.exit(1)

    # Create output directory if needed
    args.output.mkdir(parents=True, exist_ok=True)

    # Get metrics for zone overlay
    metrics = lsdl_file.metrics.as_dict() if args.show_zones else None

    # Render each character
    rendered_count = 0
    for char in chars_to_render:
        if char not in evaluated:
            print(f"lsdl-render: warning: could not evaluate '{char}'", file=sys.stderr)
            continue

        svg_content = render_character_svg(
            char=char,
            evaluated=evaluated[char],
            size=args.size,
            show_grid=args.show_grid,
            show_anchors=args.show_anchors,
            show_zones=args.show_zones,
            metrics=metrics,
        )

        # Generate safe filename
        filename = _safe_filename(char) + ".svg"
        output_path = args.output / filename

        output_path.write_text(svg_content, encoding="utf-8")
        print(f"Rendered: {output_path}")
        rendered_count += 1

    print(f"Done: {rendered_count} character(s) rendered")


def _safe_filename(char: str) -> str:
    """Generate safe filename from character.

    Uses character directly for ASCII alphanumerics, Unicode codepoint for others.
    Multi-character strings (e.g., ligatures, combining sequences) are converted
    to underscore-separated codepoints.
    """
    if len(char) == 0:
        return "empty"

    parts = []
    for c in char:
        cp = ord(c)
        # Use character directly for safe ASCII (letters, digits)
        if c.isalnum() and cp < 128:
            parts.append(c)
        else:
            # Use U+XXXX format for other characters
            parts.append(f"U+{cp:04X}")

    return "_".join(parts)


def _positive_int(value: str) -> int:
    """Argparse type validator for positive integers."""
    try:
        ivalue = int(value)
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"invalid int value: '{value}'") from e
    if ivalue <= 0:
        raise argparse.ArgumentTypeError(f"--size must be positive, got {ivalue}")
    return ivalue


if __name__ == "__main__":
    main()
