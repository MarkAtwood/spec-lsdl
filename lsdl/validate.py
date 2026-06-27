"""LSDL Validator (Stub)

Validates LSDL documents for semantic correctness beyond parsing.

STATUS: This module is a stub for future implementation. The validate()
function raises NotImplementedError until semantic validation logic is
implemented per LSDL spec Section 13 (Semantic Constraints).

The type definitions (Severity, ValidationIssue, ValidationError) are
complete and usable; only the validate() function body is unimplemented.
"""

from __future__ import annotations

# Only export types that are usable; ValidationError is internal until validate() works
__all__ = ["Severity", "ValidationIssue", "validate"]

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lsdl.model import LSDLFile


class Severity(Enum):
    """Severity level for validation issues."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """A single validation issue."""

    severity: Severity
    message: str
    location: str = ""
    code: str = ""

    def __str__(self) -> str:
        prefix = f"[{self.code}] " if self.code else ""
        loc = f"{self.location}: " if self.location else ""
        return f"{self.severity.value}: {loc}{prefix}{self.message}"


class ValidationError(Exception):
    """Raised when validation fails with errors."""

    def __init__(self, issues: list[ValidationIssue]):
        self.issues = issues
        errors = [i for i in issues if i.severity == Severity.ERROR]
        super().__init__(f"Validation failed with {len(errors)} error(s)")


def validate(doc: LSDLFile, strict: bool = False) -> list[ValidationIssue]:
    """Validate an LSDL document.

    **Stub**: This function is not yet implemented and always raises
    NotImplementedError. See LSDL spec Section 13 for planned semantics.

    Args:
        doc: The document to validate
        strict: If True, treat warnings as errors

    Returns:
        List of validation issues (may be empty if valid)

    Raises:
        NotImplementedError: Always (stub implementation)
        ValidationError: If there are errors (or warnings in strict mode)
            [when implemented]
    """
    raise NotImplementedError("Semantic validation not yet implemented - see LSDL spec Section 13")
