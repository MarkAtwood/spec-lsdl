#!/usr/bin/env python3
"""
Generate LSDL definitions from Unicode decomposition data.

Reads the unicode-manifest.json and generates DIA/DIA2 compositions for
characters that have Unicode canonical decompositions and whose base
character and diacritic marks are already defined in LSDL.

Usage:
    python3 tools/generate_from_ucd.py --block="Latin-1 Supplement"
    python3 tools/generate_from_ucd.py --block="Latin Extended-A" --output=lib/latin-ext-a-gen.lsdl
    python3 tools/generate_from_ucd.py --status=todo  # All todo characters with decompositions
"""

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
LIB_DIR = PROJECT_ROOT / "lib"
TOOLS_DIR = PROJECT_ROOT / "tools"
MANIFEST_PATH = TOOLS_DIR / "unicode-manifest.json"


# Mapping from Unicode combining mark names to LSDL element names
# This maps the "short name" extracted from Unicode names like
# "COMBINING GRAVE ACCENT" -> "grave accent" to the LSDL element name
COMBINING_MARK_TO_LSDL = {
    # Above marks
    "grave accent": "grave",
    "acute accent": "acute",
    "circumflex accent": "circumflex",
    "tilde": "tilde",
    "macron": "macron",
    "overline": "overline",
    "breve": "breve",
    "dot above": "dot-above",
    "diaeresis": "diaeresis",
    "hook above": "hook-above",
    "ring above": "ring",
    "double acute accent": "double-acute",
    "caron": "caron",
    "vertical line above": "vertical-line-above",
    "double vertical line above": "double-vertical-line-above",
    "double grave accent": "double-grave",
    "candrabindu": "candrabindu",
    "inverted breve": "inverted-breve",
    "turned comma above": "turned-comma-above",
    "comma above": "comma-above",
    "reversed comma above": "reversed-comma-above",
    "comma above right": "comma-above-right",
    "left angle above": "left-angle-above",
    "horn": "horn",
    "bridge above": "bridge-above",
    "not tilde above": "not-tilde-above",
    "homothetic above": "homothetic-above",
    "almost equal to above": "almost-equal-above",
    "right arrowhead above": "right-arrowhead-above",
    "left half ring above": "left-half-ring-above",
    "fermata": "fermata",
    "right half ring above": "right-half-ring-above",
    "dot above right": "dot-above-right",
    "zigzag above": "zigzag-above",
    "x above": "x-above",
    "vertical tilde": "vertical-tilde",
    "double overline": "double-overline",
    "grave tone mark": "grave-tone-mark",
    "acute tone mark": "acute-tone-mark",
    "greek perispomeni": "greek-perispomeni",
    "greek koronis": "greek-koronis",
    "greek dialytika tonos": "greek-dialytika-tonos",
    # Below marks
    "grave accent below": "grave-below",
    "acute accent below": "acute-below",
    "left tack below": "left-tack-below",
    "right tack below": "right-tack-below",
    "left half ring below": "left-half-ring-below",
    "up tack below": "up-tack-below",
    "down tack below": "down-tack-below",
    "plus sign below": "plus-sign-below",
    "minus sign below": "minus-sign-below",
    "palatalized hook below": "palatalized-hook-below",
    "retroflex hook below": "retroflex-hook-below",
    "dot below": "dot-below",
    "diaeresis below": "diaeresis-below",
    "ring below": "ring-below",
    "comma below": "comma-below",
    "cedilla": "cedilla",
    "ogonek": "ogonek",
    "vertical line below": "vertical-line-below",
    "bridge below": "bridge-below",
    "inverted double arch below": "inverted-double-arch-below",
    "caron below": "caron-below",
    "circumflex accent below": "circumflex-below",
    "breve below": "breve-below",
    "inverted breve below": "inverted-breve-below",
    "tilde below": "tilde-below",
    "macron below": "macron-below",
    "low line": "line-below",
    "double low line": "double-line-below",
    "right half ring below": "right-half-ring-below",
    "inverted bridge below": "inverted-bridge-below",
    "square below": "square-below",
    "seagull below": "seagull-below",
    "equals sign below": "equals-sign-below",
    "double vertical line below": "double-vertical-line-below",
    "left angle below": "left-angle-below",
    "left right arrow below": "left-right-arrow-below",
    "upwards arrow below": "upwards-arrow-below",
    "x below": "x-below",
    "left arrowhead below": "left-arrowhead-below",
    "right arrowhead below": "right-arrowhead-below",
    "right arrowhead and up arrowhead below": "right-arrowhead-up-arrowhead-below",
    "asterisk below": "asterisk-below",
    "double ring below": "double-ring-below",
    "greek ypogegrammeni": "greek-ypogegrammeni",
    # Overlay/through marks
    "tilde overlay": "tilde-overlay",
    "short stroke overlay": "stroke",
    "long stroke overlay": "stroke-long",
    "short solidus overlay": "oblique-stroke",
    "long solidus overlay": "stroke.diag",
    # Double marks (span two characters)
    "double breve below": "double-breve-below",
    "double breve": "double-breve",
    "double macron": "double-macron",
    "double macron below": "double-macron-below",
    "double tilde": "double-tilde",
    "double inverted breve": "double-inverted-breve",
    "double rightwards arrow below": "double-rightwards-arrow-below",
}


