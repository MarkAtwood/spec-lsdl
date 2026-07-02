"""Test that Unicode confusable characters produce comparable geometry.

Based on UTS #39 (Unicode Security Mechanisms) confusables.txt data.
Cross-script confusables (Latin/Greek/Cyrillic) that look identical
should ideally produce similar LSDL geometry.

Note: This is an INFORMATIONAL test. Characters defined independently
across scripts are not expected to have identical geometry - they just
need to look similar. The test reports coverage and structural differences.
"""

import json
from pathlib import Path

import pytest

from lsdl.evaluator import (
    BoundingBox,
    ComposedElement,
    EvaluatedExpr,
    PositionedElement,
    PositionedPathPoint,
    evaluate,
)
from lsdl.parser import parse

PROJECT_ROOT = Path(__file__).parent.parent
LIB_DIR = PROJECT_ROOT / "lib"
TOOLS_DIR = PROJECT_ROOT / "tools"
HOMOGLYPH_MAP = TOOLS_DIR / "homoglyph-map.json"

TOLERANCE = 1e-6


def coords_equal(a: float, b: float) -> bool:
    return abs(a - b) < TOLERANCE


def bbox_equal(a: BoundingBox, b: BoundingBox) -> bool:
    return (
        coords_equal(a.x_min, b.x_min)
        and coords_equal(a.y_min, b.y_min)
        and coords_equal(a.x_max, b.x_max)
        and coords_equal(a.y_max, b.y_max)
    )


def path_point_equal(a: PositionedPathPoint, b: PositionedPathPoint) -> bool:
    if not coords_equal(a.endpoint.x, b.endpoint.x):
        return False
    if not coords_equal(a.endpoint.y, b.endpoint.y):
        return False
    if (a.control1 is None) != (b.control1 is None):
        return False
    if a.control1 and b.control1:
        if not coords_equal(a.control1.x, b.control1.x):
            return False
        if not coords_equal(a.control1.y, b.control1.y):
            return False
    if (a.control2 is None) != (b.control2 is None):
        return False
    if a.control2 and b.control2:
        if not coords_equal(a.control2.x, b.control2.x):
            return False
        if not coords_equal(a.control2.y, b.control2.y):
            return False
    return True


def geometry_equal(a: EvaluatedExpr, b: EvaluatedExpr) -> tuple[bool, str]:
    """Compare two evaluated expressions for identical geometry."""
    if type(a) != type(b):
        return False, f"type mismatch: {type(a).__name__} vs {type(b).__name__}"

    if not bbox_equal(a.bbox, b.bbox):
        return False, f"bbox mismatch"

    if isinstance(a, PositionedElement) and isinstance(b, PositionedElement):
        if len(a.path_points) != len(b.path_points):
            return False, f"path count: {len(a.path_points)} vs {len(b.path_points)}"
        for i, (pa, pb) in enumerate(zip(a.path_points, b.path_points)):
            if not path_point_equal(pa, pb):
                return False, f"path point {i} differs"
        if a.close != b.close:
            return False, f"close differs"
        return True, ""

    if isinstance(a, ComposedElement) and isinstance(b, ComposedElement):
        if a.operator != b.operator:
            return False, f"operator: {a.operator} vs {b.operator}"
        if len(a.children) != len(b.children):
            return False, f"child count: {len(a.children)} vs {len(b.children)}"
        for i, (ca, cb) in enumerate(zip(a.children, b.children)):
            eq, diff = geometry_equal(ca, cb)
            if not eq:
                return False, f"child {i}: {diff}"
        return True, ""

    return False, "unknown type"


def load_all_lsdl_files() -> dict[str, EvaluatedExpr]:
    """Load and evaluate all lib/*.lsdl files, return char->geometry map."""
    all_chars: dict[str, EvaluatedExpr] = {}

    for lsdl_file in sorted(LIB_DIR.glob("*.lsdl")):
        try:
            source = lsdl_file.read_text()
            parsed = parse(source, filename=str(lsdl_file))
            evaluated = evaluate(parsed)
            all_chars.update(evaluated)
        except Exception:
            pass  # Skip files that fail to parse

    return all_chars


