# LSDL Implementor's Checklist

**Version:** 1.0
**Date:** 2026-06-27
**Status:** Companion Document
**Companion to:** Latin Script Description Language (LSDL) Specification v1.0 [LSDL]

---

## Purpose

This document collects every item that the LSDL specification
leaves to renderers, toolchains, or authors. It contains no new
normative text. Every entry is a cross-reference to the section
of [LSDL] where the decision is defined. The purpose is to give
implementors a single checklist of choices they must make.

All section references (SS) refer to [LSDL] unless otherwise noted.

---

## 1. Explicitly Out of Scope

These concerns are not addressed by LSDL at all. The
specification makes no statements about them and future versions
are not expected to add them.

| Topic                                      | Reference       |
|--------------------------------------------|-----------------|
| Glyph rendering (anti-aliasing, hinting, rasterization) | SS1.3 |
| Font metrics beyond vertical zones (advance widths, kerning, horizontal metrics) | SS1.3 |
| Text layout (line breaking, justification, bidi)         | SS1.3 |
| Character encoding or identification (handled by Unicode)| SS1.3 |
| Stroke animation or temporal sequencing                  | SS1.3 |
| Aesthetic or calligraphic style variation (beyond @style)| SS1.3 |
| File import, include, or cross-file references           | SS4.2.2 |
| Arabic, Devanagari, CJK, or other non-bicameral scripts  | SS17.3 |
| Case folding algorithms                                  | SS13.8 |

---

## 2. Level 1 Parser Checklist

A Level 1 (Parser) conformant implementation MUST satisfy all of
the following requirements. Each item references the normative
section of [LSDL].

### 2.1 Lexer Requirements

