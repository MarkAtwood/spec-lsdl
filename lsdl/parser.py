"""LSDL Parser

Level 1 conformant parser for Latin Script Description Language.
Validates syntax and all 23 semantic constraints from Section 12.9.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from lsdl.model import (
    FULL_ELEMENT_REGISTRY,
    AliasDefinition,
    Anchor,
    CaseMapping,
    CharacterDefinition,
    ComposeExpr,
    Coordinate,
    ElementDefinition,
    ErrorExpr,
    Expr,
    LSDLError,
    LSDLFile,
    Metadata,
    Metrics,
    PathPoint,
    RefExpr,
    StyleDefinition,
    TransformExpr,
    WildcardExpr,
    Zone,
)

# Public API - Parser class and _tokenize are internal implementation details
__all__ = ["parse", "parse_file", "parse_string", "ParseError"]


# =============================================================================
# Lexer
# =============================================================================

# Token patterns for the LSDL lexer, compiled into a single regex with named groups.
#
# Performance notes on alternation order:
# - Python's re module tries alternations left-to-right until one matches
# - Patterns are ordered by expected frequency in typical LSDL files:
#   1. Whitespace/comments (WS, NL, COMMENT) - skipped early
#   2. Keywords (@lsdl, @elem, etc.) - common structural tokens
#   3. Field names (zone:, path:, etc.) - frequent in blocks
#   4. Operators and punctuation - common delimiters
#   5. Literals (COORD, INT, etc.) - frequent values
#   6. Names (TAG, UNAME, NAME) - identifiers
#   7. LITERAL_CHAR - rare, catch-all for Unicode characters
#
# This ordering keeps average match attempts low: for typical tokens (keywords,
# names, coordinates), matches succeed within the first ~10 alternations.
# LITERAL_CHAR is intentionally last since it's a fallback for rare literal
# characters in inline definitions.
#
# If profiling shows tokenization as a bottleneck, consider:
# - Two-stage lexer with character-class dispatch
# - Reordering based on measured token frequency
# For now, the current order is adequate for typical LSDL file sizes.
TOKEN_PATTERNS = [
    ("COMMENT", r"#[^\n]*"),
    ("NL", r"\n"),
    ("WS", r"[ \t]+"),
    # Keywords
    ("KEYWORD", r"@lsdl|@metrics|@elem|@char|@alias|@case|@style|@end"),
    ("BLOCK_FIELD", r"zone:|path:|close:|width:|anchors:|build:|transform:"),
    # Meta fields - x-* extension fields, but NOT x-top or x-height (those are metric/zone names)
    ("META_FIELD", r"script:|ortho:|block:|cp:|freq:|x-(?!top|height)[a-z]+:"),
    ("FROM_EXPR", r"from_expr"),
    ("ATTACH", r"attach:"),
    ("MERGE", r"merge:"),
    ("FINAL", r"final:"),
    # Operators
    ("COMPOSE_OP", r"STACK|LR3|LR|DIA2|DIA|OVR|FRAME|LIG|APEX"),
    ("XFORM_OP", r"sc(?=\()|sh(?=\()|sk(?=\()"),
    ("XFORM_PARAM", r"sx=|sy=|dx=|dy=|kx=|ky="),
    # Punctuation (MUST come before LITERAL_CHAR which includes ASCII range)
    ("LPAREN", r"\("),
    ("RPAREN", r"\)"),
    ("COMMA", r","),
    ("EQUALS", r"="),
    ("COLON", r":"),
    ("WILDCARD", r"\*"),
    # Literals
    ("GRID_SPEC", r"/24|/12"),
    ("CODEPOINT", r"U\+[0-9A-Fa-f]{4,6}"),
    ("COORD", r"\[[0-9]+,[0-9]+\]"),
    ("SPLIT", r"[0-9]+(?:/[0-9]+)+"),
    ("INT", r"-?[0-9]+"),
    ("BOOL", r"true|false"),
    ("CURVE", r"C\("),
    # Names
    # Script/lang tags (title case like Latn, Grek, Fra) - must come before UNAME
    ("TAG", r"[A-Z][a-z]{2,}"),
    # Unicode character name (all uppercase, at least 2 chars)
    ("UNAME", r"[A-Z][A-Z0-9-]+"),
    # General name pattern - handles zone names, metric names, element names, anchor names
    # Parser uses context to determine semantics
    # Allows: lowercase start, alphanumerics, hyphens, underscores, dots for variants
    ("NAME", r"[a-z][a-z0-9_]*(?:-[a-z0-9_]+)*(?:\.[a-z][a-z0-9_]*)*"),
    # Literal Unicode character per LSDL spec Section 12.2 Lexical Productions.
    # Ranges match the Unicode blocks relevant to Latin-script fonts:
    #   !-~        U+0021-U+007E  Basic Latin (ASCII printable, excl. space/DEL)
    #   \xa0-ɏ    U+00A0-U+024F  Latin-1 Supplement, Latin Extended-A/B
    #   Ͱ-ԯ       U+0370-U+052F  Greek and Coptic, Cyrillic, Cyrillic Supplement
    #   ᪰-᫿       U+1AB0-U+1AFF  Combining Diacritical Marks Extended
    #   ᲀ-᲏       U+1C80-U+1C8F  Cyrillic Extended-C
    #   ᷀-᷿       U+1DC0-U+1DFF  Combining Diacritical Marks Supplement
    #   Ḁ-ỿ       U+1E00-U+1EFF  Latin Extended Additional
    #   ἀ-῿       U+1F00-U+1FFF  Greek Extended
    #   Ⱡ-Ɀ       U+2C60-U+2C7F  Latin Extended-C
    #   ⷠ-ⷿ       U+2DE0-U+2DFF  Cyrillic Extended-A
    #   Ꙁ-ꟿ       U+A640-U+A7FF  Cyrillic Extended-B, Latin Extended-D
    #   ꬰ-꭯       U+AB30-U+AB6F  Latin Extended-E
    #   ﬀ-ﬆ       U+FB00-U+FB06  Alphabetic Presentation Forms (ligatures)
    #   ⃐-⃿       U+20D0-U+20FF  Combining Diacritical Marks for Symbols
    #   (SMP)     U+1E030-1E08F  Cyrillic Extended-D (requires \U escape)
    (
        "LITERAL_CHAR",
        r"[!-~ -ɏͰ-ԯ᪰-᫿"
        r"ᲀ-᲏᷀-᷿Ḁ-ỿἀ-῿"
        r"Ⱡ-Ɀⷠ-ⷿꙀ-ꟿꬰ-꭯"
        r"ﬀ-ﬆ⃐-⃿]"
        r"|[\U0001E030-\U0001E08F]",
    ),
]

TOKEN_RE = re.compile("|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_PATTERNS))


@dataclass
class Token:
    type: str
    value: str
    line: int
    col: int


def _tokenize(text: str) -> list[Token]:
    """Tokenize LSDL source text (internal implementation detail)."""
    tokens = []
    line, col = 1, 1
    pos = 0
    while pos < len(text):
        match = TOKEN_RE.match(text, pos)
        if match:
            kind = match.lastgroup
            assert kind is not None  # lastgroup is set when match succeeds with named groups
            value = match.group()
            if kind == "NL":
                tokens.append(Token(kind, value, line, col))
                line += 1
                col = 1
            elif kind == "WS" or kind == "COMMENT":
                col += len(value)
            else:
                tokens.append(Token(kind, value, line, col))
                col += len(value)
            pos = match.end()
        else:
            # Unknown character - include it as error token
            tokens.append(Token("ERROR", text[pos], line, col))
            col += 1
            pos += 1
    return tokens


# =============================================================================
# Parser Error
# =============================================================================


class ParseError(LSDLError):
    """Raised when parsing fails due to syntax or semantic errors.

    Inherits from LSDLError for uniform exception handling.

    Attributes:
        message: Description of the error.
        line: 1-indexed line number where the error occurred.
            A value of 0 indicates the error is not associated with a
            specific source location (e.g., unexpected end of input,
            cycle detection during semantic analysis).
        col: 1-indexed column number where the error occurred.
            A value of 0 indicates the error is not associated with a
            specific source location.
        filename: Source filename for error messages, defaults to "<string>".
        errors: List of all ParseError instances collected during parsing.
            When multiple errors are detected, the first error is raised but
            all errors are accessible via this attribute. For a single error,
            this list contains only the raised error itself.
    """

    def __init__(
        self,
        message: str,
        line: int = 0,
        col: int = 0,
        filename: str = "<string>",
        errors: list[ParseError] | None = None,
    ):
        super().__init__(message, line, col, filename)
        # If errors list provided, use it; otherwise this error is the only one
        self.errors: list[ParseError] = errors if errors is not None else [self]


# =============================================================================
# Parser
# =============================================================================


class Parser:
    """LSDL Level 1 Parser with semantic validation.

    This class is an internal implementation detail. External code should use
    the public API functions instead:

    - parse(source, filename) - parse LSDL source text
    - parse_file(path) - parse an LSDL file from disk
    - parse_string(source, filename) - alias for parse()
    """

    def __init__(self, tokens: list[Token], filename: str = "<string>"):
        self.tokens = tokens
        self.filename = filename
        self.pos = 0
        self.errors: list[ParseError] = []
        # Track definitions for semantic validation
        self.defined_elements: dict[str, int] = {}  # name -> line
        self.defined_chars: dict[str, int] = {}  # char -> line
        self.defined_aliases: dict[str, int] = {}  # name -> line
        self.defined_styles: dict[str, int] = {}  # name -> line
        self.case_uppers: set[str] = set()
        self.case_lowers: set[str] = set()
        # For cycle detection
        self.element_refs: dict[str, set[str]] = {}
        # Allow wildcards only in @style blocks
        self.in_style_block = False

    def current(self) -> Token | None:
        """Get current token, skipping whitespace."""
        while self.pos < len(self.tokens) and self.tokens[self.pos].type == "WS":
            self.pos += 1
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def peek(self, offset: int = 0) -> Token | None:
        """Peek at token with offset from current position.

        Returns the token at `offset` positions from current. Since the lexer
        discards whitespace tokens, this simply advances by `offset` positions
        in the token stream.

        Args:
            offset: Number of tokens to look ahead (0 = current token)

        Returns:
            Token at the offset position, or None if out of bounds.
        """
        p = self.pos + offset
        return self.tokens[p] if p < len(self.tokens) else None

    def _check(self, *types: str) -> Token | None:
        """Return current token if it matches any of the given types, else None.

        This helper enables type-safe one-liner checks like:
            if tok := self._check("KEYWORD"):
                # tok is guaranteed to be Token, not Token | None
        """
        tok = self.current()
        if tok is not None and tok.type in types:
            return tok
        return None

    def _check_kw(self, keyword: str) -> Token | None:
        """Return current token if it's a KEYWORD with the given value, else None."""
        tok = self.current()
        if tok is not None and tok.type == "KEYWORD" and tok.value == keyword:
            return tok
        return None

    def _check_val(self, value: str) -> Token | None:
        """Return current token if it has the given value, else None."""
        tok = self.current()
        if tok is not None and tok.value == value:
            return tok
        return None

    def _at_end_kw(self) -> bool:
        """Check if current token is '@end' keyword."""
        tok = self.current()
        return tok is not None and tok.type == "KEYWORD" and tok.value == "@end"

    # Human-readable descriptions for token types used in error messages
    TOKEN_DESCRIPTIONS: dict[str, str] = {
        "KEYWORD": "keyword (@lsdl, @elem, @char, etc.)",
        "BLOCK_FIELD": "block field (zone:, path:, anchors:, etc.)",
        "META_FIELD": "metadata field (script:, cp:, freq:, etc.)",
        "COMPOSE_OP": "composition operator (STACK, LR, DIA, etc.)",
        "XFORM_OP": "transform operator (sc, sh, sk)",
        "XFORM_PARAM": "transform parameter (sx=, sy=, dx=, dy=, kx=, ky=)",
        "LPAREN": "'('",
        "RPAREN": "')'",
        "COMMA": "','",
        "EQUALS": "'='",
        "COLON": "':'",
        "WILDCARD": "'*' (wildcard)",
        "GRID_SPEC": "grid specifier (/12 or /24)",
        "CODEPOINT": "Unicode codepoint (U+XXXX)",
        "COORD": "coordinate ([x,y])",
        "SPLIT": "split ratio (e.g., 4/8)",
        "INT": "integer",
        "BOOL": "boolean (true or false)",
        "CURVE": "curve (C(...))",
        "TAG": "script/language tag (e.g., Latn, Grek)",
        "UNAME": "Unicode character name (e.g., LATIN-SMALL-A)",
        "NAME": "identifier",
        "LITERAL_CHAR": "literal character",
        "NL": "newline",
        "ERROR": "unknown character",
    }

    def _describe_token(self, tok: Token | None, include_value: bool = True) -> str:
        """Return a human-readable description of a token for error messages."""
        if tok is None:
            return "end of input"
        desc = self.TOKEN_DESCRIPTIONS.get(tok.type, tok.type)
        if include_value and tok.type not in ("NL", "WS"):
            return f"{desc} ({tok.value!r})"
        return desc

    def _describe_expected(self, expected_type: str) -> str:
        """Return a human-readable description of an expected token type."""
        return self.TOKEN_DESCRIPTIONS.get(expected_type, expected_type)

    def consume(self, expected_type: str | None = None) -> Token:
        """Consume and return current token."""
        tok = self.current()
        if tok is None:
            raise self.error("unexpected end of input")
        if expected_type and tok.type != expected_type:
            expected_desc = self._describe_expected(expected_type)
            got_desc = self._describe_token(tok)
            raise self.error(f"expected {expected_desc}, got {got_desc}", tok)
        self.pos += 1
        return tok

    def skip_blank_lines(self) -> None:
        """Skip consecutive newline tokens; WS and comments are already discarded by current()."""
        tok = self.current()
        while tok is not None and tok.type == "NL":
            self.pos += 1
            tok = self.current()

    def error(self, msg: str, tok: Token | None = None) -> ParseError:
        """Create a parse error."""
        t = tok or self.current()
        line, col = (t.line, t.col) if t else (0, 0)
        return ParseError(msg, line, col, self.filename)

    def add_error(self, msg: str, tok: Token | None = None) -> None:
        """Record an error and continue parsing."""
        self.errors.append(self.error(msg, tok))

    # -------------------------------------------------------------------------
    # Top-level parsing
    # -------------------------------------------------------------------------

    def parse(self) -> LSDLFile:
        """Parse complete LSDL file."""
        result = LSDLFile()
        self.skip_blank_lines()

        # Optional @lsdl version declaration
        if self._check_kw("@lsdl"):
            result.version = self.parse_version_decl()
            self.skip_blank_lines()

        # Optional @metrics block (must come before definitions)
        if self._check_kw("@metrics"):
            result.metrics = self.parse_metrics_block()
            self.skip_blank_lines()

        # Definitions
        while (tok := self.current()) is not None:
            self.skip_blank_lines()
            tok = self.current()
            if tok is None:
                break
            if tok.type == "KEYWORD":
                if tok.value == "@elem":
                    elem = self.parse_elem_block()
                    if elem:
                        if elem.name in self.defined_elements:
                            # Last definition wins (Section 4.5)
                            pass
                        self.defined_elements[elem.name] = elem.line
                        result.elements[elem.name] = elem
                elif tok.value == "@char":
                    char_def = self.parse_char_block()
                    if char_def:
                        self.defined_chars[char_def.char] = char_def.line
                        result.characters[char_def.char] = char_def
                elif tok.value == "@alias":
                    alias = self.parse_alias()
                    if alias:
                        result.aliases[alias.name] = alias
                elif tok.value == "@case":
                    case_map = self.parse_case_mapping()
                    if case_map:
                        result.case_mappings.append(case_map)
                elif tok.value == "@style":
                    style = self.parse_style_block()
                    if style:
                        result.styles[style.name] = style
                elif tok.value == "@metrics":
                    self.add_error("@metrics must appear before any definition", tok)
                    self.skip_to_end_or_keyword()
                elif tok.value == "@end":
                    self.add_error("unexpected @end", tok)
                    self.pos += 1
                else:
                    self.add_error(f"unexpected keyword: {tok.value}", tok)
                    self.pos += 1
            elif tok.type == "LITERAL_CHAR":
                # Inline character definition
                char_def = self.parse_char_inline()
                if char_def:
                    self.defined_chars[char_def.char] = char_def.line
                    result.characters[char_def.char] = char_def
            elif tok.type == "NAME" and len(tok.value) == 1:
                # Single lowercase letter followed by UNAME = inline char definition
                peek1 = self.peek(1)
                if peek1 is not None and peek1.type == "UNAME":
                    char_def = self.parse_char_inline()
                    if char_def:
                        self.defined_chars[char_def.char] = char_def.line
                        result.characters[char_def.char] = char_def
                else:
                    self.add_error(
                        f"expected @elem, @char, @alias, @case, @style, "
                        f"or inline character definition, got {tok.value!r}",
                        tok,
                    )
                    self.pos += 1
            elif tok.type == "NL":
                self.pos += 1
            else:
                self.add_error(
                    f"expected @elem, @char, @alias, @case, @style, "
                    f"or inline character definition, got {tok.value!r}",
                    tok,
                )
                self.pos += 1
            self.skip_blank_lines()

        # Semantic validation
        self.validate_semantics(result)

        if self.errors:
            # Raise first error but include all errors for callers to access
            first = self.errors[0]
            raise ParseError(
                first.message, first.line, first.col, first.filename, errors=self.errors
            )

        return result

    def skip_to_end_or_keyword(self) -> None:
        """Skip tokens until @end or another keyword."""
        while (tok := self.current()) is not None:
            if tok.type == "KEYWORD":
                if tok.value == "@end":
                    self.pos += 1
                break
            self.pos += 1

    # -------------------------------------------------------------------------
    # Version and Metrics
    # -------------------------------------------------------------------------

    def parse_version_decl(self) -> tuple[int, int]:
        """Parse @lsdl 1.0 declaration.

        Expected format: @lsdl MAJOR.MINOR (e.g., @lsdl 1.0)
        The '.' is tokenized as ERROR since it's not in the lexer patterns.
        """
        self.consume("KEYWORD")  # @lsdl

        # Parse MAJOR version - must be INT
        tok = self.current()
        if not tok or tok.type != "INT":
            got = f"{tok.type} ({tok.value!r})" if tok else "end of input"
            self.add_error(f"expected integer major version, got {got}", tok)
            return (1, 0)
        major = int(self.consume("INT").value)

        # Expect dot separator - tokenized as ERROR since '.' isn't a lexer token
        tok = self.current()
        if not tok:
            self.add_error("expected '.' after major version, got end of input")
            return (major, 0)
        if tok.value != ".":
            self.add_error(f"expected '.' after major version, got {tok.value!r}", tok)
            return (major, 0)
        # Consume the dot (it's an ERROR token or similar non-semantic token)
        self.consume()

        # Parse MINOR version - must be INT
        tok = self.current()
        if not tok or tok.type != "INT":
            got = f"{tok.type} ({tok.value!r})" if tok else "end of input"
            self.add_error(f"expected integer minor version, got {got}", tok)
            return (major, 0)
        minor = int(self.consume("INT").value)

        # Check version compatibility (constraint: reject major > 1)
        if major > 1:
            self.add_error(f"unsupported major version {major}")

        return (major, minor)

    def parse_metrics_block(self) -> Metrics:
        """Parse @metrics block."""
        tok = self.consume("KEYWORD")  # @metrics
        metrics = Metrics()
        self.skip_blank_lines()

        metric_map = {
            "cap-top": "cap_top",
            "ascender": "ascender",
            "cap-height": "cap_height",
            "x-top": "x_top",
            "baseline": "baseline",
            "descender": "descender",
            "desc-limit": "desc_limit",
        }

        while not self._at_end_kw():
            self.skip_blank_lines()
            t = self.current()
            if t is None or self._at_end_kw():
                break

            # Expect metric-name: value
            if t.type == "NAME":
                name = self.consume().value
                if self._check("COLON") is not None:
                    self.consume()
                if self._check("INT") is not None:
                    value = int(self.consume().value)
                    # Constraint 15: values must be 0-12, non-decreasing
                    if value < 0 or value > 12:
                        self.add_error(f"metric value must be 0-12, got {value}")
                    if name in metric_map:
                        setattr(metrics, metric_map[name], value)
                else:
                    self.add_error(f"expected integer value for {name}")
            elif t.type == "NL":
                self.pos += 1
            else:
                self.add_error(f"unexpected in @metrics: {t.value!r}")
                self.pos += 1

        if self._at_end_kw():
            self.consume()

        # Validate monotonicity (constraint 15)
        values = [
            metrics.cap_top,
            metrics.ascender,
            metrics.cap_height,
            metrics.x_top,
            metrics.baseline,
            metrics.descender,
            metrics.desc_limit,
        ]
        for i in range(1, len(values)):
            if values[i] < values[i - 1]:
                self.add_error("metric values must be monotonically non-decreasing", tok)
                break

        return metrics

    # -------------------------------------------------------------------------
    # Element Definitions
    # -------------------------------------------------------------------------

    def parse_elem_block(self) -> ElementDefinition | None:
        """Parse @elem block.

        Returns:
            ElementDefinition on success, None on error (error recorded via add_error).
            Callers should check for None and continue parsing to accumulate errors.
        """
        tok = self.consume("KEYWORD")  # @elem
        line, col = tok.line, tok.col

        # Element name
        name = self.parse_full_elem_name()
        if not name:
            self.skip_to_end_or_keyword()
            return None

        # Optional /24 grid spec
        grid = 12
        if self._check("GRID_SPEC") is not None:
            grid = 24 if self.consume().value == "/24" else 12

        self.skip_blank_lines()

        elem = ElementDefinition(name=name, grid=grid, line=line, col=col)
        is_expr_form = False
        seen_anchors = False  # Track if we've parsed anchors: field

        while not self._at_end_kw():
            self.skip_blank_lines()
            t = self.current()
            if t is None or self._at_end_kw():
                break

            if t.type == "BLOCK_FIELD":
                field_name = t.value.rstrip(":")
                self.consume()

                if field_name == "zone":
                    if self._check("NAME") is not None:
                        zone_val = self.consume().value
                        try:
                            elem.zone = Zone(zone_val)
                        except ValueError:
                            self.add_error(f"invalid zone: {zone_val}")
                    else:
                        self.add_error("expected zone name")

                elif field_name == "path":
                    elem.path_ids = []
                    while self._check("NAME") is not None:
                        elem.path_ids.append(self.consume().value)

                elif field_name == "close":
                    if self._check("BOOL") is not None:
                        elem.close = self.consume().value == "true"

                elif field_name == "width":
                    if self._check("INT") is not None:
                        width = int(self.consume().value)
                        if width not in (0, 1, 2):
                            self.add_error(f"width must be 0, 1, or 2, got {width}")
                        elem.width = width

                elif field_name == "anchors":
                    elem.anchors = self.parse_anchor_defs()
                    seen_anchors = True

                elif field_name == "build":
                    if self._check("FROM_EXPR") is not None:
                        self.consume()
                        is_expr_form = True
                        # Constraint 11: /24 and from_expr are mutually exclusive
                        if grid == 24:
                            self.add_error("/24 and build: from_expr are mutually exclusive", tok)
                    else:
                        self.add_error("expected 'from_expr' after build:")

                elif field_name == "transform":
                    self.add_error("transform: only valid in @style blocks")

            elif t.type == "META_FIELD":
                self.parse_metadata_field(elem.metadata)

            elif t.type == "NAME":
                peek1 = self.peek(1)
                if peek1 is not None and peek1.type == "EQUALS":
                    # After anchors:, NAME = COORD is an anchor continuation, not a path point.
                    # Path points use NAME = COORD or NAME = C(...), but only before anchors:.
                    peek2 = self.peek(2)
                    if seen_anchors and peek2 is not None and peek2.type == "COORD":
                        # Anchor continuation on a new line
                        more_anchors = self.parse_anchor_defs()
                        elem.anchors.extend(more_anchors)
                    else:
                        # Path point definition: p1 = [x,y] or p1 = C(...)
                        pid = self.consume().value
                        self.consume("EQUALS")
                        pp = self.parse_path_point(elem.grid)
                        if pp:
                            if elem.path_points is None:
                                elem.path_points = {}
                            elem.path_points[pid] = pp
                elif is_expr_form:
                    elem.expression = self.parse_expr()
                else:
                    self.add_error(f"unexpected in @elem: {t.value!r}", t)
                    self.pos += 1

            elif t.type == "COMPOSE_OP" or t.type == "XFORM_OP":
                if is_expr_form:
                    elem.expression = self.parse_expr()
                else:
                    self.add_error("expression without build: from_expr")
                    self.pos += 1

            elif t.type == "LITERAL_CHAR" and is_expr_form:
                elem.expression = self.parse_expr()

            elif t.type == "NL":
                self.pos += 1
            else:
                self.add_error(f"unexpected in @elem: {t.value!r}", t)
                self.pos += 1

        if self._at_end_kw():
            self.consume()

        # Validate element form (constraints 9, 10)
        if is_expr_form:
            if elem.path_points:
                self.add_error("expression-form block cannot have path definitions", tok)
        else:
            if not elem.zone:
                self.add_error("path-form @elem requires zone:", tok)
            if not elem.anchors:
                self.add_error("path-form @elem requires anchors:", tok)

        # Validate path point IDs match path: declaration
        if elem.path_ids and elem.path_points:
            declared = set(elem.path_ids)
            defined = set(elem.path_points.keys())
            missing = declared - defined
            extra = defined - declared
            if missing:
                self.add_error(
                    f"path points declared but not defined: {', '.join(sorted(missing))}", tok
                )
            if extra:
                self.add_error(
                    f"path points defined but not in path: {', '.join(sorted(extra))}", tok
                )

        # Track references for cycle detection
        if elem.expression:
            self.element_refs[name] = self.collect_refs(elem.expression)

        return elem

    def parse_full_elem_name(self) -> str | None:
        """Parse element name with optional variant tags.

        Returns:
            Element name string on success, None on error (error recorded via add_error).
        """
        tok = self.current()
        if tok and tok.type in ("NAME", "LITERAL_CHAR"):
            return self.consume().value
        self.add_error("expected element name")
        return None

    def parse_anchor_defs(self) -> list[Anchor]:
        """Parse anchor definitions: name=[x,y] name=[x,y] ..."""
        anchors = []
        while self._check("NAME") is not None:
            name = self.consume().value
            if self._check("EQUALS") is not None:
                self.consume()
                if self._check("COORD") is not None:
                    coord = self.parse_coordinate()
                    anchors.append(Anchor(name, coord))
                else:
                    self.add_error(f"expected coordinate after {name}=")
            else:
                # Might be continuation without =
                break
        return anchors

    def parse_coordinate(self) -> Coordinate:
        """Parse [x,y] coordinate."""
        tok = self.consume("COORD")
        # Format: [x,y]
        inner = tok.value[1:-1]  # Remove brackets
        x, y = map(int, inner.split(","))
        return Coordinate(x, y)

    def parse_path_point(self, grid: int = 12) -> PathPoint | None:
        """Parse a path point (line-to or curve-to).

        This is a try-parse method: returns None if the current token is not
        a valid path point start (COORD or CURVE). Does not record an error
        when returning None since the caller may be probing for optional content.

        Returns:
            PathPoint on success, None if current token is not a path point.
        """
        tok = self.current()
        if tok is None:
            return None
        max_val = grid

        if tok.type == "COORD":
            coord = self.parse_coordinate()
            if coord.x < 0 or coord.x > max_val or coord.y < 0 or coord.y > max_val:
                self.add_error(f"coordinate out of range 0-{max_val}: {coord}")
            return PathPoint(endpoint=coord)

        elif tok.type == "CURVE":
            self.consume()  # C(
            coords = []
            while self._check("COORD") is not None:
                coord = self.parse_coordinate()
                if coord.x < 0 or coord.x > max_val or coord.y < 0 or coord.y > max_val:
                    self.add_error(f"coordinate out of range 0-{max_val}: {coord}")
                coords.append(coord)

            if self._check("RPAREN") is not None:
                self.consume()

            if len(coords) == 2:
                # Quadratic curve
                return PathPoint(endpoint=coords[1], control1=coords[0])
            elif len(coords) == 3:
                # Cubic curve
                return PathPoint(endpoint=coords[2], control1=coords[0], control2=coords[1])
            else:
                self.add_error(f"curve requires 2 or 3 coordinates, got {len(coords)}")
                return None

        return None

    # -------------------------------------------------------------------------
    # Character Definitions
    # -------------------------------------------------------------------------

    def parse_char_block(self) -> CharacterDefinition | None:
        """Parse @char block.

        Returns:
            CharacterDefinition on success, None on error (error recorded via add_error).
            Callers should check for None and continue parsing to accumulate errors.
        """
        tok = self.consume("KEYWORD")  # @char
        line, col = tok.line, tok.col

        # Literal character
        if self._check("LITERAL_CHAR") is None:
            self.add_error("expected literal character after @char")
            self.skip_to_end_or_keyword()
            return None
        char = self.consume().value

        # Unicode name
        if self._check("UNAME") is None:
            self.add_error("expected Unicode name after character")
            self.skip_to_end_or_keyword()
            return None
        uname = self.consume().value

        self.skip_blank_lines()

        char_def = CharacterDefinition(char=char, name=uname, line=line, col=col)
        is_expr_form = False

        while not self._at_end_kw():
            self.skip_blank_lines()
            t = self.current()
            if t is None or self._at_end_kw():
                break

            if t.type == "BLOCK_FIELD":
                field_name = t.value.rstrip(":")
                self.consume()

                if field_name == "zone":
                    if self._check("NAME") is not None:
                        zone_val = self.consume().value
                        try:
                            char_def.zone = Zone(zone_val)
                        except ValueError:
                            self.add_error(f"invalid zone: {zone_val}")

                elif field_name == "path":
                    char_def.path_ids = []
                    while self._check("NAME") is not None:
                        char_def.path_ids.append(self.consume().value)

                elif field_name == "close":
                    if self._check("BOOL") is not None:
                        char_def.close = self.consume().value == "true"

                elif field_name == "width":
                    if self._check("INT") is not None:
                        width = int(self.consume().value)
                        if width not in (0, 1, 2):
                            self.add_error(f"width must be 0, 1, or 2, got {width}")
                        char_def.width = width

                elif field_name == "anchors":
                    char_def.anchors = self.parse_anchor_defs()

                elif field_name == "build":
                    if self._check("FROM_EXPR") is not None:
                        self.consume()
                        is_expr_form = True

            elif t.type == "META_FIELD":
                self.parse_metadata_field(char_def.metadata)

            elif t.type == "NAME":
                peek1 = self.peek(1)
                if peek1 is not None and peek1.type == "EQUALS":
                    # Path point definition
                    pid = self.consume().value
                    self.consume("EQUALS")
                    pp = self.parse_path_point()
                    if pp:
                        if char_def.path_points is None:
                            char_def.path_points = {}
                        char_def.path_points[pid] = pp
                else:
                    self.pos += 1

            elif t.type == "COMPOSE_OP" or t.type == "XFORM_OP":
                if is_expr_form:
                    char_def.expression = self.parse_expr()
                else:
                    self.add_error("expression without build: from_expr")

            elif t.type == "NL":
                self.pos += 1
            else:
                self.pos += 1

        if self._at_end_kw():
            self.consume()

        # Validate path point IDs match path: declaration
        if char_def.path_ids and char_def.path_points:
            declared = set(char_def.path_ids)
            defined = set(char_def.path_points.keys())
            missing = declared - defined
            extra = defined - declared
            if missing:
                self.add_error(
                    f"path points declared but not defined: {', '.join(sorted(missing))}", tok
                )
            if extra:
                self.add_error(
                    f"path points defined but not in path: {', '.join(sorted(extra))}", tok
                )

        return char_def

    def parse_char_inline(self) -> CharacterDefinition | None:
        """Parse inline character definition: CHAR UNAME = EXPR [METADATA]

        Returns:
            CharacterDefinition on success, None on error (error recorded via add_error).
            Callers should check for None and continue parsing to accumulate errors.
        """
        tok = self.current()
        if tok is None:
            self.add_error("expected literal character")
            return None
        line, col = tok.line, tok.col

        # Literal character (may be LITERAL_CHAR or single-letter NAME/NAME)
        if tok.type == "LITERAL_CHAR" or (tok.type == "NAME" and len(tok.value) == 1):
            char = self.consume().value
        else:
            self.add_error("expected literal character")
            return None

        # Unicode name
        if self._check("UNAME") is None:
            self.add_error("expected Unicode name after character")
            return None
        uname = self.consume().value

        # Equals sign
        if self._check("EQUALS") is None:
            self.add_error("expected = after Unicode name")
            return None
        self.consume()

        # Expression
        expr = self.parse_expr()
        if not expr:
            # parse_expr may return None without recording an error (e.g., at end of input)
            self.add_error("expected expression after =")
            return None

        char_def = CharacterDefinition(char=char, name=uname, expression=expr, line=line, col=col)

        # Trailing metadata
        while self._check("META_FIELD") is not None:
            self.parse_metadata_field(char_def.metadata)

        return char_def

    # -------------------------------------------------------------------------
    # Alias, Case, Style
    # -------------------------------------------------------------------------

    def parse_alias(self) -> AliasDefinition | None:
        """Parse @alias definition.

        Returns:
            AliasDefinition on success, None on error (error recorded via add_error).
            Callers should check for None and continue parsing to accumulate errors.
        """
        tok = self.consume("KEYWORD")  # @alias
        line, col = tok.line, tok.col

        # Optional script qualifier
        script_qual = None
        name_tok = self.current()
        if name_tok is not None and name_tok.type in ("NAME", "UNAME", "TAG"):
            name = self.consume().value
            # Check for script qualifier (Latn:H)
            if self._check("COLON") is not None:
                self.consume()
                script_qual = name
                next_tok = self.current()
                if next_tok is not None and next_tok.type in ("NAME", "LITERAL_CHAR", "TAG"):
                    name = self.consume().value
                else:
                    self.add_error("expected name after script qualifier")
                    return None
        else:
            self.add_error("expected alias name")
            return None

        # Equals sign
        if self._check("EQUALS") is None:
            self.add_error("expected = in alias")
            return None
        self.consume()

        # Target
        target_tok = self.current()
        if target_tok is None or target_tok.type not in ("NAME", "LITERAL_CHAR"):
            self.add_error("expected target name/character in alias")
            return None
        target = self.consume().value

        # Constraint 17: alias names must not collide
        # For script-qualified aliases, the full name includes the qualifier
        full_name = f"{script_qual}:{name}" if script_qual else name
        if full_name in self.defined_aliases:
            self.add_error(f"duplicate alias: {full_name}", tok)
        if name in self.defined_elements:
            self.add_error(f"alias name conflicts with element: {name}", tok)
        if name in self.defined_chars:
            self.add_error(f"alias name conflicts with character: {name}", tok)
        self.defined_aliases[full_name] = line

        return AliasDefinition(
            name=full_name, target=target, script_qualifier=script_qual, line=line, col=col
        )

    def parse_case_mapping(self) -> CaseMapping | None:
        """Parse @case mapping.

        Returns:
            CaseMapping on success, None on error (error recorded via add_error).
            Callers should check for None and continue parsing to accumulate errors.
        """
        tok = self.consume("KEYWORD")  # @case
        line, col = tok.line, tok.col

        # Uppercase character (LITERAL_CHAR or single-letter NAME)
        upper_tok = self.current()
        if upper_tok is None:
            self.add_error("expected uppercase character")
            return None
        if upper_tok.type == "LITERAL_CHAR" or (
            upper_tok.type == "NAME" and len(upper_tok.value) == 1
        ):
            upper = self.consume().value
        else:
            self.add_error("expected uppercase character")
            return None

        # Lowercase character (LITERAL_CHAR or single-letter NAME)
        lower_tok = self.current()
        if lower_tok is None:
            self.add_error("expected lowercase character")
            return None
        if lower_tok.type == "LITERAL_CHAR" or (
            lower_tok.type == "NAME" and len(lower_tok.value) == 1
        ):
            lower = self.consume().value
        else:
            self.add_error("expected lowercase character")
            return None

        # Optional final: form
        final = None
        if self._check("FINAL") is not None:
            self.consume()
            final_tok = self.current()
            if final_tok is not None and final_tok.type in ("LITERAL_CHAR", "NAME"):
                final = self.consume().value

        # Constraint: duplicate uppercase entries are errors
        if upper in self.case_uppers:
            self.add_error(f"duplicate @case for uppercase {upper}", tok)
        self.case_uppers.add(upper)

        if lower in self.case_lowers:
            self.add_error(f"duplicate @case for lowercase {lower}", tok)
        self.case_lowers.add(lower)

        return CaseMapping(upper=upper, lower=lower, final=final, line=line, col=col)

    def parse_style_block(self) -> StyleDefinition | None:
        """Parse @style block.

        Returns:
            StyleDefinition on success, None on error (error recorded via add_error).
            Callers should check for None and continue parsing to accumulate errors.
        """
        tok = self.consume("KEYWORD")  # @style
        line, col = tok.line, tok.col

        # Style name (lowercase ASCII)
        if self._check("NAME") is None:
            self.add_error("expected style name")
            self.skip_to_end_or_keyword()
            return None
        name = self.consume().value

        if name in self.defined_styles:
            self.add_error(f"duplicate style: {name}", tok)
        self.defined_styles[name] = line

        self.skip_blank_lines()
        self.in_style_block = True

        transform = None
        while not self._at_end_kw():
            self.skip_blank_lines()
            t = self.current()
            if t is None or self._at_end_kw():
                break

            if t.type == "BLOCK_FIELD" and t.value == "transform:":
                self.consume()
                expr = self.parse_expr()
                if expr and isinstance(expr, TransformExpr):
                    transform = expr
                elif expr:
                    self.add_error("@style transform must be a transform expression (sc, sh, sk)")
            elif t.type == "NL":
                self.pos += 1
            else:
                self.pos += 1

        self.in_style_block = False

        if self._at_end_kw():
            self.consume()

        if not transform:
            self.add_error("@style block requires transform:", tok)
            return None

        return StyleDefinition(name=name, transform=transform, line=line, col=col)

    # -------------------------------------------------------------------------
    # Metadata
    # -------------------------------------------------------------------------

    def parse_metadata_field(self, meta: Metadata) -> None:
        """Parse a metadata field and add to metadata object."""
        tok = self.consume("META_FIELD")
        field_name = tok.value.rstrip(":")

        if field_name == "script":
            cur = self.current()
            if cur is not None:
                meta.script = self.consume().value
        elif field_name == "ortho":
            # Comma-separated list of language tags
            orthos = []
            while (t := self._check("NAME", "UNAME", "TAG")) is not None:
                orthos.append(self.consume().value)
                if self._check("COMMA") is not None:
                    self.consume()
                else:
                    break
            meta.ortho = orthos
        elif field_name == "block":
            parts = []
            while (t := self.current()) is not None and t.type not in (
                "NL",
                "META_FIELD",
                "KEYWORD",
            ):
                parts.append(self.consume().value)
            meta.block = " ".join(parts)
        elif field_name == "cp":
            if self._check("CODEPOINT") is not None:
                meta.cp = self.consume().value
        elif field_name == "freq":
            if self._check("INT") is not None:
                meta.freq = int(self.consume().value)
        elif field_name.startswith("x-"):
            # Extension field
            parts = []
            while (t := self.current()) is not None and t.type not in (
                "NL",
                "META_FIELD",
                "KEYWORD",
            ):
                parts.append(self.consume().value)
            meta.extensions[field_name] = " ".join(parts)

    # -------------------------------------------------------------------------
    # Expression Parsing
    # -------------------------------------------------------------------------

    def parse_expr(self) -> Expr | None:
        """Parse an expression (composition, transform, or reference).

        This is a try-parse method: returns None if there is no current token
        (end of input) or if the current token cannot start an expression.
        When returning None due to an invalid token, an error is recorded via add_error.

        Returns:
            Expr on success, None if no expression can be parsed.
        """
        tok = self.current()
        if not tok:
            return None

        if tok.type == "COMPOSE_OP":
            return self.parse_compose_expr()
        elif tok.type == "XFORM_OP":
            return self.parse_xform_expr()
        elif tok.type == "WILDCARD":
            if not self.in_style_block:
                self.add_error("* wildcard only valid in @style blocks", tok)
            self.consume()
            return WildcardExpr(line=tok.line, col=tok.col)
        elif tok.type in ("NAME", "LITERAL_CHAR"):
            name = self.consume().value
            return RefExpr(name=name, line=tok.line, col=tok.col)
        else:
            # Provide actionable guidance based on what token we got
            got_desc = self._describe_token(tok)
            hint = ""
            if tok.type == "KEYWORD":
                hint = " (expressions cannot start with keywords)"
            elif tok.type == "RPAREN":
                hint = " (missing argument before closing parenthesis?)"
            elif tok.type == "COMMA":
                hint = " (missing argument before comma?)"
            elif tok.type == "INT":
                hint = " (numbers must be part of a coordinate like [x,y] or a parameter like sx=N)"
            self.add_error(
                f"expected expression: composition operator (STACK, LR, DIA, OVR, FRAME, LIG, APEX), "
                f"transform (sc, sh, sk), or element name, got {got_desc}{hint}",
                tok,
            )
            self.pos += 1
            return None

    def parse_compose_expr(self) -> ComposeExpr:
        """Parse composition operator expression."""
        tok = self.consume("COMPOSE_OP")
        op = tok.value
        line, col = tok.line, tok.col

        # Check for opening paren with helpful error message
        lparen_tok = self.current()
        if lparen_tok is None or lparen_tok.type != "LPAREN":
            got = lparen_tok.value if lparen_tok else "end of input"
            raise self.error(f"expected '(' after {op}, got {got!r}", tok)
        self.consume("LPAREN")
        children: list[Expr] = []
        split: list[int] | None = None
        anchor_override: str | None = None
        merge_strategy: str | None = None

        # Parse first child
        child = self.parse_expr()
        if child:
            children.append(child)

        # Parse remaining children and parameters
        while self._check("COMMA") is not None:
            self.consume()

            # Check for split
            if self._check("SPLIT") is not None:
                split = [int(x) for x in self.consume().value.split("/")]
                continue

            # Check for attach: parameter (DIA)
            if self._check("ATTACH") is not None:
                self.consume()
                if self._check("NAME") is not None:
                    anchor_override = self.consume().value
                continue

            # Check for merge: parameter (LIG)
            if self._check("MERGE") is not None:
                self.consume()
                if self._check("NAME") is not None:
                    merge_strategy = self.consume().value
                continue

            # Otherwise it's another child expression
            cur = self.current()
            if cur is not None and cur.type != "RPAREN":
                child = self.parse_expr()
                if child:
                    children.append(child)

        if self._check("RPAREN") is not None:
            self.consume()

        # Validate operator constraints (12.9)
        self.validate_compose_args(op, children, split, tok)

        return ComposeExpr(
            op=op,
            children=children,
            split=split,
            anchor_override=anchor_override,
            merge_strategy=merge_strategy,
            line=line,
            col=col,
        )

    def validate_compose_args(
        self, op: str, children: list[Expr], split: list[int] | None, tok: Token
    ) -> None:
        """Validate composition operator arguments per Section 12.9."""
        n = len(children)

        if op == "STACK":
            if n < 2:
                self.add_error(f"STACK requires at least 2 children, got {n}", tok)

        elif op == "LR":
            if n < 2:
                self.add_error(f"LR requires at least 2 children, got {n}", tok)
            # Constraint 19: split must have N values if provided
            if split and len(split) != n:
                self.add_error(f"LR split has {len(split)} values but {n} children", tok)

        elif op == "LR3":
            if n < 3:
                self.add_error(f"LR3 requires at least 3 children, got {n}", tok)
            if split and len(split) != n:
                self.add_error(f"LR3 split has {len(split)} values but {n} children", tok)

        elif op == "DIA":
            # Constraint 20: DIA must have 2 or 3 arguments
            if n < 2 or n > 3:
                self.add_error(f"DIA requires 2 or 3 arguments, got {n}", tok)

        elif op == "DIA2":
            # Constraint 21: DIA2 must have exactly 3 arguments
            if n != 3:
                self.add_error(f"DIA2 requires exactly 3 arguments, got {n}", tok)

        elif op == "OVR":
            if n != 2:
                self.add_error(f"OVR requires exactly 2 children, got {n}", tok)

        elif op == "FRAME":
            # Constraint 22: FRAME must have at least 2 children
            if n < 2:
                self.add_error(f"FRAME requires at least 2 children, got {n}", tok)

        elif op == "LIG":
            # Constraint 23: LIG must have 2 or 3 arguments
            if n < 2 or n > 3:
                self.add_error(f"LIG requires 2 or 3 arguments, got {n}", tok)

        elif op == "APEX" and n < 2:
            self.add_error(f"APEX requires at least 2 children, got {n}", tok)

        # Constraint 1: split values must be positive
        if split:
            for s in split:
                if s <= 0:
                    self.add_error(f"split values must be positive, got {s}", tok)

    def parse_xform_expr(self) -> TransformExpr:
        """Parse transform operator expression."""
        tok = self.consume("XFORM_OP")
        op = tok.value
        line, col = tok.line, tok.col

        # Check for opening paren with helpful error message
        lparen_tok = self.current()
        if lparen_tok is None or lparen_tok.type != "LPAREN":
            got = lparen_tok.value if lparen_tok else "end of input"
            raise self.error(f"expected '(' after {op}, got {got!r}", tok)
        self.consume("LPAREN")

        # Parse child expression
        child = self.parse_expr()
        if child is None:
            self.add_error("transform requires a child expression", tok)
            # Use ErrorExpr placeholder to allow AST construction to continue
            # while preserving the error context for clear messaging downstream
            child = ErrorExpr(message="missing child expression in transform", line=line, col=col)

        # Parse parameters
        params: dict[str, int] = {}
        while self._check("COMMA") is not None:
            self.consume()
            if self._check("XFORM_PARAM") is not None:
                param_name = self.consume().value.rstrip("=")
                if self._check("INT") is not None:
                    param_val = int(self.consume().value)
                    # Constraint 2: TPARAM in range -12 to 24
                    if param_val < -12 or param_val > 24:
                        self.add_error(f"transform param must be -12 to 24, got {param_val}", tok)
                    params[param_name] = param_val

        if self._check("RPAREN") is not None:
            self.consume()

        return TransformExpr(op=op, child=child, params=params, line=line, col=col)

    # -------------------------------------------------------------------------
    # Semantic Validation
    # -------------------------------------------------------------------------

    def collect_refs(self, expr: Expr) -> set[str]:
        """Collect all element/character references from an expression."""
        refs: set[str] = set()
        if isinstance(expr, RefExpr):
            refs.add(expr.name)
        elif isinstance(expr, ComposeExpr):
            for child in expr.children:
                refs.update(self.collect_refs(child))
        elif isinstance(expr, TransformExpr):
            refs.update(self.collect_refs(expr.child))
        elif isinstance(expr, WildcardExpr):
            pass  # Wildcards don't reference anything
        elif isinstance(expr, ErrorExpr):
            pass  # ErrorExpr is a parse error placeholder, no references
        return refs

    def validate_semantics(self, result: LSDLFile) -> None:
        """Validate all semantic constraints from Section 12.9."""
        # Build complete name registry
        all_names = set(result.elements.keys())
        all_names.update(result.characters.keys())
        all_names.update(result.aliases.keys())

        # Constraint 6, 8: All references must resolve
        for _, elem in result.elements.items():
            if elem.expression:
                self.validate_refs(elem.expression, all_names, elem)

        for _, char_def in result.characters.items():
            if char_def.expression:
                self.validate_refs(char_def.expression, all_names, char_def)

        # Constraint 7: Cycle detection
        self.detect_cycles(result)

        # Constraint 18: @case must reference defined characters
        # Note: In lenient mode (default), we allow references to undefined
        # single-character names as they may be defined in concatenated files.
        for case_map in result.case_mappings:
            if case_map.upper not in result.characters and len(case_map.upper) > 1:
                self.add_error(
                    f"@case references undefined character: {case_map.upper}",
                    Token("", "", case_map.line, case_map.col),
                )
            if case_map.lower not in result.characters and len(case_map.lower) > 1:
                self.add_error(
                    f"@case references undefined character: {case_map.lower}",
                    Token("", "", case_map.line, case_map.col),
                )
            if (
                case_map.final
                and case_map.final not in result.characters
                and len(case_map.final) > 1
            ):
                self.add_error(
                    f"@case references undefined final character: {case_map.final}",
                    Token("", "", case_map.line, case_map.col),
                )

    def validate_refs(
        self, expr: Expr, all_names: set[str], context: ElementDefinition | CharacterDefinition
    ) -> None:
        """Validate that all references in an expression resolve."""
        if isinstance(expr, RefExpr):
            name = expr.name
            # Check if it's a known element/character/alias
            if name not in all_names:
                # Check if base name (without variants) is in element registry
                base = name.split(".")[0]
                # Allow references that are:
                # 1. In the element registry (or a variant thereof)
                # 2. Single characters (likely character references defined elsewhere)
                # 3. Single lowercase letters (likely base characters like a, b, c)
                is_known_base = base in FULL_ELEMENT_REGISTRY
                is_single_char = len(name) == 1
                if not is_known_base and not is_single_char:
                    self.add_error(
                        f"unresolved reference: {name}",
                        Token("", "", expr.line, expr.col),
                    )
        elif isinstance(expr, ComposeExpr):
            for child in expr.children:
                self.validate_refs(child, all_names, context)
        elif isinstance(expr, TransformExpr):
            self.validate_refs(expr.child, all_names, context)

    def detect_cycles(self, result: LSDLFile) -> None:
        """Detect cycles in element reference graph (constraint 7)."""
        # Build dependency graph
        graph: dict[str, set[str]] = {}
        for name, elem in result.elements.items():
            if elem.expression:
                graph[name] = self.collect_refs(elem.expression)
            else:
                graph[name] = set()

        # DFS for cycles
        visited: set[str] = set()
        path: set[str] = set()

        def dfs(node: str) -> bool:
            if node in path:
                self.add_error(f"cycle detected involving: {node}")
                return True
            if node in visited:
                return False
            path.add(node)
            for dep in graph.get(node, set()):
                if dep in graph and dfs(dep):  # Only follow element refs
                    return True
            path.remove(node)
            visited.add(node)
            return False

        for node in graph:
            dfs(node)


# =============================================================================
# Public API
# =============================================================================


def parse(source: str, filename: str = "<string>") -> LSDLFile:
    """Parse LSDL source text into an LSDLFile.

    Args:
        source: LSDL source code as a string
        filename: Optional filename for error messages

    Returns:
        Parsed LSDLFile model

    Raises:
        ParseError: If the source contains syntax or semantic errors
    """
    tokens = _tokenize(source)
    parser = Parser(tokens, filename)
    return parser.parse()


def parse_string(source: str, filename: str = "<string>") -> LSDLFile:
    """Parse LSDL source text into an LSDLFile (alias for parse())."""
    return parse(source, filename)


def parse_file(path: str | Path, *, encoding: str = "utf-8") -> LSDLFile:
    """Parse an LSDL file into an LSDLFile.

    Args:
        path: Path to the .lsdl file
        encoding: Character encoding for reading the file. Defaults to UTF-8,
            which is the canonical encoding for LSDL source files per the spec.

    Returns:
        Parsed LSDLFile model

    Raises:
        ParseError: If the file contains syntax or semantic errors
        FileNotFoundError: If the file doesn't exist
    """
    path = Path(path)
    source = path.read_text(encoding=encoding)
    return parse(source, filename=str(path))