def load_confusable_groups() -> list[dict]:
    """Load homoglyph-map.json (from Unicode confusables.txt)."""
    if not HOMOGLYPH_MAP.exists():
        return []

    with open(HOMOGLYPH_MAP) as f:
        data = json.load(f)

    return data.get("groups", [])


class TestConfusableGeometry:
    """Test Unicode confusable character geometry."""

    @pytest.fixture(scope="class")
    def char_geometries(self) -> dict[str, EvaluatedExpr]:
        return load_all_lsdl_files()

    @pytest.fixture(scope="class")
    def confusable_groups(self) -> list[dict]:
        return load_confusable_groups()

    def test_confusables_map_exists(self):
        """Verify homoglyph-map.json exists."""
        assert HOMOGLYPH_MAP.exists(), f"Missing {HOMOGLYPH_MAP}"

    def test_confusable_coverage_report(
        self, char_geometries: dict[str, EvaluatedExpr], confusable_groups: list[dict]
    ):
        """Report coverage of Unicode confusables in LSDL."""
        if not confusable_groups:
            pytest.skip("No confusable groups defined")

        total_groups = len(confusable_groups)
        covered_groups = 0
        total_pairs = 0
        matching_pairs = 0
        mismatching_pairs = 0

        for group in confusable_groups:
            members = group.get("members", [])
            defined_members = []

            for m in members:
                char = m.get("char", "")
                if len(char) == 1 and char in char_geometries:
                    defined_members.append((char, m.get("script")))

            if len(defined_members) < 2:
                continue  # Need at least 2 to compare

            covered_groups += 1

            # Compare all pairs within the group
            for i, (char_a, script_a) in enumerate(defined_members):
                for char_b, script_b in defined_members[i + 1 :]:
                    if script_a == script_b:
                        continue  # Only compare cross-script
                    total_pairs += 1
                    geom_a = char_geometries[char_a]
                    geom_b = char_geometries[char_b]
                    is_equal, _ = geometry_equal(geom_a, geom_b)
                    if is_equal:
                        matching_pairs += 1
                    else:
                        mismatching_pairs += 1

        # Report results
        print(f"\n{'=' * 60}")
        print("UNICODE CONFUSABLES GEOMETRY REPORT")
        print(f"{'=' * 60}")
        print(f"Confusable groups in map:     {total_groups}")
        print(f"Groups with 2+ LSDL chars:    {covered_groups}")
        print(f"Cross-script pairs compared:  {total_pairs}")
        print(f"Geometrically identical:      {matching_pairs}")
        print(f"Structurally different:       {mismatching_pairs}")
        if total_pairs > 0:
            pct = matching_pairs / total_pairs * 100
            print(f"Match rate:                   {pct:.1f}%")
        print(f"{'=' * 60}\n")

        # This test always passes - it's informational
        # Characters defined independently aren't expected to match


def test_confusables_sample():
    """Show sample of confusable pairs and their geometry match status."""
    char_geometries = load_all_lsdl_files()
    groups = load_confusable_groups()

    if not groups:
        pytest.skip("No confusable groups")

    print("\n" + "=" * 70)
    print("SAMPLE CONFUSABLE PAIRS")
    print("=" * 70)
    print(f"{'Char A':8} {'Char B':8} {'Scripts':25} {'Match'}")
    print("-" * 70)

    shown = 0
    for group in groups:
        members = group.get("members", [])
        defined = [
            (m["char"], m["script"])
            for m in members
            if len(m.get("char", "")) == 1 and m["char"] in char_geometries
        ]

        for i, (char_a, script_a) in enumerate(defined):
            for char_b, script_b in defined[i + 1 :]:
                if script_a == script_b:
                    continue
                if shown >= 20:
                    continue

                geom_a = char_geometries.get(char_a)
                geom_b = char_geometries.get(char_b)
                if geom_a and geom_b:
                    is_equal, diff = geometry_equal(geom_a, geom_b)
                    status = "✓ identical" if is_equal else f"✗ {diff[:20]}"
                    print(
                        f"{char_a} U+{ord(char_a):04X}  {char_b} U+{ord(char_b):04X}  "
                        f"{script_a:10}->{script_b:10}  {status}"
                    )
                    shown += 1

    print("=" * 70)