def load_manifest() -> dict:
    """Load the unicode-manifest.json file."""
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        return json.load(f)


def extract_defined_base_chars(lib_dir: Path) -> set:
    """
    Extract all base characters defined in LSDL files.
    Returns set of single characters (e.g., 'A', 'a', etc.)
    """
    defined = set()

    for lsdl_file in lib_dir.glob("*.lsdl"):
        content = lsdl_file.read_text(encoding="utf-8")

        for line in content.split('\n'):
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('@'):
                continue

            # Match character definitions: CHAR  NAME = definition
            match = re.match(r'^(.)\s+([A-Z][A-Z0-9\-]+)\s*=', line)
            if match:
                char = match.group(1)
                defined.add(char)

    return defined


def extract_defined_diacritics(lib_dir: Path) -> set:
    """
    Extract all diacritic element names from diacritics.lsdl.
    Returns set of element names (e.g., 'grave', 'acute', etc.)
    """
    defined = set()
    diacritics_file = lib_dir / "diacritics.lsdl"

    if not diacritics_file.exists():
        return defined

    content = diacritics_file.read_text(encoding="utf-8")

    for line in content.split('\n'):
        line = line.strip()
        # Match @elem declarations
        match = re.match(r'^@elem\s+(\S+)', line)
        if match:
            defined.add(match.group(1))

    return defined


def get_combining_mark_name(codepoint: int) -> str | None:
    """
    Get the short name for a combining mark.
    E.g., U+0300 COMBINING GRAVE ACCENT -> "grave accent"
    """
    try:
        name = unicodedata.name(chr(codepoint))
        if name.startswith("COMBINING "):
            return name[len("COMBINING "):].lower()
    except ValueError:
        pass
    return None


def decompose_character(char: str) -> tuple[str, list[str]] | None:
    """
    Fully decompose a character to its base letter and list of combining marks.
    Returns (base_char, [mark1, mark2, ...]) or None if not decomposable.

    Handles recursive decomposition for characters like Ḉ which decomposes to
    Ç + acute, and Ç decomposes to C + cedilla.
    """
    decomp = unicodedata.decomposition(char)
    if not decomp:
        return None

    # Parse decomposition string
    parts = decomp.split()

    # Filter out compatibility tags like <compat>, <font>, etc.
    hex_parts = [p for p in parts if not p.startswith('<')]

    if not hex_parts:
        return None

    # First part is the base
    base_cp = int(hex_parts[0], 16)
    base_char = chr(base_cp)

    # Remaining parts are combining marks
    marks = []
    for hex_cp in hex_parts[1:]:
        cp = int(hex_cp, 16)
        mark_name = get_combining_mark_name(cp)
        if mark_name:
            marks.append(mark_name)
        else:
            # Not a combining mark we recognize
            return None

    # Check if base itself has a decomposition (recursive)
    base_decomp = decompose_character(base_char)
    if base_decomp:
        # Insert base's marks before our marks
        ultimate_base, base_marks = base_decomp
        return (ultimate_base, base_marks + marks)

    return (base_char, marks)


