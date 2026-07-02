#!/usr/bin/env python3
"""LSDL Coverage Validation Tool

Validates LSDL character definitions against the Unicode manifest and checks
for parse errors, evaluation errors, case mapping completeness, and duplicates.

Usage:
    python3 tools/validate_coverage.py [--verbose]
"""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lsdl.parser import ParseError, parse_file
from lsdl.evaluator import EvaluationError, evaluate_character, EvaluationContext
from lsdl.model import LSDLFile


@dataclass
class BlockStats:
    """Coverage statistics for a single Unicode block."""
    name: str
    total: int = 0
    done: int = 0
    todo: int = 0
    errors: int = 0


@dataclass
class ValidationResult:
    """Complete validation results."""
    # Per-block coverage stats
    block_stats: list[BlockStats] = field(default_factory=list)

    # Parse errors: list of (filename, error_message)
    parse_errors: list[tuple[str, str]] = field(default_factory=list)

    # Evaluation errors: list of (char, error_message)
    eval_errors: list[tuple[str, str]] = field(default_factory=list)

    # Missing case mappings: list of (upper, lower, which_missing)
    missing_case_mappings: list[tuple[str, str, str]] = field(default_factory=list)

    # Duplicate definitions: list of (char, file1, file2)
    duplicates: list[tuple[str, str, str]] = field(default_factory=list)

    # Characters defined in files
    defined_chars: dict[str, str] = field(default_factory=dict)  # char -> filename

    # All case mappings found
    case_mappings: list[tuple[str, str]] = field(default_factory=list)  # (upper, lower)


def load_manifest(manifest_path: Path) -> dict[str, Any]:
    """Load the Unicode manifest JSON file."""
    with open(manifest_path) as f:
        return json.load(f)


def parse_all_lsdl_files(lib_dir: Path, verbose: bool = False) -> tuple[dict[str, LSDLFile], list[tuple[str, str]]]:
    """Parse all LSDL files in lib directory.

    Returns:
        Tuple of (parsed_files dict, parse_errors list)
    """
    parsed_files: dict[str, LSDLFile] = {}
    parse_errors: list[tuple[str, str]] = []

    lsdl_files = sorted(lib_dir.glob("*.lsdl"))

    for lsdl_file in lsdl_files:
        if verbose:
            print(f"  Parsing {lsdl_file.name}...")
        try:
            parsed = parse_file(lsdl_file)
            parsed_files[lsdl_file.name] = parsed
        except ParseError as e:
            # Collect all errors from the exception
            for err in e.errors:
                error_msg = f"{err.filename}:{err.line}:{err.col}: {err.message}"
                parse_errors.append((lsdl_file.name, error_msg))

    return parsed_files, parse_errors


def collect_definitions(
    parsed_files: dict[str, LSDLFile]
) -> tuple[dict[str, str], list[tuple[str, str, str]], list[tuple[str, str]]]:
    """Collect all character definitions and case mappings from parsed files.

    Returns:
        Tuple of (defined_chars, duplicates, case_mappings)
        - defined_chars: char -> filename mapping
        - duplicates: list of (char, file1, file2) tuples
        - case_mappings: list of (upper, lower) tuples
    """
    defined_chars: dict[str, str] = {}
    duplicates: list[tuple[str, str, str]] = []
    case_mappings: list[tuple[str, str]] = []

    for filename, lsdl_file in parsed_files.items():
        # Collect character definitions
        for char in lsdl_file.characters:
            if char in defined_chars:
                duplicates.append((char, defined_chars[char], filename))
            else:
                defined_chars[char] = filename

        # Collect case mappings
        for case_map in lsdl_file.case_mappings:
            case_mappings.append((case_map.upper, case_map.lower))

    return defined_chars, duplicates, case_mappings


