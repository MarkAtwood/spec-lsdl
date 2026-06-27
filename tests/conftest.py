"""Pytest fixtures for LSDL tests.

Test vectors are expected in test-vectors/ directory. If this directory
does not exist, tests requiring vectors will be skipped gracefully.
"""

from pathlib import Path

import pytest

# Project root and test vector directories
PROJECT_ROOT = Path(__file__).parent.parent
TEST_VECTORS_DIR = PROJECT_ROOT / "test-vectors"
VALID_VECTORS_DIR = TEST_VECTORS_DIR / "valid"
INVALID_VECTORS_DIR = TEST_VECTORS_DIR / "invalid"

# Check if test vectors are available
TEST_VECTORS_AVAILABLE = TEST_VECTORS_DIR.is_dir()

# Skip reason for missing test vectors
SKIP_NO_VECTORS = pytest.mark.skipif(
    not TEST_VECTORS_AVAILABLE,
    reason=f"Test vectors directory not found: {TEST_VECTORS_DIR}. "
    "Ensure test-vectors/ is present (check git submodules if applicable).",
)


def _require_vectors_dir(path: Path, name: str) -> Path:
    """Return path if it exists, otherwise raise skip exception."""
    if not path.is_dir():
        pytest.skip(f"{name} directory not found: {path}")
    return path


@pytest.fixture
def valid_vectors_dir() -> Path:
    """Path to valid test vectors. Skips if directory doesn't exist."""
    return _require_vectors_dir(VALID_VECTORS_DIR, "Valid test vectors")


@pytest.fixture
def invalid_vectors_dir() -> Path:
    """Path to invalid test vectors. Skips if directory doesn't exist."""
    return _require_vectors_dir(INVALID_VECTORS_DIR, "Invalid test vectors")


@pytest.fixture
def minimal_lsdl_path() -> Path:
    """Path to minimal.lsdl test vector. Skips if not found."""
    _require_vectors_dir(VALID_VECTORS_DIR, "Valid test vectors")
    path = VALID_VECTORS_DIR / "minimal.lsdl"
    if not path.is_file():
        pytest.skip(f"minimal.lsdl not found: {path}")
    return path


@pytest.fixture
def minimal_lsdl_source() -> str:
    """Contents of minimal.lsdl test vector. Skips if not found."""
    _require_vectors_dir(VALID_VECTORS_DIR, "Valid test vectors")
    path = VALID_VECTORS_DIR / "minimal.lsdl"
    if not path.is_file():
        pytest.skip(f"minimal.lsdl not found: {path}")
    return path.read_text()


@pytest.fixture
def valid_lsdl_files() -> list[Path]:
    """List of all valid .lsdl test files. Skips if directory doesn't exist."""
    _require_vectors_dir(VALID_VECTORS_DIR, "Valid test vectors")
    return sorted(VALID_VECTORS_DIR.glob("*.lsdl"))


@pytest.fixture
def invalid_syntax_files() -> list[Path]:
    """List of all syntax error test files. Skips if directory doesn't exist."""
    syntax_dir = INVALID_VECTORS_DIR / "syntax"
    _require_vectors_dir(syntax_dir, "Syntax error test vectors")
    return sorted(syntax_dir.glob("*.lsdl"))


@pytest.fixture
def invalid_semantic_files() -> list[Path]:
    """List of all semantic error test files. Skips if directory doesn't exist."""
    semantic_dir = INVALID_VECTORS_DIR / "semantic"
    _require_vectors_dir(semantic_dir, "Semantic error test vectors")
    return sorted(semantic_dir.glob("*.lsdl"))


def collect_test_vectors() -> tuple[list[Path], list[Path], list[Path]]:
    """Collect all test vector paths for parametrized tests.

    Returns empty lists if directories don't exist, allowing pytest to
    skip parametrized tests gracefully rather than failing at collection.
    """
    if not TEST_VECTORS_DIR.is_dir():
        return [], [], []

    valid = []
    if VALID_VECTORS_DIR.is_dir():
        valid = sorted(VALID_VECTORS_DIR.glob("*.lsdl"))

    syntax = []
    syntax_dir = INVALID_VECTORS_DIR / "syntax"
    if syntax_dir.is_dir():
        syntax = sorted(syntax_dir.glob("*.lsdl"))

    semantic = []
    semantic_dir = INVALID_VECTORS_DIR / "semantic"
    if semantic_dir.is_dir():
        semantic = sorted(semantic_dir.glob("*.lsdl"))

    return valid, syntax, semantic


VALID_FILES, SYNTAX_ERROR_FILES, SEMANTIC_ERROR_FILES = collect_test_vectors()