def unicode_name_to_lsdl_name(unicode_name: str) -> str:
    """
    Convert Unicode character name to LSDL name format.
    E.g., "LATIN CAPITAL LETTER A WITH GRAVE" -> "LATIN-CAPITAL-A-GRAVE"
    """
    # Remove common filler words and convert to dashes
    name = unicode_name.upper()
    # Remove "LETTER" and "WITH"
    name = name.replace(" LETTER ", " ")
    name = name.replace(" WITH ", "-")
    # Replace remaining spaces with dashes
    name = name.replace(" ", "-")
    return name


def infer_script(char: str, unicode_name: str) -> str:
    """Infer the script code from the character name."""
    name_upper = unicode_name.upper()
    if "LATIN" in name_upper:
        return "Latn"
    elif "GREEK" in name_upper:
        return "Grek"
    elif "CYRILLIC" in name_upper:
        return "Cyrl"
    elif "COPTIC" in name_upper:
        return "Copt"
    else:
        return "Zyyy"  # Common/Unknown


def generate_lsdl_definition(
    char: str,
    unicode_name: str,
    base_char: str,
    marks: list[str],
    defined_bases: set,
    defined_diacritics: set,
) -> tuple[str, str | None]:
    """
    Generate an LSDL definition for a character.

    Returns (definition_line, error_message).
    If successful, error_message is None.
    If not generatable, definition_line is empty and error_message explains why.
    """
    # Check if base character is defined
    if base_char not in defined_bases:
        return ("", f"base character '{base_char}' not defined in LSDL")

    # Map Unicode mark names to LSDL element names
    lsdl_marks = []
    for mark in marks:
        lsdl_mark = COMBINING_MARK_TO_LSDL.get(mark)
        if not lsdl_mark:
            return ("", f"unknown combining mark '{mark}'")
        if lsdl_mark not in defined_diacritics:
            return ("", f"diacritic '{lsdl_mark}' not defined in diacritics.lsdl")
        lsdl_marks.append(lsdl_mark)

    # Generate the definition
    lsdl_name = unicode_name_to_lsdl_name(unicode_name)
    script = infer_script(char, unicode_name)

    if len(lsdl_marks) == 1:
        # Single diacritic: DIA(base, mark)
        definition = f"DIA({base_char}, {lsdl_marks[0]})"
    elif len(lsdl_marks) == 2:
        # Double diacritic: DIA2(base, mark1, mark2)
        definition = f"DIA2({base_char}, {lsdl_marks[0]}, {lsdl_marks[1]})"
    else:
        return ("", f"unsupported number of marks ({len(lsdl_marks)})")

    line = f"{char}  {lsdl_name} = {definition} script:{script}"
    return (line, None)


def generate_for_block(
    manifest: dict,
    block_name: str,
    status_filter: str | None,
    defined_bases: set,
    defined_diacritics: set,
) -> tuple[list[str], list[str]]:
    """
    Generate LSDL definitions for a specific block.

    Returns (definitions, warnings).
    """
    definitions = []
    warnings = []

    for block in manifest["blocks"]:
        if block["name"] != block_name:
            continue

        for char_entry in block["characters"]:
            # Apply status filter if specified
            if status_filter and char_entry["lsdl_status"] != status_filter:
                continue

            # Skip if no decomposition
            if not char_entry["decomposition"]:
                continue

            char = char_entry["char"]
            unicode_name = char_entry["name"]

            # Decompose the character
            decomp = decompose_character(char)
            if not decomp:
                warnings.append(f"{char} ({unicode_name}): could not decompose")
                continue

            base_char, marks = decomp

            # Generate definition
            definition, error = generate_lsdl_definition(
                char, unicode_name, base_char, marks,
                defined_bases, defined_diacritics
            )

            if error:
                warnings.append(f"{char} ({unicode_name}): {error}")
            else:
                definitions.append(definition)

    return definitions, warnings