def check_case_mappings(
    case_mappings: list[tuple[str, str]],
    defined_chars: dict[str, str]
) -> list[tuple[str, str, str]]:
    """Check that both characters in each case mapping are defined.

    Returns:
        List of (upper, lower, which_missing) tuples for incomplete mappings
    """
    missing: list[tuple[str, str, str]] = []

    for upper, lower in case_mappings:
        upper_defined = upper in defined_chars
        lower_defined = lower in defined_chars

        if not upper_defined and not lower_defined:
            missing.append((upper, lower, "both"))
        elif not upper_defined:
            missing.append((upper, lower, "upper"))
        elif not lower_defined:
            missing.append((upper, lower, "lower"))

    return missing


def evaluate_all_characters(
    parsed_files: dict[str, LSDLFile],
    verbose: bool = False
) -> list[tuple[str, str]]:
    """Attempt to evaluate all character definitions.

    Returns:
        List of (char, error_message) tuples for evaluation errors
    """
    eval_errors: list[tuple[str, str]] = []

    # Suppress placeholder warnings during validation
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)

        for filename, lsdl_file in parsed_files.items():
            ctx = EvaluationContext(file=lsdl_file, metrics=lsdl_file.metrics)

            for char, char_def in lsdl_file.characters.items():
                try:
                    evaluate_character(char_def, ctx)
                except EvaluationError as e:
                    error_msg = f"{filename}:{e.line}:{e.col}: {e.message}"
                    eval_errors.append((char, error_msg))
                except Exception as e:
                    # Catch any other unexpected errors
                    error_msg = f"{filename}: {type(e).__name__}: {e}"
                    eval_errors.append((char, error_msg))

    return eval_errors


def compute_block_stats(
    manifest: dict[str, Any],
    defined_chars: dict[str, str]
) -> list[BlockStats]:
    """Compute coverage statistics per Unicode block."""
    block_stats: list[BlockStats] = []

    for block in manifest["blocks"]:
        stats = BlockStats(name=block["name"])

        for char_info in block["characters"]:
            stats.total += 1
            char = char_info["char"]

            if char in defined_chars:
                stats.done += 1
            else:
                stats.todo += 1

        block_stats.append(stats)

    return block_stats


def print_report(result: ValidationResult, verbose: bool = False) -> None:
    """Print the validation report."""
    print("\n" + "=" * 70)
    print("LSDL COVERAGE VALIDATION REPORT")
    print("=" * 70)

    # Summary
    total_chars = sum(b.total for b in result.block_stats)
    total_done = sum(b.done for b in result.block_stats)
    total_todo = sum(b.todo for b in result.block_stats)
    coverage_pct = (total_done / total_chars * 100) if total_chars > 0 else 0

    print(f"\nOVERALL COVERAGE: {total_done}/{total_chars} ({coverage_pct:.1f}%)")
    print(f"  Done: {total_done}")
    print(f"  Todo: {total_todo}")

    # Per-block stats
    print("\n" + "-" * 70)
    print("COVERAGE BY BLOCK")
    print("-" * 70)
    print(f"{'Block':<40} {'Done':>8} {'Todo':>8} {'Total':>8} {'%':>7}")
    print("-" * 70)

    for block in result.block_stats:
        pct = (block.done / block.total * 100) if block.total > 0 else 0
        print(f"{block.name:<40} {block.done:>8} {block.todo:>8} {block.total:>8} {pct:>6.1f}%")

    # Parse errors
    if result.parse_errors:
        print("\n" + "-" * 70)
        print(f"PARSE ERRORS ({len(result.parse_errors)})")
        print("-" * 70)
        for filename, error in result.parse_errors:
            print(f"  {error}")
    else:
        print("\n[OK] No parse errors")

    # Evaluation errors
    if result.eval_errors:
        print("\n" + "-" * 70)
        print(f"EVALUATION ERRORS ({len(result.eval_errors)})")
        print("-" * 70)
        for char, error in result.eval_errors:
            print(f"  '{char}': {error}")
    else:
        print("\n[OK] No evaluation errors")

    # Missing case mappings
    if result.missing_case_mappings:
        print("\n" + "-" * 70)
        print(f"MISSING CASE MAPPING CHARACTERS ({len(result.missing_case_mappings)})")
        print("-" * 70)
        for upper, lower, which in result.missing_case_mappings:
            if which == "both":
                print(f"  @case {upper} {lower}: both characters undefined")
            elif which == "upper":
                print(f"  @case {upper} {lower}: uppercase '{upper}' undefined")
            else:
                print(f"  @case {upper} {lower}: lowercase '{lower}' undefined")
    else:
        print("\n[OK] All case mapping characters are defined")

    # Duplicates
    if result.duplicates:
        print("\n" + "-" * 70)
        print(f"DUPLICATE DEFINITIONS ({len(result.duplicates)})")
        print("-" * 70)
        for char, file1, file2 in result.duplicates:
            print(f"  '{char}': defined in {file1} and {file2}")
    else:
        print("\n[OK] No duplicate definitions")

    # Verbose: list defined chars per file
    if verbose:
        print("\n" + "-" * 70)
        print("CHARACTERS DEFINED PER FILE")
        print("-" * 70)

        # Group by file
        file_chars: dict[str, list[str]] = {}
        for char, filename in result.defined_chars.items():
            if filename not in file_chars:
                file_chars[filename] = []
            file_chars[filename].append(char)

        for filename in sorted(file_chars.keys()):
            chars = file_chars[filename]
            print(f"\n{filename} ({len(chars)} characters):")
            # Show first 50 chars, truncate if more
            char_preview = "".join(sorted(chars)[:50])
            if len(chars) > 50:
                char_preview += f"... (+{len(chars) - 50} more)"
            print(f"  {char_preview}")

    print("\n" + "=" * 70)

    # Exit status summary
    issues = len(result.parse_errors) + len(result.eval_errors) + \
             len(result.missing_case_mappings) + len(result.duplicates)

    if issues > 0:
        print(f"VALIDATION FAILED: {issues} issue(s) found")
    else:
        print("VALIDATION PASSED")


