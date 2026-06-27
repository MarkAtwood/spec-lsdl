"""LSDL Validate CLI

Command-line tool to validate LSDL files.

Usage:
    lsdl-validate [OPTIONS] FILE...
    lsdl-validate -              # Read from stdin

Options:
    -q, --quiet     Only output errors
    --json          Output as JSON
    --strict        Treat warnings as errors
    --version       Show version
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

from lsdl.cli import get_version
from lsdl.evaluator import EvaluationError
from lsdl.parser import ParseError, parse
from lsdl.validate import Severity, ValidationIssue

__all__ = ["main"]


@dataclass
class ValidationResult:
    """Result of validating a single file.

    This is distinct from ValidationIssue: ValidationResult aggregates all issues
    for a single file, while ValidationIssue represents an individual problem.
    """

    path: str
    valid: bool
    errors: list[ValidationIssue]
    warnings: list[ValidationIssue]


def format_error_line(
    path: str,
    line: int,
    col: int,
    level: str,
    message: str,
    source_line: str | None = None,
) -> str:
    """Format an error/warning in GCC-style format.

    Example:
        file.lsdl:42:15: error: undefined element 'bogus'
          A LATIN-CAPITAL-A = STACK(bogus, stem)
                                    ^^^^^
    """
    result = f"{path}:{line}:{col}: {level}: {message}"
    if source_line is not None:
        result += f"\n  {source_line.rstrip()}"
        # Add caret pointer
        if col > 0:
            result += f"\n  {' ' * (col - 1)}^"
    return result


def get_source_line(source: str, line_num: int) -> str | None:
    """Get a specific line from source text (1-indexed)."""
    lines = source.split("\n")
    if 1 <= line_num <= len(lines):
        return lines[line_num - 1]
    return None


def validate_source(
    source: str,
    path: str,
    quiet: bool = False,
    output: TextIO | None = None,
) -> ValidationResult:
    """Validate LSDL source text.

    Args:
        source: LSDL source code
        path: Path for error messages
        quiet: If True, suppress non-error output
        output: File to write output to (defaults to stderr)

    Returns:
        ValidationResult with errors and warnings
    """
    if output is None:
        output = sys.stderr

    errors: list[ValidationIssue] = []
    warnings: list[ValidationIssue] = []

    try:
        parse(source, filename=path)
    except (ParseError, EvaluationError) as e:
        code = "parse-error" if isinstance(e, ParseError) else "evaluation-error"
        issue = ValidationIssue(
            severity=Severity.ERROR,
            message=e.message,
            location=f"{path}:{e.line}:{e.col}",
            code=code,
        )
        errors.append(issue)

        source_line = get_source_line(source, e.line)
        msg = format_error_line(path, e.line, e.col, "error", e.message, source_line)
        print(msg, file=output)

    return ValidationResult(
        path=path,
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


def validate_file(
    path: Path,
    quiet: bool = False,
    output: TextIO | None = None,
) -> ValidationResult:
    """Validate an LSDL file.

    Args:
        path: Path to the .lsdl file
        quiet: If True, suppress non-error output
        output: File to write output to (defaults to stderr)

    Returns:
        ValidationResult with errors and warnings
    """
    if output is None:
        output = sys.stderr

    errors: list[ValidationIssue] = []
    warnings: list[ValidationIssue] = []
    path_str = str(path)

    try:
        source = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        errors.append(
            ValidationIssue(
                severity=Severity.ERROR,
                message="file not found",
                location=path_str,
                code="file-not-found",
            )
        )
        print(f"{path_str}: error: file not found", file=output)
        return ValidationResult(path=path_str, valid=False, errors=errors, warnings=warnings)
    except PermissionError:
        errors.append(
            ValidationIssue(
                severity=Severity.ERROR,
                message="permission denied",
                location=path_str,
                code="permission-denied",
            )
        )
        print(f"{path_str}: error: permission denied", file=output)
        return ValidationResult(path=path_str, valid=False, errors=errors, warnings=warnings)
    except UnicodeDecodeError as e:
        errors.append(
            ValidationIssue(
                severity=Severity.ERROR,
                message=f"invalid UTF-8: {e}",
                location=path_str,
                code="encoding-error",
            )
        )
        print(f"{path_str}: error: invalid UTF-8 encoding", file=output)
        return ValidationResult(path=path_str, valid=False, errors=errors, warnings=warnings)

    return validate_source(source, path_str, quiet=quiet, output=output)


def main(argv: list[str] | None = None) -> None:
    """Main entry point for lsdl-validate command."""
    parser = argparse.ArgumentParser(
        prog="lsdl-validate",
        description="Validate LSDL files for syntax and semantic correctness",
    )
    parser.add_argument(
        "files",
        nargs="+",
        help="LSDL file(s) to validate, or '-' for stdin",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Only output errors, not warnings",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output results as JSON",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {get_version()}",
    )

    args = parser.parse_args(argv)

    results: list[ValidationResult] = []
    has_errors = False
    has_warnings = False

    # In JSON mode, suppress human-readable error output by writing to a
    # StringIO null sink; structured errors are emitted via JSON at the end.
    import io

    output: TextIO = io.StringIO() if args.json_output else sys.stderr

    for file_arg in args.files:
        if file_arg == "-":
            # Read from stdin
            source = sys.stdin.read()
            result = validate_source(source, "<stdin>", quiet=args.quiet, output=output)
        else:
            path = Path(file_arg)
            result = validate_file(path, quiet=args.quiet, output=output)

        results.append(result)
        if result.errors:
            has_errors = True
        if result.warnings:
            has_warnings = True

    # JSON output mode
    if args.json_output:

        def issue_to_dict(issue: ValidationIssue) -> dict:
            """Convert ValidationIssue to JSON-serializable dict."""
            return {
                "severity": issue.severity.value,
                "message": issue.message,
                "location": issue.location,
                "code": issue.code,
            }

        output_data = {
            "files": [
                {
                    "path": r.path,
                    "valid": r.valid,
                    "errors": [issue_to_dict(e) for e in r.errors],
                    "warnings": [issue_to_dict(w) for w in r.warnings],
                }
                for r in results
            ],
            "summary": {
                "total_files": len(results),
                "valid_files": sum(1 for r in results if r.valid),
                "total_errors": sum(len(r.errors) for r in results),
                "total_warnings": sum(len(r.warnings) for r in results),
            },
        }
        print(json.dumps(output_data, indent=2))

    # Exit code: 1 if errors, 1 if warnings and --strict
    if has_errors:
        sys.exit(1)
    if has_warnings and args.strict:
        sys.exit(1)


if __name__ == "__main__":
    main()