def generate_all_todo(
    manifest: dict,
    defined_bases: set,
    defined_diacritics: set,
) -> tuple[list[str], list[str]]:
    """
    Generate LSDL definitions for all 'todo' characters with decompositions.

    Returns (definitions, warnings).
    """
    definitions = []
    warnings = []

    for block in manifest["blocks"]:
        block_defs, block_warnings = generate_for_block(
            manifest, block["name"], "todo",
            defined_bases, defined_diacritics
        )
        definitions.extend(block_defs)
        warnings.extend(block_warnings)

    return definitions, warnings


def format_output(definitions: list[str], block_name: str | None = None) -> str:
    """Format definitions with header."""
    lines = ["@lsdl 1.0", ""]

    if block_name:
        lines.append(f"# Generated from Unicode decomposition data: {block_name}")
    else:
        lines.append("# Generated from Unicode decomposition data")
    lines.append("")

    lines.extend(definitions)
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate LSDL definitions from Unicode decomposition data"
    )
    parser.add_argument(
        "--block",
        help="Unicode block name to process (e.g., 'Latin-1 Supplement')"
    )
    parser.add_argument(
        "--status",
        choices=["todo", "done", "all"],
        default=None,
        help="Filter by LSDL status (default: all)"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file path (default: stdout)"
    )
    parser.add_argument(
        "--list-blocks",
        action="store_true",
        help="List available block names and exit"
    )
    parser.add_argument(
        "--warnings", "-w",
        action="store_true",
        help="Show warnings for characters that couldn't be generated"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be generated without writing"
    )

    args = parser.parse_args()

    # Load manifest
    manifest = load_manifest()

    # List blocks if requested
    if args.list_blocks:
        print("Available blocks:")
        for block in manifest["blocks"]:
            count = len(block["characters"])
            todo_count = sum(1 for c in block["characters"] if c["lsdl_status"] == "todo")
            print(f"  {block['name']}: {count} chars ({todo_count} todo)")
        return 0

    # Load defined elements
    defined_bases = extract_defined_base_chars(LIB_DIR)
    defined_diacritics = extract_defined_diacritics(LIB_DIR)

    # Generate definitions
    if args.block:
        # Check block exists
        block_names = [b["name"] for b in manifest["blocks"]]
        if args.block not in block_names:
            print(f"Error: Unknown block '{args.block}'", file=sys.stderr)
            print(f"Available blocks: {', '.join(block_names)}", file=sys.stderr)
            return 1

        definitions, warnings = generate_for_block(
            manifest, args.block, args.status,
            defined_bases, defined_diacritics
        )
        output = format_output(definitions, args.block)

    elif args.status == "todo":
        # Generate all todo characters
        definitions, warnings = generate_all_todo(
            manifest, defined_bases, defined_diacritics
        )
        output = format_output(definitions, "all todo characters")

    else:
        print("Error: Must specify --block or --status=todo", file=sys.stderr)
        return 1

    # Show warnings if requested
    if args.warnings and warnings:
        print(f"# Warnings ({len(warnings)} characters skipped):", file=sys.stderr)
        for warning in warnings:
            print(f"#   {warning}", file=sys.stderr)
        print(file=sys.stderr)

    # Output
    if args.dry_run:
        print(f"Would generate {len(definitions)} definitions")
        if args.output:
            print(f"Would write to: {args.output}")
        return 0

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output)
        print(f"Generated {len(definitions)} definitions to {args.output}")
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
