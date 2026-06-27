"""LSDL Dump CLI

Debug/inspection tool to parse and dump LSDL file structure.

Usage:
    lsdl-dump [options] <file.lsdl>

Options:
    --format=tree|json|table  Output format (default: tree)
    --elements               Show only elements
    --characters             Show only characters
    --stats                  Show summary statistics
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from lsdl.cli import get_version
from lsdl.model import (
    CharacterDefinition,
    ComposeExpr,
    ElementDefinition,
    Expr,
    LSDLError,
    LSDLFile,
    RefExpr,
    TransformExpr,
    WildcardExpr,
)
from lsdl.parser import ParseError, parse_file

__all__ = ["main"]


def main(argv: list[str] | None = None) -> None:
    """Main entry point for lsdl-dump command."""
    parser = argparse.ArgumentParser(
        prog="lsdl-dump",
        description="Parse LSDL file and dump its structure",
    )
    parser.add_argument(
        "file",
        type=Path,
        help="LSDL file to parse",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["tree", "json", "table"],
        default="tree",
        help="Output format (default: tree)",
    )
    parser.add_argument(
        "--elements",
        action="store_true",
        help="Show only elements",
    )
    parser.add_argument(
        "--characters",
        action="store_true",
        help="Show only characters",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show summary statistics",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {get_version()}",
    )

    args = parser.parse_args(argv)

    # Validate file exists
    if not args.file.exists():
        print(f"lsdl-dump: error: file not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    # Parse the file
    try:
        doc = parse_file(args.file)
    except ParseError as e:
        print(f"lsdl-dump: parse error: {e}", file=sys.stderr)
        sys.exit(1)
    except LSDLError as e:
        print(f"lsdl-dump: error: {e}", file=sys.stderr)
        sys.exit(1)

    # Output based on format and filters
    if args.stats:
        _dump_stats(doc, args.file)
    elif args.format == "json":
        _dump_json(doc, args)
    elif args.format == "table":
        _dump_table(doc, args)
    else:  # tree (default)
        _dump_tree(doc, args)


# =============================================================================
# Tree Format
# =============================================================================


def _dump_tree(doc: LSDLFile, args: argparse.Namespace) -> None:
    """Dump document in tree format."""
    # Version
    print(f"@lsdl {doc.version[0]}.{doc.version[1]}")

    # Metrics
    if not args.elements and not args.characters:
        print("@metrics")
        for name, value in doc.metrics.as_dict().items():
            print(f"  {name}: {value}")

    # Elements
    if not args.characters:
        elems = list(doc.elements.values())
        if elems:
            print(f"Elements ({len(elems)}):")
            for elem in elems:
                _dump_element_tree(elem)

    # Characters
    if not args.elements:
        chars = list(doc.characters.values())
        if chars:
            print(f"Characters ({len(chars)}):")
            for char_def in chars:
                _dump_character_tree(char_def)

    # Aliases (if showing everything)
    if not args.elements and not args.characters and doc.aliases:
        print(f"Aliases ({len(doc.aliases)}):")
        for alias in doc.aliases.values():
            qual = f"{alias.script_qualifier}:" if alias.script_qualifier else ""
            print(f"  {qual}{alias.name} = {alias.target}")

    # Case mappings (if showing everything)
    if not args.elements and not args.characters and doc.case_mappings:
        print(f"Case Mappings ({len(doc.case_mappings)}):")
        for cm in doc.case_mappings:
            final = f" final:{cm.final}" if cm.final else ""
            print(f"  {cm.upper} <-> {cm.lower}{final}")

    # Styles (if showing everything)
    if not args.elements and not args.characters and doc.styles:
        print(f"Styles ({len(doc.styles)}):")
        for style in doc.styles.values():
            print(f"  {style.name}: {style.transform}")


def _dump_element_tree(elem: ElementDefinition) -> None:
    """Dump a single element in tree format."""
    zone_str = f"[{elem.zone.value}]" if elem.zone else ""
    anchors_str = ""
    if elem.anchors:
        anchor_names = [a.name for a in elem.anchors]
        anchors_str = f" anchors: {', '.join(anchor_names)}"

    if elem.is_expr_form:
        expr_str = _expr_to_str(elem.expression)
        print(f"  {elem.name} {zone_str} = {expr_str}{anchors_str}")
    else:
        print(f"  {elem.name} {zone_str}{anchors_str}")


def _dump_character_tree(char_def: CharacterDefinition) -> None:
    """Dump a single character in tree format."""
    if char_def.expression:
        expr_str = _expr_to_str(char_def.expression)
        print(f"  {char_def.char} {char_def.name} = {expr_str}")
    else:
        print(f"  {char_def.char} {char_def.name}")


def _expr_to_str(expr: Expr | None) -> str:
    """Convert expression to string."""
    if expr is None:
        return ""
    if isinstance(expr, RefExpr):
        return expr.name
    elif isinstance(expr, ComposeExpr):
        children = ", ".join(_expr_to_str(c) for c in expr.children)
        extras = []
        if expr.split:
            extras.append("/".join(str(s) for s in expr.split))
        if expr.anchor_override:
            extras.append(f"attach:{expr.anchor_override}")
        if expr.merge_strategy:
            extras.append(f"merge:{expr.merge_strategy}")
        if extras:
            children += ", " + ", ".join(extras)
        return f"{expr.op}({children})"
    elif isinstance(expr, TransformExpr):
        child = _expr_to_str(expr.child)
        params = ", ".join(f"{k}={v}" for k, v in expr.params.items())
        return f"{expr.op}({child}, {params})"
    elif isinstance(expr, WildcardExpr):
        return "*"
    return str(expr)


# =============================================================================
# JSON Format
# =============================================================================


def _dump_json(doc: LSDLFile, args: argparse.Namespace) -> None:
    """Dump document as JSON."""
    data: dict[str, Any] = {
        "version": f"{doc.version[0]}.{doc.version[1]}",
    }

    if not args.elements and not args.characters:
        data["metrics"] = doc.metrics.as_dict()

    if not args.characters:
        data["elements"] = {name: _element_to_dict(elem) for name, elem in doc.elements.items()}

    if not args.elements:
        data["characters"] = {
            char: _character_to_dict(char_def) for char, char_def in doc.characters.items()
        }

    if not args.elements and not args.characters:
        if doc.aliases:
            data["aliases"] = {
                name: {
                    "target": alias.target,
                    "script_qualifier": alias.script_qualifier,
                }
                for name, alias in doc.aliases.items()
            }

        if doc.case_mappings:
            data["case_mappings"] = [
                {
                    "upper": cm.upper,
                    "lower": cm.lower,
                    "final": cm.final,
                }
                for cm in doc.case_mappings
            ]

        if doc.styles:
            data["styles"] = {
                name: {
                    "transform": _expr_to_dict(style.transform),
                }
                for name, style in doc.styles.items()
            }

    print(json.dumps(data, indent=2, ensure_ascii=False))


def _element_to_dict(elem: ElementDefinition) -> dict[str, Any]:
    """Convert element to dictionary."""
    result: dict[str, Any] = {
        "name": elem.name,
        "grid": elem.grid,
    }

    if elem.zone:
        result["zone"] = elem.zone.value

    if elem.is_expr_form:
        result["expression"] = _expr_to_dict(elem.expression)
    else:
        if elem.path_ids:
            result["path"] = elem.path_ids
        if elem.path_points:
            result["path_points"] = {
                pid: _path_point_to_dict(pp) for pid, pp in elem.path_points.items()
            }
        result["close"] = elem.close
        result["width"] = elem.width

    if elem.anchors:
        result["anchors"] = {a.name: {"x": a.position.x, "y": a.position.y} for a in elem.anchors}

    if elem.metadata.script:
        result["script"] = elem.metadata.script
    if elem.metadata.ortho:
        result["ortho"] = elem.metadata.ortho
    if elem.metadata.block:
        result["block"] = elem.metadata.block
    if elem.metadata.cp:
        result["cp"] = elem.metadata.cp
    if elem.metadata.extensions:
        result["extensions"] = elem.metadata.extensions

    return result


def _character_to_dict(char_def: CharacterDefinition) -> dict[str, Any]:
    """Convert character definition to dictionary."""
    result: dict[str, Any] = {
        "char": char_def.char,
        "name": char_def.name,
    }

    if char_def.expression:
        result["expression"] = _expr_to_dict(char_def.expression)

    if char_def.is_path_form:
        if char_def.zone:
            result["zone"] = char_def.zone.value
        if char_def.path_ids:
            result["path"] = char_def.path_ids
        if char_def.path_points:
            result["path_points"] = {
                pid: _path_point_to_dict(pp) for pid, pp in char_def.path_points.items()
            }
        result["close"] = char_def.close
        result["width"] = char_def.width

    if char_def.anchors:
        result["anchors"] = {
            a.name: {"x": a.position.x, "y": a.position.y} for a in char_def.anchors
        }

    if char_def.metadata.script:
        result["script"] = char_def.metadata.script
    if char_def.metadata.ortho:
        result["ortho"] = char_def.metadata.ortho
    if char_def.metadata.cp:
        result["cp"] = char_def.metadata.cp
    if char_def.metadata.freq is not None:
        result["freq"] = char_def.metadata.freq

    return result


def _expr_to_dict(expr: Expr | None) -> dict[str, Any] | None:
    """Convert expression to dictionary."""
    if expr is None:
        return None

    if isinstance(expr, RefExpr):
        return {"type": "ref", "name": expr.name}
    elif isinstance(expr, ComposeExpr):
        result: dict[str, Any] = {
            "type": "compose",
            "op": expr.op,
            "children": [_expr_to_dict(c) for c in expr.children],
        }
        if expr.split:
            result["split"] = expr.split
        if expr.anchor_override:
            result["anchor_override"] = expr.anchor_override
        if expr.merge_strategy:
            result["merge_strategy"] = expr.merge_strategy
        return result
    elif isinstance(expr, TransformExpr):
        return {
            "type": "transform",
            "op": expr.op,
            "child": _expr_to_dict(expr.child),
            "params": expr.params,
        }
    elif isinstance(expr, WildcardExpr):
        return {"type": "wildcard"}

    return {"type": "unknown"}


def _path_point_to_dict(pp: Any) -> dict[str, Any]:
    """Convert path point to dictionary."""
    result: dict[str, Any] = {
        "endpoint": {"x": pp.endpoint.x, "y": pp.endpoint.y},
    }
    if pp.control1:
        result["control1"] = {"x": pp.control1.x, "y": pp.control1.y}
    if pp.control2:
        result["control2"] = {"x": pp.control2.x, "y": pp.control2.y}
    return result


# =============================================================================
# Table Format
# =============================================================================


def _dump_table(doc: LSDLFile, args: argparse.Namespace) -> None:
    """Dump document in table format."""
    if not args.characters:
        _dump_elements_table(doc)

    if not args.elements:
        if not args.characters and doc.elements:
            print()  # Blank line between tables
        _dump_characters_table(doc)


def _dump_elements_table(doc: LSDLFile) -> None:
    """Dump elements as table."""
    if not doc.elements:
        return

    # Calculate column widths
    name_width = max((len(e.name) for e in doc.elements.values()), default=0)
    name_width = max(name_width, 7)  # "Element"
    zone_width = max((len(e.zone.value) if e.zone else 0 for e in doc.elements.values()), default=4)
    zone_width = max(zone_width, 4)  # "Zone"

    # Header
    print(f"{'Element':<{name_width}}  {'Zone':<{zone_width}}  Grid  Form        Anchors")
    print("-" * (name_width + zone_width + 40))

    # Rows
    for elem in doc.elements.values():
        zone = elem.zone.value if elem.zone else "-"
        form = "expr" if elem.is_expr_form else "path"
        anchors = ", ".join(a.name for a in elem.anchors) if elem.anchors else "-"
        row = f"{elem.name:<{name_width}}  {zone:<{zone_width}}  {elem.grid:>4}  {form:<10}"
        print(f"{row}  {anchors}")


def _dump_characters_table(doc: LSDLFile) -> None:
    """Dump characters as table."""
    if not doc.characters:
        return

    # Calculate column widths
    name_width = max((len(c.name) for c in doc.characters.values()), default=0)
    name_width = max(name_width, 12)  # "Unicode Name"

    # Header
    print(f"Char  {'Unicode Name':<{name_width}}  Expression")
    print("-" * (name_width + 50))

    # Rows
    for char_def in doc.characters.values():
        expr_str = _expr_to_str(char_def.expression) if char_def.expression else "[path]"
        # Truncate long expressions
        if len(expr_str) > 60:
            expr_str = expr_str[:57] + "..."
        print(f"{char_def.char:>4}  {char_def.name:<{name_width}}  {expr_str}")


# =============================================================================
# Stats Format
# =============================================================================


def _dump_stats(doc: LSDLFile, filepath: Path) -> None:
    """Dump summary statistics."""
    print(f"File: {filepath}")
    print(f"Version: {doc.version[0]}.{doc.version[1]}")
    print(f"Elements: {len(doc.elements)}")
    print(f"Characters: {len(doc.characters)}")
    print(f"Aliases: {len(doc.aliases)}")
    print(f"Case Mappings: {len(doc.case_mappings)}")
    print(f"Styles: {len(doc.styles)}")

    # Element stats
    if doc.elements:
        path_form = sum(1 for e in doc.elements.values() if not e.is_expr_form)
        expr_form = sum(1 for e in doc.elements.values() if e.is_expr_form)
        grid_12 = sum(1 for e in doc.elements.values() if e.grid == 12)
        grid_24 = sum(1 for e in doc.elements.values() if e.grid == 24)
        print(f"  Path-form elements: {path_form}")
        print(f"  Expr-form elements: {expr_form}")
        print(f"  Grid 12: {grid_12}")
        print(f"  Grid 24: {grid_24}")

    # Character stats
    if doc.characters:
        with_expr = sum(1 for c in doc.characters.values() if c.expression)
        path_form = sum(1 for c in doc.characters.values() if c.is_path_form)
        print(f"  Expression-based characters: {with_expr}")
        print(f"  Path-form characters: {path_form}")

        # Script breakdown
        scripts: dict[str, int] = {}
        for c in doc.characters.values():
            script = c.metadata.script or "unspecified"
            scripts[script] = scripts.get(script, 0) + 1
        if scripts:
            print("  By script:")
            for script, count in sorted(scripts.items(), key=lambda x: -x[1]):
                print(f"    {script}: {count}")

    # Composition operator usage
    ops: dict[str, int] = {}
    for elem in doc.elements.values():
        if elem.expression:
            _count_ops(elem.expression, ops)
    for char_def in doc.characters.values():
        if char_def.expression:
            _count_ops(char_def.expression, ops)

    if ops:
        print("Composition operators:")
        for op, count in sorted(ops.items(), key=lambda x: -x[1]):
            print(f"  {op}: {count}")


def _count_ops(expr: Expr | None, counts: dict[str, int]) -> None:
    """Count composition operators in expression."""
    if expr is None:
        return
    if isinstance(expr, ComposeExpr):
        counts[expr.op] = counts.get(expr.op, 0) + 1
        for child in expr.children:
            _count_ops(child, counts)
    elif isinstance(expr, TransformExpr):
        counts[expr.op] = counts.get(expr.op, 0) + 1
        _count_ops(expr.child, counts)


if __name__ == "__main__":
    main()