| Requirement                                | Reference       |
|--------------------------------------------|-----------------|
| Parse UTF-8 encoded files without BOM      | SS4.2           |
| Accept LF or CR LF line endings            | SS4.2           |
| Handle horizontal whitespace (SPACE, TAB) interchangeably | SS4.2 |
| Parse comment lines (lines beginning with #) | SS4.1          |

### 2.2 Version Declaration

| Requirement                                | Reference       |
|--------------------------------------------|-----------------|
| Parse @lsdl X.Y format declaration         | SS4.2           |
| Reject files with unsupported major version | SS4.2          |
| Warn on unknown minor version, continue processing | SS4.2    |
| Assume version 1.0 if no declaration present | SS4.2         |

### 2.3 Metrics Block

| Requirement                                | Reference       |
|--------------------------------------------|-----------------|
| Parse @metrics ... @end block              | SS5.3           |
| Validate metric values are 0-12 integers   | SS5.3, SS12.9 #15 |
| Validate monotonically non-decreasing order | SS5.3, SS12.9 #15 |
| Enforce at most one @metrics block per file | SS12.9 #14     |
| Enforce @metrics appears before any @elem/@char/@alias | SS12.9 #13 |

### 2.4 Element Definitions (Block Form)

| Requirement                                | Reference       |
|--------------------------------------------|-----------------|
| Parse @elem ... @end blocks                | SS10.1          |
| Parse zone: declaration with valid zone names | SS10.3, SS12.9 #12 |
| Parse path: with point references          | SS10.2          |
| Parse path points: [x,y], C([cx,cy] [x,y]), C([c1x,c1y] [c2x,c2y] [x,y]) | SS10.2 |
| Validate coordinate values 0-12 (standard) or 0-24 (/24 blocks) | SS12.9 #4, #5 |
| Parse /24 grid override                    | SS5.5           |
| Reject /24 combined with build: from_expr  | SS12.9 #11      |
| Parse width: with values 0, 1, or 2        | SS5.6, SS12.9 #3 |
| Parse anchors: with name=[x,y] definitions | SS7.2           |
| Validate at least one anchor per element   | SS7.1           |
| Parse close: true/false                    | SS10.1          |

### 2.5 Character Definitions

| Requirement                                | Reference       |
|--------------------------------------------|-----------------|
| Parse inline form: CHAR UNAME = EXPR [METADATA...] | SS11.1  |
| Parse @char ... @end block form            | SS11.2          |
| Parse build: from_expr expression blocks   | SS10.6, SS12.9 #9 |
| Validate path blocks have zone:, path defs, width:, anchors: | SS12.9 #10 |

### 2.6 Composition Operators (9 operators)

| Operator | Validation Requirements              | Reference       |
|----------|--------------------------------------|-----------------|
| STACK    | 2+ child expressions                 | SS8.2           |
| LR       | 2+ children; split count = child count if provided | SS8.3, SS12.9 #19 |
| LR3      | 3+ children; split count = child count if provided | SS8.4, SS12.9 #19 |
| DIA      | 2 or 3 arguments                     | SS8.5, SS12.9 #20 |
| DIA2     | Exactly 3 arguments                  | SS8.6, SS12.9 #21 |
| OVR      | Exactly 2 arguments                  | SS8.7           |
| FRAME    | 2+ child expressions                 | SS8.8, SS12.9 #22 |
| LIG      | 2 or 3 arguments                     | SS8.9, SS12.9 #23 |
| APEX     | 2+ child expressions                 | SS8.9           |

### 2.7 Transform Operators (3 operators)

| Operator | Parameters                           | Reference       |
|----------|--------------------------------------|-----------------|
| sc       | sx= and sy= scale factors            | SS9.2           |
| sh       | dx= and dy= shift values             | SS9.3           |
| sk       | kx= and ky= skew values              | SS9.4           |

| Requirement                                | Reference       |
|--------------------------------------------|-----------------|
| Validate TPARAM values in range -12 to 24  | SS9.1, SS12.9 #2 |
| Validate split values are positive integers | SS12.9 #1      |

### 2.8 Metadata Fields

| Requirement                                | Reference       |
|--------------------------------------------|-----------------|
| Parse script: with ISO 15924 codes         | SS4.7.1, SS12.9 #16 |
| Parse ortho: with comma-separated ISO 639 codes | SS4.7.3    |
| Parse block: field                         | SS4.6           |
| Parse cp: with U+XXXX code point           | SS4.6           |
| Parse freq: with positive integer          | SS4.6           |
| Accept x- prefixed extension fields        | SS4.6           |

### 2.9 Other Definitions

| Requirement                                | Reference       |
|--------------------------------------------|-----------------|
| Parse @alias definitions                   | SS10.7          |
| Reject alias name collisions with element names | SS10.7, SS12.9 #17 |
| Parse @case declarations                   | SS13.2          |
| Validate @case references defined characters | SS12.9 #18    |
| Parse @style blocks with transform: line   | SS16.2          |
| Validate * wildcard only in @style blocks  | SS16.3          |

### 2.10 Semantic Validation (23 constraints from SS12.9)

| # | Constraint                                  | Reference       |
|---|---------------------------------------------|-----------------|
| 1 | Split values MUST be positive integers      | SS12.9 #1       |
| 2 | TPARAM values MUST be -12 to 24             | SS12.9 #2       |
| 3 | WIDTH values MUST be 0, 1, or 2             | SS12.9 #3       |
| 4 | Standard block coordinates MUST be 0-12    | SS12.9 #4       |
| 5 | /24 block coordinates MUST be 0-24         | SS12.9 #5       |
| 6 | All FULL_ELEM references MUST resolve      | SS12.9 #6       |
| 7 | Element reference graph MUST be acyclic    | SS12.9 #7, SS4.4 |
| 8 | Element names MUST be in closed registry, variants, aliases, or defined chars | SS12.9 #8 |
| 9 | build: from_expr blocks have exactly one EXPR, zero path defs | SS12.9 #9 |
| 10 | Path geometry blocks MUST have zone:, paths, width:, anchors: | SS12.9 #10 |
| 11 | /24 blocks MUST NOT use build: from_expr   | SS12.9 #11      |
| 12 | ZONE_NAME values MUST be in zone registry  | SS12.9 #12      |
| 13 | @metrics MUST appear before @elem/@char/@alias | SS12.9 #13  |
| 14 | At most one @metrics block per file        | SS12.9 #14      |
| 15 | Metric landmarks MUST be 0-12, non-decreasing | SS12.9 #15   |
| 16 | script: tags MUST be valid ISO 15924 codes | SS12.9 #16      |
| 17 | Alias names MUST NOT collide with element/alias names | SS12.9 #17 |
| 18 | @case declarations MUST reference defined characters | SS12.9 #18 |
| 19 | LR/LR3 split count MUST equal child count  | SS12.9 #19      |
| 20 | DIA MUST have 2 or 3 arguments             | SS12.9 #20      |
| 21 | DIA2 MUST have exactly 3 arguments         | SS12.9 #21      |
| 22 | FRAME MUST have 2+ child expressions       | SS12.9 #22      |
| 23 | LIG MUST have 2 or 3 arguments             | SS12.9 #23      |

---

## 3. Level 2 Renderer Checklist

A Level 2 (Renderer) conformant implementation MUST satisfy all
Level 1 requirements plus the following.

### 3.1 Expression Evaluation

| Requirement                                | Reference       |
|--------------------------------------------|-----------------|
| Resolve all element references to their definitions | SS2.2 Level 2 |
| Apply last-definition-wins for duplicate element names | SS4.5 |

### 3.2 Bounding Box Computation

| Requirement                                | Reference       |
|--------------------------------------------|-----------------|
| Compute bounding boxes for all DAG nodes   | SS2.2 Level 2   |
| Child boxes inherit 12x12 space            | SS5.1           |
| DIA/DIA2 bounding box expands to enclose base + diacritic | SS15.3.4 |

### 3.3 Composition Operator Placement Semantics

| Operator | Placement Semantics                  | Reference       |
|----------|--------------------------------------|-----------------|
| STACK    | Align first.base to second.top vertically | SS8.2      |
| LR       | Side by side on baseline, proportional splits | SS8.3   |
| LR3      | Three-part horizontal, default 4/4/4 | SS8.4           |
| DIA      | Diacritic.attach to base.mark-above or base.mark-below | SS8.5, SS7.3 |
| DIA2     | First mark closer to base, second stacks outward | SS8.6, SS15.4 |
| OVR      | Both children occupy full parent box | SS8.7           |
| FRAME    | Parts positioned by anchor matching  | SS8.8           |
| LIG      | Horizontal adjacency or merge strategy | SS8.9, SS14.5 |
| APEX     | Diagonals meeting at top point       | SS8.9           |

### 3.4 Transform Application

| Requirement                                | Reference       |
|--------------------------------------------|-----------------|
| Apply transforms inside-out (standard function composition) | SS9.1 |
| sc and sk transforms anchor at center [6,6] | SS9.1          |
| sh is translation with no anchor point     | SS9.1           |
| Transform parameters use /12 grid even in /24 blocks | SS9.1 |
| MUST NOT reorder transforms                | SS9.1           |

### 3.5 Anchor Resolution

| Requirement                                | Reference       |
|--------------------------------------------|-----------------|
| DIA: diacritic-above zone attaches to mark-above | SS7.3 #1  |
| DIA: diacritic-below zone attaches to mark-below | SS7.3 #1  |
| DIA: x-height zone (through-mark) centers on base | SS7.3 #1 |
| DIA: fallback to centered above/below if anchor missing | SS15.3.1, SS15.3.2 |
| STACK: align base/top anchors              | SS7.3 #2        |
| LR: align on baseline using base anchors   | SS7.3 #3        |
| FRAME: use explicitly named anchors        | SS7.3 #4        |
| Support explicit attach:ANCHOR override    | SS7.4, SS15.5   |
| Reject expression if overridden anchor missing on base | SS15.5 |

### 3.6 Output Generation

| Requirement                                | Reference       |
|--------------------------------------------|-----------------|
| Emit element geometry as positioned path segments | SS2.2 Level 2 |
| Include width values in output             | SS2.2 Level 2   |

---

## 4. Implementation-Defined (Parser/Tooling)

These are choices a parser or toolchain must make. The spec
requires correct rejection of invalid input but does not constrain
how these decisions are made.

| Decision                                   | Reference       |
|--------------------------------------------|-----------------|
| Error recovery strategy (stop-at-first, collect-all, partial output) | SS2.3 |
| Error reporting format (message text, structured JSON, error codes, line/column) | SS2.3 |
| Capacity limits (SHOULD support full Latin/Greek/Cyrillic repertoire ~2500 chars) | SS18 |
| Multi-file concatenation and library management | SS4.2.2     |
| NFC detection and rejection of non-NFC input | SS4.2          |
| Mapping of width values (0, 1, 2) to concrete pixel or em widths | SS5.6 |
| Whether to warn on duplicate element names | SS4.5          |
| Whether to warn on unknown metadata fields  | SS4.6          |
| Whether to warn on unknown orthography tags  | SS4.7.3       |
| Whether to warn on unknown minor version numbers | SS4.2      |
| Whether to validate script tag consistency in @case pairs | SS13.5 |

---

## 5. Renderer Discretion (MAY/SHOULD)

These are decisions a Level 2 or Level 3 renderer MAY or SHOULD
make. Two conformant renderers may produce visually different
output from the same LSDL input due to these choices. The
evaluated element geometry is deterministic; visual presentation
is not.

| Decision                                   | Reference       |
|--------------------------------------------|-----------------|
| Output format (filled outlines, SVG paths, bitmaps, other) | SS1.3 |
| Aesthetic proportion adjustment within composition operators | SS1.4 Principle 2 |
| Positional variant substitution (e.g., bowl vs bowl.l based on context) | SS1.4 Principle 3, SS10.5 |
| Concrete width mapping (hairline, normal, bold to pixels/ems) | SS5.6 |
| Orthography-based definition selection when multiple definitions exist | SS4.7.2, SS13.6 |
| Orthography-based definition filtering     | SS4.7.2         |
| Fallback when no ortho-matched definition exists | SS4.7.2     |
| Treatment of unknown x- extension metadata | SS4.6           |
| Expansion of element geometry to filled outlines (Level 3) | SS2.2 |
| Whether to implement merge: strategies in LIG or fall back to LR | SS14.5 |
| Handling of unrecognized merge: strategy names | SS14.5       |
| Style application scope and mechanism      | SS16.4          |
| Whether to exclude diacritics from style transforms | SS16.8  |
| Selection between duplicate character definitions by ortho: context | SS13.6 |

---

## 6. Author Responsibility

These are decisions or obligations that fall on the LSDL file
author, not on parsers or renderers. A conformant parser is not
required to validate these; incorrect authoring may produce
unexpected but syntactically valid results.

| Decision                                   | Reference       |
|--------------------------------------------|-----------------|
| Ensuring NFC consistency in file text       | SS4.2           |
| Choosing the correct positional variant name vs. relying on renderer substitution | SS10.5 |
| Selecting the most specific applicable orthography tag | App E.4 |
| Ensuring @case pairs have consistent script: tags | SS13.5    |
| Defining all characters referenced in @case declarations | SS13.2 |
| Defining diacritics in correct zones (diacritic-above, diacritic-below, x-height) | SS15.2 |
| Ensuring diacritic elements have attach anchor | SS15.2       |
| Providing mark-above/mark-below anchors on base characters for proper diacritic attachment | SS15.3.1, SS15.3.2 |
| Noting non-standard usage via x- metadata  | SS17.2          |
| Defining base characters before using them in DIA compositions | SS12.9 #6 |

---

## 7. Deterministic by Specification

For contrast, these properties are fully determined by the spec.
Two conformant implementations given the same input MUST produce
identical results for these.

| Property                                   | Reference       |
|--------------------------------------------|-----------------|
| Element geometry (positioned path segments) | SS2.2 Level 2  |
| Bounding box computation for all nodes     | SS2.2 Level 2   |
| Child box inheritance (each child gets 12x12 space) | SS5.1   |
| Layout operator space division (proportional splits) | SS8.3   |
| Transform composition order (inside-out)   | SS9.1           |
| Transform anchor point (center, [6,6])     | SS9.1           |
| Transform parameters use /12 grid even in /24 blocks | SS9.1  |
| DIA anchor resolution by zone (above/below/through) | SS7.3   |
| DIA2 stacking order (first mark closer to base) | SS15.4     |
| Bounding box expansion for DIA compositions | SS15.3.4       |
| Element reference resolution (last-definition-wins for duplicates) | SS4.5 |
| Alias resolution (bidirectional equivalence) | SS10.7        |
| Acyclicity enforcement                     | SS4.4           |
| Closed operator sets (reject unknown elements, layouts, transforms) | SS1.2, SS6.7 |
| Metric zone boundaries from @metrics or defaults | SS5.2, SS5.3 |
| @case declarations have no effect on evaluation | SS13.4 #4  |
| @style blocks have no effect on evaluation (tooling concern) | SS16.5 #6 |
| Metadata has no effect on evaluation       | SS4.6           |

---

## 8. Conformance Testing

### 8.1 Valid Input Tests

Run against `test-vectors/valid/` directory:
- Parser MUST accept all files without error
- Level 2 renderer MUST produce deterministic output matching expected geometry

### 8.2 Invalid Input Tests

Run against `test-vectors/invalid/` directory:
- Parser MUST reject all files
- Error should match expected error category (see test metadata)

### 8.3 Error Categories

| Category              | Description                                    |
|-----------------------|------------------------------------------------|
| `syntax`              | Lexical or grammar error                       |
| `undefined-ref`       | Reference to undefined element/character       |
| `cycle`               | Cyclic element reference detected              |
| `unknown-operator`    | Unknown composition or transform operator      |
| `unknown-element`     | Element name not in closed registry            |
| `unknown-zone`        | Zone name not in zone registry                 |
| `param-range`         | Parameter value out of bounds                  |
| `coord-range`         | Coordinate value out of grid bounds            |
| `split-mismatch`      | Split count doesn't match child count          |
| `arg-count`           | Wrong number of arguments to operator          |
| `duplicate-metrics`   | Multiple @metrics blocks                       |
| `metrics-order`       | @metrics after @elem/@char/@alias              |
| `anchor-missing`      | Required anchor not defined                    |
| `alias-collision`     | Alias name collides with element name          |
| `case-undefined`      | @case references undefined character           |

---

## References

**[LSDL]**
Latin Script Description Language (LSDL) Specification, Version 1.0, 2026-02-09.
