"""LSDL Command Line Interface

Entry points for lsdl-validate, lsdl-dump, and lsdl-render commands.
"""


def get_version() -> str:
    """Get the lsdl package version.

    Returns:
        Version string, or "unknown" if the package is not installed.
    """
    try:
        from lsdl import __version__

        return __version__
    except ImportError:
        return "unknown"