def validate(manifest_path: Path, lib_dir: Path, verbose: bool = False) -> ValidationResult:
    """Run full validation and return results."""
    result = ValidationResult()

    # Load manifest
    if verbose:
        print("Loading Unicode manifest...")
    manifest = load_manifest(manifest_path)

    # Parse all LSDL files
    if verbose:
        print("\nParsing LSDL files...")
    parsed_files, result.parse_errors = parse_all_lsdl_files(lib_dir, verbose)

    # Collect definitions
    if verbose:
        print("\nCollecting definitions...")
    result.defined_chars, result.duplicates, result.case_mappings = \
        collect_definitions(parsed_files)

    # Check case mappings
    if verbose:
        print("Checking case mappings...")
    result.missing_case_mappings = check_case_mappings(
        result.case_mappings, result.defined_chars
    )

    # Evaluate all characters
    if verbose:
        print("Evaluating character definitions...")
    result.eval_errors = evaluate_all_characters(parsed_files, verbose)

    # Compute block stats
    if verbose:
        print("Computing coverage statistics...")
    result.block_stats = compute_block_stats(manifest, result.defined_chars)

    return result


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate LSDL character definitions against Unicode manifest"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed progress and per-file character lists"
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(__file__).parent / "unicode-manifest.json",
        help="Path to unicode-manifest.json (default: tools/unicode-manifest.json)"
    )
    parser.add_argument(
        "--lib-dir",
        type=Path,
        default=Path(__file__).parent.parent / "lib",
        help="Path to lib directory containing .lsdl files (default: lib/)"
    )

    args = parser.parse_args()

    # Validate paths
    if not args.manifest.exists():
        print(f"Error: Manifest not found: {args.manifest}", file=sys.stderr)
        return 1

    if not args.lib_dir.exists():
        print(f"Error: Library directory not found: {args.lib_dir}", file=sys.stderr)
        return 1

    # Run validation
    result = validate(args.manifest, args.lib_dir, args.verbose)

    # Print report
    print_report(result, args.verbose)

    # Return exit code: 0 if no issues, 1 if any issues
    issues = len(result.parse_errors) + len(result.eval_errors) + \
             len(result.missing_case_mappings) + len(result.duplicates)

    return 0 if issues == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
