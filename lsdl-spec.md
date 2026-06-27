# Latin Script Description Language (LSDL) Specification

**Version:** 1.0
**Author:** Mark Atwood
**Date:** 2026-02-09  

---

## Abstract

Latin Script Description Language (LSDL) is a constructive,
non-Turing domain-specific language for describing the structural
composition of characters in Latin, Greek, Cyrillic, and related
bicameral alphabetic scripts from anatomical elements, reusable
components, and composition operators. LSDL fills the gap between
Unicode (which encodes identity, not structure), font formats
(which store flattened outlines with no semantics), and
typographic databases (which are annotations, not grammars). LSDL
produces deterministic geometric descriptions of character
structure from a closed set of primitives and operators.

LSDL is a sibling format to CSDL (CJK Stroke Description
Language). Both share the same 12×12 coordinate grid, the same
transform operators, and the same design philosophy: define
primitives once, then compose. LSDL differs from CSDL in its use
of a vertical metric system, anchor-based attachment (rather than
grid partitioning), first-class diacritic composition, case
mapping, and ligature support.

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Conformance](#2-conformance)
3. [Terminology](#3-terminology)
4. [Data Model](#4-data-model)
5. [Coordinate System and Metric Zones](#5-coordinate-system-and-metric-zones)
6. [Element Vocabulary](#6-element-vocabulary)
7. [Anchor Points](#7-anchor-points)
8. [Composition Operators](#8-composition-operators)
9. [Transform Operators](#9-transform-operators)
10. [Element Definitions (Block Form)](#10-element-definitions-block-form)
11. [Character Definitions](#11-character-definitions)
12. [Expression Grammar](#12-expression-grammar)
13. [Case Mapping, Script Tags, and Orthography](#13-case-mapping-script-tags-and-orthography)
14. [Ligatures](#14-ligatures)
15. [Diacritic Mark Vocabulary](#15-diacritic-mark-vocabulary)
16. [Style Transforms](#16-style-transforms)
17. [Extensibility](#17-extensibility)
18. [Security Considerations](#18-security-considerations)
19. [References](#19-references)
20. [Appendix A: Script Coverage Registry](#appendix-a-script-coverage-registry)
21. [Appendix B: Standard Element Library](#appendix-b-standard-element-library)
22. [Appendix C: Standard Diacritic Library](#appendix-c-standard-diacritic-library)
23. [Appendix D: Complete Example File](#appendix-d-complete-example-file)
24. [Appendix E: Script and Orthography Tag Registry](#appendix-e-script-and-orthography-tag-registry)

---

## 1. Introduction

### 1.1 Motivation

Existing standards and formats for Latin, Greek, and Cyrillic
characters each address a different concern and leave structural
composition undescribed:

Unicode assigns code points to characters. It encodes identity
("this is U+00E9 LATIN SMALL LETTER E WITH ACUTE") but says
nothing about how the character is built from an e-shape and an
acute mark, or how the e-shape itself is composed from arcs and
a crossbar.

Font formats (OpenType, TrueType) store flattened cubic or
quadratic outlines. The anatomical structure (stems, bowls, arcs,
serifs, diacritics) is destroyed during font compilation. There
is no way to recover "this glyph is STACK(ascender, bowl.r)" from
the outline data.

Typographic references (letter anatomy charts, type design
textbooks) annotate characters with structural terminology, but
these are informal descriptions, not constructive grammars. They
cannot be evaluated to produce geometry.

OpenType's GDEF/GPOS/GSUB tables encode glyph substitution and
positioning rules for rendering engines, but these are
layout-engine directives, not structural descriptions of how
characters are built from parts.

LSDL occupies the missing layer: a constructive language that
takes anatomical element primitives, reusable named components,
anchor-based attachment, and composition operators as input, and
produces deterministic geometric descriptions of character
structure as output.

### 1.2 Goals

The language is designed to satisfy the following goals:

**Constructive.** An LSDL expression can be evaluated to produce
element geometry. It is not an annotation; it is a build
specification.

**Deterministic.** The same input MUST always produce the same
output. There are no stochastic, context-dependent, or
implementation-defined evaluation behaviors.

**Non-Turing.** LSDL has no loops, variables, conditionals,
recursion, or macros. A character definition is a finite directed
acyclic graph (DAG) of nodes. Evaluation is a single pass: resolve
references, compute bounding boxes, align anchors, place children,
emit element geometry. Evaluation always terminates.

**Terse.** Approximately 90% of characters can be described in a
single line (higher than CSDL's 85% because diacritic composition
via DIA is extremely compact). The remaining characters use
multi-line block form for complex element definitions.

**Composable.** Elements are reusable. An element defined once can
be referenced by name in any number of character definitions.

**Closed.** All operator sets (elements, compositions, transforms)
are enumerated and closed. An implementation MUST reject unknown
operators. This prevents dialect fragmentation and guarantees that
any conformant parser can process any conformant LSDL file.

**Metric-aware.** Unlike CSDL's uniform bounding box, LSDL
integrates a vertical metric system (baseline, x-height, ascender
line, descender line, cap height) that reflects the fundamental
architecture of bicameral alphabetic scripts.

**Anchor-based.** Composition operates through named anchor points
on elements (top, base, mid, mark-above, mark-below, attach)
rather than through grid partitioning alone. This reflects how
alphabetic characters are structurally assembled: parts attach at
specific points, not in spatial quadrants.

### 1.3 Scope

LSDL describes the structural composition of characters in
bicameral alphabetic scripts. Its primary targets are:

- **Latin script:** Basic Latin through Latin Extended-E and Latin
  Extended Additional (approximately 1400 characters).
- **Greek script:** Greek and Coptic, Greek Extended
  (approximately 400 characters).
- **Cyrillic script:** Cyrillic through Cyrillic Extended-D
  (approximately 500 characters).
- **Combining marks:** Combining Diacritical Marks and extensions
  (approximately 200 marks).

LSDL also provides extensibility hooks for structurally adjacent
scripts that share the bicameral model, such as Armenian,
Georgian, and Coptic (see Section 17.3 and Appendix E).

An optional `script:` tag allows authors to annotate definitions
with their script using ISO 15924 codes. An optional `ortho:` tag
allows annotation with orthographic tradition using ISO 639
language codes. Renderers MAY use these tags for variant selection
but MUST NOT require them for evaluation.

LSDL does not address:

- Glyph rendering (anti-aliasing, hinting, rasterization)
- Font metrics beyond the vertical metric zones (advance widths,
  kerning, horizontal metrics)
- Text layout (line breaking, justification, bidi)
- Character encoding or identification (handled by Unicode)
- Stroke animation or temporal sequencing
- Aesthetic or calligraphic style variation (beyond the `@style`
  transform hook)

LSDL output is a tree of positioned elements in a coordinate
space. A renderer MAY transform this output into filled outlines,
SVG paths, bitmap images, or any other representation.

### 1.4 Design Principles

**Principle 1: Enumerate, don't generate.** Anatomical elements
are named primitives in a closed registry, not runtime
compositions of geometric operations. This eliminates an entire
class of combinatorial ambiguity.

**Principle 2: Composition is attachment, not partition.** Unlike
CJK characters that tile spatially, alphabetic characters compose
by attaching elements at anchor points along a vertical metric.
LSDL's composition model reflects this: STACK aligns along a
vertical axis, DIA attaches at anchor points, FRAME assembles from
named attachment positions.

**Principle 3: Variants are named, not computed.** Contextual
variants of elements (e.g., bowl.l vs bowl.r, stem.cyr,
sigma.final) are explicitly named. Variant selection is a renderer
RECOMMENDATION, not a requirement.

**Principle 4: Diacritics are first-class.** Unlike CJK (where
diacritics are rare), alphabetic scripts depend heavily on
diacritic composition. LSDL provides dedicated DIA and DIA2
operators and a standard diacritic vocabulary rather than treating
marks as an afterthought.

**Principle 5: Case is structural metadata.** Alphabetic scripts
have case pairs. LSDL records these as @case declarations, not as
implicit naming conventions.

---

## 2. Conformance

### 2.1 Key Words

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in
this document are to be interpreted as described in [BCP 14]
[RFC 2119] [RFC 8174] when, and only when, they appear in all
capitals, as shown here.

### 2.2 Conformance Levels

LSDL defines three conformance levels. Each level subsumes the
requirements of all lower levels.

**Level 1 (Parser).** A Level 1 conformant implementation MUST:

- Parse LSDL files according to the grammar in Section 12.
- Validate that all element references are resolvable.
- Validate that the element reference graph is acyclic.
- Validate that all operators are members of the closed sets
  defined in Sections 6, 8, and 9.
- Validate that all numeric parameters are within their
  specified bounds.
- Validate that all anchor names referenced in compositions are
  defined on the referenced elements.
- Reject any input that violates the above constraints.

**Level 2 (Renderer).** A Level 2 conformant implementation MUST
additionally:

- Resolve all element references to their definitions.
- Compute bounding boxes for all nodes in the expression DAG.
- Resolve anchor point alignment between composed elements.
- Place child nodes within parent bounding boxes according to
  composition operator semantics and anchor resolution rules.
- Emit element geometry as positioned path segments with
  specified width values.

**Level 3 (Full).** A Level 3 conformant implementation MUST
additionally:

- Expand element geometry to filled outlines (closed paths
  suitable for rendering as filled regions).

### 2.3 Error Handling

Error recovery strategy (stop at first error, collect all
diagnostics, attempt partial output) is implementation-defined.
Error reporting format (human-readable messages, structured JSON,
error codes, line/column references) is implementation-defined.
This specification does not constrain error recovery or error
reporting behavior. A conformant implementation MUST correctly
reject invalid input; how it reports, formats, or recovers from
errors is a local decision.

### 2.4 Partial Conformance

An implementation that satisfies some but not all requirements of a
conformance level MUST NOT claim conformance to that level. An
implementation MAY claim conformance to a lower level while noting
specific additional capabilities from higher levels.

---

## 3. Terminology

**anchor point**
: A named coordinate on an element where other elements may
  attach. Anchors are the primary mechanism for composition
  alignment in LSDL. See Section 7.

**baseline**
: The horizontal reference line on which characters sit. In the
  default metric system, baseline is at y=8. See Section 5.

**bounding box**
: A rectangular region in the coordinate system defined by its
  top-left corner and bottom-right corner. Every node in an LSDL
  expression has a bounding box.

**case mapping**
: A declaration that associates an uppercase character definition
  with its lowercase counterpart (and optionally a final form).
  See Section 13.3.

**character definition**
: An LSDL expression that describes a complete character by its
  literal Unicode character, its Unicode character name, and a
  structural expression.

**composition operator**
: One of the 8 structural composition operators (STACK, LR, LR3,
  DIA, DIA2, OVR, FRAME, LIG) that combine elements into
  characters. See Section 8.

**DAG**
: Directed Acyclic Graph. The reference structure of an LSDL
  expression, where nodes are elements or compositions and edges
  are references from parent to child.

**diacritic**
: A combining mark that attaches to a base character via the DIA
  or DIA2 operator. Diacritics are elements with an `attach`
  anchor. See Section 15.

**element**
: A named, reusable structural primitive that can be referenced
  by name in character definitions and other element compositions.
  Elements are the leaf-level building blocks of LSDL (analogous
  to strokes in CSDL). See Section 6.

**expression**
: An LSDL construct that evaluates to element geometry within a
  bounding box. Expressions are either element references,
  composition operator applications, or transform operator
  applications.

**grid unit**
: The fundamental unit of the LSDL coordinate system. One grid
  unit equals 1/12th of the containing bounding box dimension.

**inline form**
: A character definition expressed as a single line of LSDL.

**block form**
: An element definition expressed as multiple lines delimited by
  `@elem`/`@end` markers.

**ligature**
: A single glyph representing two or more characters joined
  together, described by the LIG operator. See Section 14.

**metric zone**
: A named vertical region of the coordinate space (cap, ascender,
  x-height, descender, diacritic-above, diacritic-below). See
  Section 5.

**path**
: A sequence of line-to and curve-to segments defining the
  geometric shape of a leaf element. See Section 10.2.

**positional variant**
: A named variant of an element that specifies its form in a
  particular structural context (e.g., bowl.l for left-side bowl,
  stem.cyr for Cyrillic stem). Expressed using dotted name syntax.

**script tag**
: An ISO 15924 script code (e.g., Latn, Grek, Cyrl) indicating
  the script a definition belongs to. See Section 13.

**split**
: A numeric parameter to layout operators that specifies how the
  parent bounding box is divided among children. The renderer
  divides the parent box proportionally according to the split
  values.

**transform operator**
: One of the 3 geometric modification operators (sc, sh, sk) that
  alter the scale, position, or skew of a child expression. See
  Section 9.

---

## 4. Data Model

### 4.1 Overview

An LSDL file is a UTF-8 encoded, line-oriented text file
containing a sequence of definitions. Definitions are of seven
kinds:

1. **Metric declarations** define the vertical metric system for
   the file.
2. **Alias definitions** bind an ASCII name to an element or
   character name.
3. **Element definitions** define named, reusable structural
   primitives in block form.
4. **Character definitions** define complete characters, either in
   inline form (one line) or block form (multiple lines).
5. **Case mapping declarations** associate uppercase and lowercase
   character pairs.
6. **Style declarations** define transform presets for stylistic
   variants.
7. **Comments** are lines beginning with `#`.

### 4.2 File Structure

An LSDL file MUST be encoded as UTF-8 [RFC 3629] without BOM.
Line endings MUST be LF (U+000A) or CR LF (U+000D U+000A); a
conformant parser MUST accept both.

Horizontal whitespace (U+0020 SPACE and U+0009 TAB) is
interchangeable wherever the grammar permits `WS`. Leading and
trailing whitespace on any line is not significant.

All Unicode text in an LSDL file SHOULD be in NFC [UAX #15].
Element name matching operates on the raw code point sequence;
a conformant parser MUST NOT apply normalization during name
resolution. A parser MAY reject a file containing non-NFC text.

The conventional file extension for LSDL files is `.lsdl`. The
proposed media type is `text/lsdl` (see Section 19.2).

An LSDL file SHOULD begin with a format declaration as its first
non-comment, non-blank line:

    @lsdl 1.0

A Level 1 parser that encounters an `@lsdl` declaration with a
major version it does not support MUST reject the file. A parser
that encounters an `@lsdl` declaration with a recognized major
version but an unknown minor version SHOULD issue a warning and
continue processing. If no `@lsdl` declaration is present, a
parser SHOULD assume version 1.0.

Blank lines and comment lines MAY appear anywhere in the file.
Comment lines begin with `#` as the first non-whitespace character.

### 4.2.1 Version Compatibility Contract

A minor version increment (e.g., 1.0 to 1.1) indicates additions
that do not alter the meaning of existing constructs. Specifically,
a minor version MAY add new metadata fields, new script or
orthography tags, and new entries to the appendix registries. A
minor version MUST NOT add new element names, composition
operators, or transform operators.

A major version increment (e.g., 1.x to 2.0) is required for any
change that would cause a conformant v1 parser to reject a
previously valid file, or that alters the evaluated geometry of an
existing construct. Adding a new element name or operator to the
closed registries is a major version change, because a v1 parser
enforcing the closed set will reject files that use the new name.

A Level 1 parser conformant to version N.x MUST accept any file
declared as version N.y where y >= x, ignoring unknown metadata
fields and unknown script or orthography tags. It MUST reject
files declared as version M.z where M > N.

### 4.2.2 Multi-File Composition

LSDL does not define an import, include, or file-reference
mechanism. Each LSDL file is a self-contained unit for parsing
purposes; all element names referenced in a file MUST be defined
or aliased within that same file.

In practice, toolchains will maintain shared element libraries
(e.g., a base file containing the standard ~45 element definitions
and ~30 diacritic definitions) and concatenate or merge them with
character definition files before parsing. This concatenation is
a tooling concern and is outside the scope of this specification.
A concatenated result MUST be a valid LSDL file (single `@lsdl`
declaration, single optional `@metrics` declaration, no duplicate
element names except as permitted by Section 4.5).

### 4.3 Expression DAG

Every character definition evaluates to a finite DAG. The nodes of
the DAG are:

- **Element nodes** (leaves): invoke a named element primitive with
  its path geometry, anchors, and width.
- **Composition nodes** (internal): apply a composition operator to
  1 or more child expressions with anchor alignment.
- **Transform nodes** (internal): apply a transform operator to
  exactly 1 child expression.
- **Reference nodes** (internal, resolved): reference a named
  element or previously defined character, which is itself a DAG.

After reference resolution, the complete structure is a tree (since
each reference is expanded to its own copy of the referenced
sub-DAG for evaluation purposes). The DAG structure exists at the
definition level; the evaluated structure is a tree.

### 4.4 Acyclicity Constraint

The element reference graph MUST be acyclic. That is, no element
definition MAY reference itself, directly or indirectly. A Level 1
conformant implementation MUST detect and reject cycles.

Formally: let G = (V, E) where V is the set of all defined
elements and E contains an edge (a, b) if element a references
element b. G MUST be a DAG.

### 4.5 Duplicate Element Definitions

An LSDL file MAY contain multiple `@elem` blocks with the same
element name. When duplicates exist, the last definition in file
order wins. A conformant parser MAY issue a warning on duplicate
element names but MUST NOT reject the file.

### 4.6 Metadata

Character definitions MAY include metadata fields. Metadata is
informational and MUST NOT affect evaluation. The following
metadata fields are defined:

- `script:` ISO 15924 script code (e.g., Latn, Grek, Cyrl)
- `ortho:` Orthography/language tag(s) (ISO 639 codes)
- `block:` Unicode block name
- `cp:` Explicit Unicode code point (U+XXXX)
- `freq:` Frequency rank within script (positive integer)

Additional metadata fields MAY be defined by implementations but
MUST be prefixed with `x-` to avoid collision with future standard
fields.

### 4.7 Script Tags

LSDL defines an optional script tag (`script:`) that indicates the
script a definition belongs to. Script tags use ISO 15924 codes.

#### 4.7.1 Tag Format

A script tag value MUST be a valid ISO 15924 script code as
registered in the IANA Language Subtag Registry. The primary
codes used by LSDL are:

| Tag    | Script Name      | LSDL Usage                      |
|--------|------------------|---------------------------------|
| `Latn` | Latin            | Latin script characters         |
| `Grek` | Greek            | Greek script characters         |
| `Cyrl` | Cyrillic         | Cyrillic script characters      |
| `Armn` | Armenian         | Armenian (extension)            |
| `Geor` | Georgian         | Georgian (extension)            |
| `Copt` | Coptic           | Coptic (extension)              |

Tags are case-sensitive. Authors MUST use the canonical casing
defined in Appendix E.

#### 4.7.2 Semantics

Script tags are metadata. They MUST NOT affect evaluation. An LSDL
expression produces identical geometric output regardless of the
presence or value of a `script:` tag.

Renderers MAY use script tags for variant selection and filtering.
Renderers MUST NOT reject definitions that lack a `script:` tag.

#### 4.7.3 Orthography Tags

Orthography tags (`ortho:`) indicate the language or orthographic
tradition using ISO 639 language codes, comma-separated:

    é  LATIN-SMALL-E-ACUTE = DIA(e, acute) script:Latn ortho:Fra,Spa,Por

Orthography tags are informational. They enable renderers to
filter definitions by language context but MUST NOT affect
evaluation.

### 4.8 File-Level Declarations

An LSDL file MAY contain a `@metrics` block defining the vertical
metric system (see Section 5.3). This block MUST appear before any
element or character definition.

An LSDL file MAY contain any number of `@style` blocks defining
transform presets (see Section 16).

---

## 5. Coordinate System and Metric Zones

### 5.1 Grid

The LSDL coordinate system divides the bounding box into a 12×12
grid of integer coordinates. The grid geometry is identical to
CSDL.

- The origin `[0,0]` is at the top-left corner.
- The X axis increases to the right.
- The Y axis increases downward.
- `[12,12]` is the bottom-right corner.
- `[6,6]` is the center.

The value 12 is chosen because it is divisible by 2, 3, 4, and 6.

### 5.2 Vertical Metric Zones

Unlike CSDL's uniform bounding box, LSDL maps the vertical axis
to named typographic landmarks. These landmarks define the metric
zones that govern element placement.

The default metric assignment is:

| Landmark       | y-value | Description                              |
|----------------|---------|------------------------------------------|
| `cap-top`      | 0       | Top of capital letters and diacritics    |
| `ascender`     | 1       | Top of ascender strokes (b, d, h, k, l) |
| `cap-height`   | 2       | Top of capital letter body               |
| `x-top`        | 4       | Top of lowercase body (x-height line)    |
| `baseline`     | 8       | Reference line on which characters sit   |
| `descender`    | 10      | Bottom of descender strokes (g, p, q, y) |
| `desc-limit`   | 12      | Absolute bottom (descender clearance)    |

These landmarks define the following zones:

| Zone              | y-start | y-end | Used by                                |
|-------------------|---------|-------|----------------------------------------|
| `diacritic-above` | 0       | 2     | Diacritics above capitals              |
| `ascender`        | 1       | 4     | b, d, f, h, k, l, β                   |
| `cap`             | 0       | 8     | A, B, C … Z, Α, Β … Ω, А, Б … Я     |
| `x-height`        | 4       | 8     | a, c, e, m, n, o … lowercase body      |
| `baseline`        | 8       | 8     | Reference line (zero height)           |
| `descender`       | 8       | 11    | g, p, q, y, β, ξ, ψ                   |
| `diacritic-below` | 9       | 12    | cedilla, ogonek, underdot              |

### 5.3 @metrics Declaration

The default metric values MAY be overridden at file scope using
a `@metrics` block:

    @metrics
    cap-top: 0
    ascender: 1
    cap-height: 2
    x-top: 4
    baseline: 8
    descender: 10
    desc-limit: 12
    @end

A `@metrics` block MUST appear before any `@elem` or character
definition in the file. Only one `@metrics` block is permitted
per file. If no `@metrics` block is present, the default values
apply.

All metric landmark values MUST be non-negative integers not
exceeding 12. The values MUST be monotonically non-decreasing in
the order listed (cap-top ≤ ascender ≤ cap-height ≤ x-top ≤
baseline ≤ descender ≤ desc-limit).

Scripts with unusual vertical proportions (e.g., Georgian, with
a different ascender-to-x-height ratio) override via `@metrics`
at file scope.

### 5.4 Horizontal Axis

The horizontal axis spans 0 to 12, left to right, with no named
landmarks. Horizontal positioning is governed by element anchors
and composition operator splits, not by metric zones.

### 5.5 /24 Override

For elements that require finer positioning than the 12-unit grid
provides, a coordinate MAY be specified in 24ths by appending `/24`
to the `@elem` declaration:

    @elem element_name /24
    ...
    @end

Within a /24 block, all path coordinates use the 24-unit grid.
Composition operators and transform operators are unaffected; they
continue to use 12-unit splits.

The default grid for all `@elem` blocks is `/12` (the standard
12-unit grid). The `/12` specifier is implicit and SHOULD NOT
appear in an LSDL file.

### 5.6 Element Width

Element width (stroke weight) is specified as an integer value:

- `0` = hairline
- `1` = normal weight
- `2` = bold weight

Implementations MAY map these values to pixel widths, em-relative
widths, or other concrete measures as appropriate for the output
format.

---

## 6. Element Vocabulary

### 6.1 Overview

Elements are the atomic anatomical parts of alphabetic glyphs.
Every character is built from approximately 45 named elements
drawn from the following categories.

### 6.2 Verticals

| Element       | Description                            | Typical y-span         |
|---------------|----------------------------------------|------------------------|
| `stem`        | Vertical straight stroke               | x-height or cap        |
| `ascender`    | Stem extending above x-height          | ascender → baseline    |
| `descender`   | Stem extending below baseline          | x-top → descender      |
| `full-stem`   | Full-height stem                       | ascender → descender   |

### 6.3 Curves

| Element        | Description                    | Notes                              |
|----------------|--------------------------------|------------------------------------|
| `bowl`         | Closed round form              | as in b, d, p, q, o, О            |
| `bowl.upper`   | Upper half-bowl                | as in B (top), β (top)             |
| `bowl.lower`   | Lower half-bowl                | as in B (bottom), β (bottom)       |
| `counter`      | Interior of a bowl             | implicit; not drawn                |
| `arc.top`      | Open curve, top half           | as in c, s (top), С                |
| `arc.bot`      | Open curve, bottom half        | as in s (bottom), ε (bottom)       |
| `hook.top`     | Curved entry at top            | as in f, Γ                         |
| `hook.bot`     | Curved exit at bottom          | as in j, J                         |
| `loop`         | Closed curve below baseline    | as in g (double-storey)            |
| `ear`          | Small projection               | as in g (single-storey), r         |
| `shoulder`     | Arch from stem                 | as in h, m, n                      |
| `ogee`         | S-curve                        | as in integral, ξ                  |

### 6.4 Horizontals and Diagonals

| Element         | Description                      | Notes                          |
|-----------------|----------------------------------|--------------------------------|
| `crossbar`      | Horizontal stroke                | as in A, H, e, f, Н           |
| `bar.top`       | Bar at top of glyph              | as in T, Г, Т                 |
| `bar.bot`       | Bar at bottom of glyph           | as in L, Ц                    |
| `bar.mid`       | Bar at x-height                  | as in e (crossbar), G          |
| `arm`           | Horizontal projecting from stem  | as in E, F, K, Е, Ж           |
| `leg`           | Diagonal descending from junction| as in K, R, k                  |
| `diagonal`      | Full-height diagonal             | as in N, Z, И                  |
| `apex`          | Meeting point of two diagonals   | as in A, Λ, Л                 |
| `vertex`        | Bottom meeting of diagonals      | as in V, W                     |
| `spine`         | Central S-curve                  | as in S, s, З                  |
| `tail`          | Terminal flourish                | as in Q, Щ                     |
| `stroke.diag`   | Overlay diagonal slash           | as in Ø, ø                    |
| `stroke.horiz`  | Overlay horizontal bar           | as in ł, Ħ, đ                 |

### 6.5 Terminals

| Element  | Description                     | Notes                        |
|----------|---------------------------------|------------------------------|
| `serif`  | Perpendicular terminal          | style-dependent              |
| `spur`   | Small serif-like projection     | as in b, G                   |
| `ball`   | Circular terminal               | as in a, c, f, r (some styles)|
| `finial` | Tapered terminal                | as in e, c                   |
| `swash`  | Extended decorative terminal    | style-dependent              |
| `flag`   | Small horizontal at top of stem | as in 1, ь                   |
| `tittle` | Dot above                       | as in i, j                   |

### 6.6 Special

| Element        | Description                    | Notes                         |
|----------------|--------------------------------|-------------------------------|
| `dot`          | Period/point                   | standalone dot                |
| `caron.alt`    | Vertical stroke (háček variant)| as in ď, ť, Ľ                |
| `comma.shape`  | Comma-shaped mark              | as in Cyrillic palatal marks  |

### 6.7 Element Name Registry

The complete set of element names defined in Sections 6.2 through
6.6 constitutes the closed element registry for LSDL v1.0. A
Level 1 parser MUST reject any element reference that is not a
member of this registry, a defined variant (Section 10.5), or a
registered alias (Section 10.7).

Variant tags (`.tag` suffixes) are open-ended. Authors MAY
introduce new variant tags as needed without specification-level
changes. Common variant tags include:

| Tag      | Meaning                                    |
|----------|--------------------------------------------|
| `.l`     | Left-side variant                          |
| `.r`     | Right-side variant                         |
| `.upper` | Upper portion                              |
| `.lower` | Lower portion                              |
| `.full`  | Full/complete form                         |
| `.cyr`   | Cyrillic-specific form                     |
| `.greek` | Greek-specific form                        |
| `.final` | Word-final form (e.g., Greek final sigma)  |
| `.curved`| Curved variant                             |
| `.angled`| Angled variant                             |

---

## 7. Anchor Points

### 7.1 Overview

Anchors are named coordinates on elements where other elements
attach. They are the primary mechanism for composition alignment
in LSDL, distinguishing it from CSDL's grid-partitioning approach.

Every element definition MUST declare at least one anchor point.
Anchors are declared on the `anchors:` line of an `@elem` block.

### 7.2 Standard Anchor Names

The following anchor names are defined as standard. Elements
SHOULD use these names where applicable:

| Anchor Name    | Description                                    |
|----------------|------------------------------------------------|
| `top`          | Top connection point                           |
| `base`         | Bottom/baseline connection point               |
| `mid`          | Vertical midpoint                              |
| `attach`       | General attachment point (used by diacritics)  |
| `mark-above`   | Diacritic attachment above                     |
| `mark-below`   | Diacritic attachment below                     |
| `arm.left`     | Left arm connection                            |
| `arm.right`    | Right arm connection                           |
| `top-serif`    | Top serif attachment                           |
| `bot-serif`    | Bottom serif attachment                        |
| `left`         | Left edge connection                           |
| `right`        | Right edge connection                          |

Anchor names are open-ended lowercase ASCII identifiers with
optional dot separators. Authors MAY define custom anchor names.

### 7.3 Anchor Resolution Rules

When composition operators combine elements, anchors are resolved
according to the following rules:

1. **DIA resolution.** The DIA operator attaches the diacritic's
   `attach` anchor to the base element's `mark-above` anchor (for
   above-marks) or `mark-below` anchor (for below-marks). The
   direction is inferred from the diacritic's zone declaration:
   elements in `diacritic-above` zone attach to `mark-above`;
   elements in `diacritic-below` zone attach to `mark-below`.
   Through-marks (zone `x-height` with overlay semantics) are
   centered on the base element's bounding box.

2. **STACK resolution.** The STACK operator aligns elements
   vertically using `top` and `base` anchors. The first element's
   `base` anchor aligns with the second element's `top` anchor.

3. **LR resolution.** The LR operator aligns elements horizontally
   on the baseline using `base` anchors.

4. **FRAME resolution.** The FRAME operator uses explicitly named
   anchors from its component elements.

### 7.4 Explicit Anchor Override

The default anchor resolution MAY be overridden using explicit
anchor syntax in composition expressions:

    DIA(o, acute, attach:top-right)

---

## 8. Composition Operators

### 8.1 Overview

LSDL defines 8 composition operators that combine elements into
characters. These operators differ structurally from CSDL's spatial
tiling operators because alphabetic characters compose by
attachment rather than partition.

### 8.2 STACK (Vertical Stacking)

    STACK(a, b)
    STACK(a, b, c, ...)

Stacks elements along a shared vertical axis, top to bottom. The
y-zones are inferred from element type declarations unless
overridden. The first element's `base` anchor aligns with the
second element's `top` anchor.

Example: `STACK(ascender, bowl.r)` produces the structure of `b`.

Example: `STACK(ascender.curved, bowl.r.upper, bowl.r.lower)`
produces the structure of `β`.

### 8.3 LR (Left-Right)

    LR(a, b)
    LR(a, b, split)
    LR(a, b, c, ..., split)

Places elements side by side, left to right, aligned on the
baseline. Like CSDL's LR, with proportional splits. Default
split for two elements is 6/6 (equal halves).

Example: `LR(bowl.l, ascender, 7/5)` produces the structure
of `d`.

Split values are proportional; the renderer divides the parent
box according to the ratio of the values. Values summing to 12
align with grid unit boundaries and SHOULD be preferred.

Note: LR in LSDL accepts variable numbers of children (unlike
CSDL which uses separate LR and LR3 operators). When more than
three children are provided, a corresponding multi-part split
MUST be provided.

### 8.4 LR3 (Three-Part Horizontal)

    LR3(a, b, c)
    LR3(a, b, c, split)

Syntactic convenience equivalent to LR with three children.
Default split is 4/4/4 (equal thirds). LR3 is provided for
compatibility with CSDL's naming convention and to make three-part
compositions visually distinct.

### 8.5 DIA (Diacritic Attachment)

    DIA(base, mark)
    DIA(base, mark, attach:ANCHOR_NAME)

Attaches a diacritic mark to a base character or element. The
mark's `attach` anchor aligns with the base's `mark-above` or
`mark-below` anchor (direction inferred from mark zone; see
Section 7.3).

DIA is the most frequently used operator in LSDL. Approximately
half of all Latin Extended characters are base+diacritic
compositions:

    é  = DIA(e, acute)
    ç  = DIA(c, cedilla)
    ö  = DIA(o, diaeresis)

The base argument MAY be any expression, including a previously
defined character name. This enables chained composition.
However, DIA2 (Section 8.6) is preferred for multi-diacritic
compositions.

### 8.6 DIA2 (Double Diacritic Attachment)

    DIA2(base, mark1, mark2)

Attaches two diacritic marks to a base character. The first mark
attaches closest to the base; the second mark stacks outward from
the first.

    ắ  = DIA2(a, breve, acute)       # breve then acute above
    ǭ  = DIA2(o, ogonek, macron)     # ogonek below, macron above

DIA2 is semantically equivalent to nested DIA but provides a
single-expression syntax for the common case of two diacritics.

### 8.7 OVR (Overlay)

    OVR(a, b)

Places child `b` on top of child `a` within the same bounding box.
Both children occupy the full parent box. OVR is used for
characters where components are superimposed.

    Ø  = OVR(O, stroke.diag)
    ł  = OVR(l, stroke.horiz)

### 8.8 FRAME (Assembled from Attachment Points)

    FRAME(part1, part2, ...)

Assembles a character from named parts positioned at their defined
anchor points. Unlike STACK (which assumes vertical alignment) and
LR (which assumes horizontal adjacency), FRAME places each part
according to its own anchor definitions without imposing a single
axis of composition.

    e  = FRAME(arc.top, crossbar, arc.bot)
    П  = FRAME(stem.l, bar.top, stem.r)
    Д  = FRAME(stem.l.angled, bar.top, stem.r.angled, foot.l, foot.r)

A conformant renderer resolves the spatial arrangement by matching
corresponding anchors between parts.

### 8.9 APEX (Diagonal Meeting Point)

    APEX(stem1, stem2, ...)
    APEX(stem1, stem2, crossbar, ...)

Semantic alias for FRAME with the convention that the first two
arguments are diagonal stems meeting at a top point, and
subsequent arguments are horizontal elements. APEX exists for
readability when describing characters like A, Λ, Л.

    A  = APEX(stem.l, stem.r, crossbar)

---

## 9. Transform Operators

### 9.1 Overview

LSDL defines 3 transform operators identical to CSDL's transforms.
They modify the geometry of a child expression. Transform
operators take a single child expression and produce a modified
version within a bounding box.

All transform parameters are bounded integers in the range -12 to
24 inclusive. The upper bound of 24 equals 2× the grid dimension.
Transform parameters always operate in the 12-unit grid space,
even when applied to children defined in `/24` blocks.

Scale (`sc`) and skew (`sk`) transforms are applied relative to
the center of the child expression's bounding box (i.e., point
`[6,6]` in the child's coordinate space). Shift (`sh`) is a
translation and has no anchor point.

When transforms are nested, evaluation proceeds inside-out
(standard function composition). Implementations MUST NOT
reorder transforms.

### 9.2 sc (Scale)

    sc(expr, sx=N, sy=N)

Scales the child expression. `sx` and `sy` are scale factors
expressed as fractions of 12. A value of 12 means no scaling
(100%), 6 means 50%, 18 means 150%.

Example: `sc(bowl, sx=8, sy=8)` renders bowl at 2/3 size.

### 9.3 sh (Shift)

    sh(expr, dx=N, dy=N)

Shifts the child expression by `dx` grid units horizontally and
`dy` grid units vertically. Positive `dx` shifts right, positive
`dy` shifts down.

Example: `sh(dot, dx=0, dy=-2)` shifts dot two units up.

### 9.4 sk (Skew)

    sk(expr, kx=N, ky=N)

Applies a skew transformation. `kx` skews horizontally (positive
values tilt the top to the right), `ky` skews vertically.

Example: `sk(stem, kx=2, ky=0)` applies italic lean.

---

## 10. Element Definitions (Block Form)

### 10.1 Block Form

Elements are defined using `@elem` / `@end` delimiters:

    @elem element_name
    zone: ZONE_NAME
    path: p1 p2 ...
    p1 = [x,y]
    p2 = [x,y]
    ...
    close: true|false
    width: WIDTH
    anchors: name=[x,y] name=[x,y] ...
    @end

### 10.2 Path Syntax

Three point types are supported:

**Line-to:** `[x,y]` — a straight line segment to the specified
coordinate.

**Quadratic curve-to:** `C([cx,cy] [x,y])` — a quadratic Bézier
curve with one control point and endpoint.

**Cubic curve-to:** `C([c1x,c1y] [c2x,c2y] [x,y])` — a cubic
Bézier curve with two control points and an endpoint.

Coordinates are on the 12×12 grid (or 24×24 for `/24` blocks).
If `close: true`, the path closes back to the first point.

### 10.3 Zone Declaration

The `zone:` declaration specifies which vertical metric zone the
element occupies. Valid zone names are:

| Zone Name          | Description                              |
|--------------------|------------------------------------------|
| `cap`              | Full capital height (0 to baseline)      |
| `x-height`         | Lowercase body (x-top to baseline)       |
| `ascender`         | Ascender zone (ascender to baseline)     |
| `descender`        | Descender zone (x-top to descender)      |
| `full`             | Full vertical extent (0 to 12)           |
| `diacritic-above`  | Above diacritics zone                    |
| `diacritic-below`  | Below diacritics zone                    |

### 10.4 Example: stem

    @elem stem
    zone: x-height
    path: p1 p2
    p1 = [6,4]
    p2 = [6,8]
    width: 1
    anchors: top=[6,4] base=[6,8] mid=[6,6]
      arm.left=[0,6] arm.right=[12,6]
      mark-above=[6,3] mark-below=[6,9]
      top-serif=[6,3] bot-serif=[6,9]
    @end

### 10.5 Positional Variants

An element MAY have multiple positional variants, each defined as
a separate `@elem` block with a dotted name:

    @elem bowl       # default (right-side)
    ...
    @end

    @elem bowl.l     # left-side
    ...
    @end

    @elem bowl.full  # full round (as in o)
    ...
    @end

When a character definition references `bowl`, a renderer MAY
substitute a variant based on structural context. An author who
requires a specific variant SHOULD use the variant name explicitly.

### 10.6 Expression Form

An element MAY be defined by a composition or transform expression
over other elements:

    @elem compound_name
    build: from_expr
    COMPOSITION_EXPR
    @end

An `@elem` block MUST contain either path geometry OR a
`build: from_expr` line, not both. A `/24` block MUST NOT use
`build: from_expr`.

### 10.7 Aliases

Alias definitions bind an ASCII name to an element or character
name:

    @alias stem-with-right-bowl = b.shape
    @alias o-shape = bowl.full
    @alias yu = Ю

Script-qualified aliases prevent collisions between scripts that
share visual forms:

    @alias Latn:H = H    # Latin H
    @alias Grek:H = Η    # Greek Eta
    @alias Cyrl:H = Н    # Cyrillic En

An alias name MUST NOT collide with any element name defined in
the same file. A Level 1 parser MUST reject such collisions.

---

## 11. Character Definitions

### 11.1 Inline Form

The inline form defines a character on a single line:

    CHAR  UNICODE_NAME  =  EXPR  [METADATA...]

The `CHAR` is the literal Unicode character. The `UNICODE_NAME` is
the Unicode character name with spaces replaced by hyphens. The
`EXPR` is a composition, transform, or element reference.

Examples:

    A  LATIN-CAPITAL-A      = APEX(stem.l, stem.r, crossbar)
    b  LATIN-SMALL-B        = STACK(ascender, bowl.r)
    é  LATIN-SMALL-E-ACUTE  = DIA(e, acute)
    Ø  LATIN-CAPITAL-O-STROKE = OVR(O, stroke.diag) script:Latn ortho:Dan,Nor
    П  CYRILLIC-CAPITAL-PE  = FRAME(stem.l, bar.top, stem.r) script:Cyrl
    β  GREEK-SMALL-BETA     = STACK(ascender.curved, bowl.r.upper, bowl.r.lower) script:Grek

### 11.2 Block Form

Characters requiring complex internal structure use block form:

    @char CHAR UNICODE_NAME
    build: from_expr
    EXPR
    [METADATA]
    @end

Or for leaf characters defined by explicit path geometry:

    @char CHAR UNICODE_NAME
    zone: ZONE_NAME
    path: p1 p2 ...
    p1 = [x,y]
    ...
    width: WIDTH
    anchors: ...
    [METADATA]
    @end

### 11.3 Metadata

Metadata fields appear after the expression (inline form) or as
separate lines before `@end` (block form). Metadata is
informational; it does not affect evaluation.

Standard metadata fields:

| Field      | Type              | Description                          |
|------------|-------------------|--------------------------------------|
| `script:`  | ISO 15924 code    | Script code (Latn, Grek, Cyrl)       |
| `ortho:`   | ISO 639 code(s)   | Orthography/language tag(s)          |
| `block:`   | name              | Unicode block name                   |
| `cp:`      | U+XXXX            | Explicit Unicode code point          |
| `freq:`    | 1+                | Frequency rank within script         |

Extension metadata fields MUST use the `x-` prefix.

### 11.4 Character-Element Equivalence

When a character definition uses a literal character glyph as its
identifier, and an `@elem` block defines an element with that same
character as its name, the element definition serves double duty:
it is both a reusable element for composition and the character
definition for the corresponding Unicode code point. An explicit
`@char` definition takes precedence over an implicit
element-derived definition.

---

## 12. Expression Grammar

This section defines the complete formal grammar of LSDL using
W3C-style EBNF notation. All productions are finite; there is no
recursion except through named element references, which are
constrained to be acyclic (Section 4.4).

### 12.1 Notation

The grammar uses W3C EBNF notation as defined in the XML
specification [W3C XML], Section 6. The same notation conventions
as CSDL Section 6.1 apply.

### 12.2 Lexical Productions

```ebnf
(* Whitespace and line structure *)
WS          ::= ( #x20 | #x09 )+
NL          ::= #x0A | ( #x0D #x0A )
BLANK_LINE  ::= WS? NL
COMMENT     ::= WS? '#' [^#x0A#x0D]* NL

(* Basic tokens *)
DIGIT       ::= [0-9]
LETTER      ::= [a-zA-Z]
INT         ::= '-'? DIGIT+
UINT        ::= DIGIT+

(* Unicode code point label *)
CODEPOINT   ::= 'U+' [0-9A-Fa-f] [0-9A-Fa-f] [0-9A-Fa-f] [0-9A-Fa-f]
                ( [0-9A-Fa-f] [0-9A-Fa-f] )?

(* Unicode character name: uppercase ASCII letters, digits, hyphens *)
UNAME       ::= [A-Z] [A-Z0-9-]*

(* Literal Unicode character: any printable scalar value in the
   Unicode blocks listed in Appendix A. Informative note: the
   following ranges reflect the blocks relevant to LSDL. *)
LITERAL_CHAR ::= [#x0021-#x007E]
               | [#x00A0-#x024F]
               | [#x0370-#x052F]
               | [#x1AB0-#x1AFF]
               | [#x1C80-#x1C8F]
               | [#x1DC0-#x1DFF]
               | [#x1E00-#x1EFF]
               | [#x1F00-#x1FFF]
               | [#x2C60-#x2C7F]
               | [#x2DE0-#x2DFF]
               | [#xA640-#xA7FF]
               | [#xAB30-#xAB6F]
               | [#xFB00-#xFB06]
               | [#x1E030-#x1E08F]
               | [#x20D0-#x20FF]

(* Element names *)
ELEM_NAME   ::= [a-z] [a-z0-9]*
VARIANT_TAG ::= '.' [a-z] [a-z0-9]*
FULL_ELEM   ::= ( ELEM_NAME | LITERAL_CHAR ) ( VARIANT_TAG )*

(* Anchor name *)
ANCHOR_NAME ::= [a-z] [a-z0-9]* ( '.' [a-z] [a-z0-9]* )*
```

### 12.3 Coordinate and Path Productions

```ebnf
COORD       ::= '[' UINT ',' UINT ']'
GRID_SPEC   ::= '/24' | '/12'
WIDTH       ::= '0' | '1' | '2'

LINE_TO     ::= COORD
QUAD_CURVE  ::= 'C(' COORD WS COORD ')'
CUBIC_CURVE ::= 'C(' COORD WS COORD WS COORD ')'
PATH_POINT  ::= LINE_TO | QUAD_CURVE | CUBIC_CURVE
```

### 12.4 Split Productions

```ebnf
SPLIT_2     ::= UINT '/' UINT
SPLIT_3     ::= UINT '/' UINT '/' UINT
SPLIT_N     ::= UINT ( '/' UINT )+
```

### 12.5 Composition Operator Productions

```ebnf
ANCHOR_OVR  ::= 'attach:' ANCHOR_NAME
MERGE_PARAM ::= 'merge:' [a-z] [a-z0-9-]*

STACK_EXPR  ::= 'STACK(' EXPR ( ',' WS? EXPR )+ ')'
LR_EXPR     ::= 'LR(' EXPR ',' WS? EXPR ( ',' WS? EXPR )*
                  ( ',' WS? SPLIT_N )? ')'
LR3_EXPR    ::= 'LR3(' EXPR ',' WS? EXPR ',' WS? EXPR
                  ( ',' WS? EXPR )* ( ',' WS? SPLIT_N )? ')'
DIA_EXPR    ::= 'DIA(' EXPR ',' WS? EXPR
                  ( ',' WS? ANCHOR_OVR )? ')'
DIA2_EXPR   ::= 'DIA2(' EXPR ',' WS? EXPR ',' WS? EXPR ')'
OVR_EXPR    ::= 'OVR(' EXPR ',' WS? EXPR ')'
FRAME_EXPR  ::= 'FRAME(' EXPR ( ',' WS? EXPR )+ ')'
LIG_EXPR    ::= 'LIG(' EXPR ',' WS? EXPR
                  ( ',' WS? MERGE_PARAM )? ')'
APEX_EXPR   ::= 'APEX(' EXPR ( ',' WS? EXPR )+ ')'

COMPOSE_EXPR ::= STACK_EXPR | LR_EXPR | LR3_EXPR
               | DIA_EXPR | DIA2_EXPR
               | OVR_EXPR | FRAME_EXPR | LIG_EXPR
               | APEX_EXPR
```

### 12.6 Transform Operator Productions

```ebnf
TPARAM      ::= INT   /* constrained: -12 <= value <= 24 */

SC_EXPR     ::= 'sc(' EXPR ',' WS? 'sx=' TPARAM ',' WS? 'sy=' TPARAM ')'
SH_EXPR     ::= 'sh(' EXPR ',' WS? 'dx=' TPARAM ',' WS? 'dy=' TPARAM ')'
SK_EXPR     ::= 'sk(' EXPR ',' WS? 'kx=' TPARAM ',' WS? 'ky=' TPARAM ')'

XFORM_EXPR  ::= SC_EXPR | SH_EXPR | SK_EXPR
```

### 12.7 Expression Production

```ebnf
EXPR        ::= COMPOSE_EXPR | XFORM_EXPR | FULL_ELEM
```

### 12.8 Definition Productions

```ebnf
ALIAS_DEF   ::= '@alias' WS ( LETTER+ ':' )? FULL_ELEM WS '=' WS
                ( FULL_ELEM | LITERAL_CHAR ) NL

META_SCRIPT ::= 'script:' WS? LETTER LETTER LETTER LETTER
META_ORTHO  ::= 'ortho:' WS? LETTER+ ( ',' LETTER+ )*
META_BLOCK  ::= 'block:' WS? [^#x0A#x0D]+
META_CP     ::= 'cp:' WS? CODEPOINT
META_FREQ   ::= 'freq:' WS? UINT
META_EXT    ::= 'x-' LETTER+ ':' WS? [^#x0A#x0D]+
METADATA    ::= META_SCRIPT | META_ORTHO | META_BLOCK
              | META_CP | META_FREQ | META_EXT

METRIC_LINE ::= LETTER+ ( '-' LETTER+ )* ':' WS? UINT
METRICS_BLOCK ::= '@metrics' NL ( METRIC_LINE NL )+ '@end' NL

CASE_DEF    ::= '@case' WS LITERAL_CHAR WS LITERAL_CHAR
                ( WS 'final:' LITERAL_CHAR )? NL

STYLE_BLOCK ::= '@style' WS [a-z]+ NL
                'transform:' WS XFORM_EXPR NL '@end' NL

ZONE_NAME   ::= 'cap' | 'x-height' | 'ascender' | 'descender'
              | 'full' | 'diacritic-above' | 'diacritic-below'

PATH_ID     ::= [a-z] [a-z0-9]*
PATH_DEF    ::= PATH_ID WS '=' WS PATH_POINT
ANCHOR_DEF  ::= ANCHOR_NAME '=' COORD

ELEM_BLOCK  ::= '@elem' WS FULL_ELEM ( WS GRID_SPEC )? NL
                'zone:' WS ZONE_NAME NL
                'path:' WS PATH_ID ( WS PATH_ID )* NL
                ( PATH_DEF NL )+
                ( 'close:' WS ('true' | 'false') NL )?
                'width:' WS WIDTH NL
                'anchors:' WS ANCHOR_DEF ( WS ANCHOR_DEF )* NL
                ( WS ANCHOR_DEF ( WS ANCHOR_DEF )* NL )*
                ( METADATA NL )* '@end' NL

ELEM_EXPR_BLOCK ::= '@elem' WS FULL_ELEM NL
                    'build:' WS 'from_expr' NL EXPR NL
                    ( METADATA NL )* '@end' NL

CHAR_INLINE ::= LITERAL_CHAR WS UNAME WS '=' WS EXPR
                ( WS METADATA )* NL

CHAR_BLOCK  ::= '@char' WS LITERAL_CHAR WS UNAME NL
                ( 'build:' WS 'from_expr' NL EXPR NL
                | 'zone:' WS ZONE_NAME NL
                  'path:' WS PATH_ID ( WS PATH_ID )* NL
                  ( PATH_DEF NL )+
                  ( 'close:' WS ('true' | 'false') NL )?
                  'width:' WS WIDTH NL
                  'anchors:' WS ANCHOR_DEF ( WS ANCHOR_DEF )* NL
                  ( WS ANCHOR_DEF ( WS ANCHOR_DEF )* NL )* )
                ( METADATA NL )* '@end' NL

FORMAT_DECL ::= '@lsdl' WS DIGIT+ '.' DIGIT+ NL

DEFINITION  ::= ALIAS_DEF | ELEM_BLOCK | ELEM_EXPR_BLOCK
              | CHAR_INLINE | CHAR_BLOCK | CASE_DEF | STYLE_BLOCK

LSDL_FILE   ::= FORMAT_DECL? METRICS_BLOCK?
                ( DEFINITION | COMMENT | BLANK_LINE )*
```

### 12.9 Semantic Constraints

The following constraints are not expressible in the EBNF grammar
and MUST be enforced by a conformant Level 1 parser.

1. All split values MUST be positive integers. Values summing
   to 12 SHOULD be preferred.
2. All `TPARAM` values MUST be in the range -12 to 24 inclusive.
3. All `WIDTH` values MUST be 0, 1, or 2.
4. All coordinate values in standard blocks MUST be 0 to 12.
5. All coordinate values in `/24` blocks MUST be 0 to 24.
6. All `FULL_ELEM` references MUST resolve to a defined element,
   alias, or previously defined character.
7. The element reference graph MUST be acyclic.
8. All element names in compositions MUST be members of the closed
   element registry, defined variants, registered aliases, or
   previously defined characters.
9. An `@elem` block with `build: from_expr` MUST contain exactly
   one `EXPR` line and zero path definitions.
10. An `@elem` block with path geometry MUST contain `zone:`,
    path point definitions, `width:`, and `anchors:`.
11. An `@elem` block MUST NOT specify both `/24` and
    `build: from_expr`.
12. All `ZONE_NAME` values MUST be members of the zone registry.
13. The `@metrics` block, if present, MUST appear before any
    `@elem`, `@char`, or `@alias` definition.
14. Only one `@metrics` block is permitted per file.
15. All metric landmark values MUST be non-negative integers ≤ 12,
    in monotonically non-decreasing order.
16. All `script:` tag values MUST be valid ISO 15924 codes.
17. Alias names MUST NOT collide with element or other alias names.
18. `@case` declarations MUST reference characters defined in the
    same file.
19. LR/LR3 with N element children MUST have a split with exactly
    N values if a split is provided.
20. `DIA` MUST have 2 or 3 arguments.
21. `DIA2` MUST have exactly 3 arguments.
22. `FRAME` MUST have at least 2 child expressions.
23. `LIG` MUST have 2 or 3 arguments.

---

## 13. Case Mapping, Script Tags, and Orthography

### 13.1 Overview

Bicameral alphabetic scripts pair uppercase and lowercase forms of
the same abstract character. LSDL records these pairings as
structural metadata via `@case` declarations so that tools can
traverse case relationships without relying on the Unicode
Character Database. Script and orthography tags (introduced in
Section 4.7) annotate definitions with their script and language
context.

This section is the normative reference for `@case` declaration
semantics. Script and orthography tag semantics are defined in
Section 4.7; this section provides additional guidance on their
interaction with case mapping and variant selection.

### 13.2 Case Mapping Declarations

A case mapping declaration associates an uppercase character
definition with its lowercase counterpart:

    @case UPPER LOWER
    @case UPPER LOWER final:FINAL

The `UPPER` and `LOWER` arguments are literal Unicode characters
that MUST correspond to character definitions (inline or block
form) in the same file. A Level 1 parser MUST reject a `@case`
declaration that references an undefined character.

Examples:

    @case A a
    @case E e
    @case Σ σ final:ς

### 13.3 Final Forms

Some scripts have positional variants beyond the uppercase/
lowercase pair. Greek final sigma (ς) is the primary example in
LSDL's target repertoire. The optional `final:` parameter records
a word-final variant:

    @case Σ σ final:ς

The `final:` character MUST also be defined in the same file.
A `@case` declaration MAY include at most one `final:` parameter.

### 13.4 Case Mapping Constraints

1. Each uppercase character MUST appear in at most one `@case`
   declaration. Duplicate uppercase entries are an error.
2. Each lowercase character MUST appear in at most one `@case`
   declaration as the lowercase member. (A lowercase character
   MAY appear as a `final:` member in a different declaration.)
3. `@case` declarations MAY appear anywhere in the file after the
   `@metrics` block (if present) but SHOULD be grouped together
   for readability.
4. `@case` declarations are metadata. They MUST NOT affect
   evaluation of character expressions. The geometric output of
   a character is identical regardless of whether it participates
   in a `@case` declaration.
5. `@case` declarations are not transitive. If `@case A a` and
   `@case A á` both appeared, the second would be rejected by
   constraint (1). To express that `á` is a variant of `a`, use
   the `ortho:` tag or application-level metadata.

### 13.5 Script Tags and Case Mapping

When both members of a `@case` pair include `script:` tags, the
tags SHOULD be identical. A renderer MAY issue a warning if an
uppercase character is tagged `script:Latn` and its lowercase
counterpart is tagged `script:Grek`, but MUST NOT reject the file
on this basis.

### 13.6 Orthography Tags and Variant Selection

Orthography tags (`ortho:`) are informational metadata that
enable renderers to filter or select definitions by language
context. Their semantics are defined in Section 4.7.3.

When a character exists in multiple orthographic traditions with
different structural forms (e.g., Bulgarian Cyrillic italic
variants vs. Russian Cyrillic forms), each variant SHOULD be
defined as a separate character definition with distinct `ortho:`
tags. A renderer MAY select among orthographic variants based on
language context but MUST NOT require orthography tags for
evaluation.

Example: Serbian Cyrillic lowercase б has a different structural
form in italic than Russian б. Both are defined separately:

    б  CYRILLIC-SMALL-BE     = ... script:Cyrl ortho:Rus
    б  CYRILLIC-SMALL-BE     = ... script:Cyrl ortho:Srp

When duplicate character definitions exist (same literal
character), the renderer selects based on `ortho:` context. If no
orthographic context is available, the last definition in file
order applies (consistent with Section 4.5).

### 13.7 Case Mapping and Diacritics

A `@case` declaration maps between two complete character
definitions. When a lowercase character is a diacritic composition
(e.g., `é = DIA(e, acute)`), the `@case` declaration maps the
uppercase character (É) to the composed lowercase form. The
`@case` mechanism is oblivious to the internal structure of the
character definitions it maps; it operates solely on the literal
Unicode character identifiers.

    É  LATIN-CAPITAL-E-ACUTE = DIA(E, acute) script:Latn
    é  LATIN-SMALL-E-ACUTE   = DIA(e, acute) script:Latn
    @case É é

A `@case` declaration MUST NOT be used to express relationships
between a base character and its diacritic compositions (e.g.,
mapping `e` to `é`). Such relationships are outside the scope of
case mapping and belong to orthographic or application-level
metadata.

### 13.8 Case Folding

LSDL does not define a case folding algorithm. Case folding
(converting a character to a canonical case form for comparison)
is a text processing operation outside LSDL's scope. The `@case`
declarations provide the structural data from which a toolchain
MAY derive case folding tables, but LSDL itself specifies no
folding semantics.

### 13.9 Grammar

The grammar production for `@case` is defined in Section 12.8:

```ebnf
CASE_DEF    ::= '@case' WS LITERAL_CHAR WS LITERAL_CHAR
                ( WS 'final:' LITERAL_CHAR )? NL
```

Semantic constraint 18 (Section 12.9) requires that all literal
characters in a `@case` declaration reference characters defined
in the same file.

---

## 14. Ligatures

### 14.1 Overview

A ligature is a single glyph representing two or more characters
joined together. Ligatures are structurally distinct from
compositions: a composition builds a single character from
anatomical parts, while a ligature merges two or more complete
characters into a combined form.

LSDL describes ligatures using the LIG operator (Section 8). This
section defines the semantics of ligature definitions and the
`merge:` parameter vocabulary.

### 14.2 Ligature Definitions

A ligature is defined using the LIG operator in a character
definition:

    CHAR UNICODE_NAME = LIG(char1, char2) [METADATA]
    CHAR UNICODE_NAME = LIG(char1, char2, merge:STRATEGY) [METADATA]

The first two arguments are expressions (typically character
references) representing the component characters. The optional
`merge:` parameter specifies the structural strategy by which the
components are joined.

Examples:

    ﬁ  LATIN-SMALL-LIGATURE-FI = LIG(f, i, merge:hook-tittle) cp:U+FB01
    ﬂ  LATIN-SMALL-LIGATURE-FL = LIG(f, l, merge:hook-ascender) cp:U+FB02
    Æ  LATIN-CAPITAL-AE = LIG(A, E, merge:stem-shared) cp:U+00C6
    Œ  LATIN-CAPITAL-OE = LIG(O, E, merge:bowl-stem) cp:U+0152

### 14.3 The merge: Parameter

The `merge:` parameter identifies the structural strategy used to
join two characters into a ligature. Merge strategies describe
which anatomical elements are shared, absorbed, or replaced when
the characters combine.

The merge strategy name is a lowercase ASCII identifier composed
of element names or structural descriptions joined by hyphens.
The name is descriptive: it tells a renderer (or human reader)
what structural operation produces the ligature.

### 14.4 Standard Merge Strategies

The following merge strategies are defined for LSDL v1.0. This
registry is open-ended; authors MAY introduce new merge strategy
names without specification-level changes.

| Strategy          | Description                                    | Example        |
|-------------------|------------------------------------------------|----------------|
| `hook-tittle`     | The f-hook absorbs the i-tittle; the f's       | ﬁ (fi)         |
|                   | terminal replaces the i's dot.                 |                |
| `hook-ascender`   | The f-hook merges into the l-ascender;          | ﬂ (fl)         |
|                   | shared vertical at the junction.               |                |
| `stem-shared`     | The right stem of the first character is the   | Æ (AE)         |
|                   | left stem of the second; a single stem         |                |
|                   | serves both.                                   |                |
| `bowl-stem`       | The right curve of the first character merges  | Œ (OE)         |
|                   | into the left stem of the second.              |                |

### 14.5 Merge Strategy Semantics

A merge strategy is a RECOMMENDATION to the renderer. The
strategy name identifies the structural intent of the ligature
but does not prescribe exact geometry. A conformant Level 2
renderer SHOULD implement the described structural merge but MAY
fall back to horizontal adjacency (equivalent to LR) if it does
not recognize the strategy.

When `merge:` is omitted, the default behavior is horizontal
adjacency: the two characters are placed side by side with no
structural merging, equivalent to `LR(char1, char2)`.

### 14.6 Ligature Code Points

Ligature definitions SHOULD include an explicit `cp:` metadata
field with the Unicode code point of the ligature character.
Because ligatures map to the Alphabetic Presentation Forms block
(U+FB00–U+FB06) or to characters with dedicated code points
(Æ at U+00C6, Œ at U+0152, etc.), the `cp:` field ensures
unambiguous identification.

### 14.7 Ligature Constraints

1. LIG MUST have exactly 2 expression arguments, plus an optional
   `merge:` parameter. (This is a restatement of Section 12.9
   constraint 23.)
2. The `merge:` parameter value MUST match the production
   `[a-z][a-z0-9-]*`.
3. A ligature definition MUST have a literal Unicode character
   identifier, like any character definition.
4. The component arguments to LIG MAY be any expression, including
   element references, character references, or composition
   expressions. In practice, they are nearly always character
   references.
5. The merge strategy registry is open-ended. A Level 1 parser
   MUST accept any syntactically valid merge strategy name. A
   Level 2 renderer MAY issue a warning for unrecognized strategies
   but MUST NOT reject the file.

### 14.8 Ligature and Case Mapping Interaction

When a ligature has both uppercase and lowercase forms (e.g.,
Æ/æ, Œ/œ), both forms SHOULD be defined as separate LIG
expressions and linked via a `@case` declaration:

    Æ  LATIN-CAPITAL-AE = LIG(A, E, merge:stem-shared) cp:U+00C6
    æ  LATIN-SMALL-AE   = LIG(a, e, merge:stem-shared) cp:U+00E6
    @case Æ æ

The `@case` declaration maps between the composed ligature forms,
not between the component characters. The renderer is not required
to infer case relationships between ligature components.

### 14.9 Ligature vs. OVR Disambiguation

Ligatures (LIG) and overlays (OVR) both combine two expressions
into a single glyph, but they differ structurally:

LIG combines two complete characters that are placed side by side
(or structurally merged) along the horizontal axis. The result
replaces a multi-character sequence with a single glyph. LIG
presupposes that the components are independent characters that
happen to be joined.

OVR superimposes two expressions in the same bounding box along
the z-axis (depth). The result is a single character with an
overlay element. OVR presupposes that the base and overlay are
parts of one character, not two independent characters.

The distinction matters for semantic decomposition: a LIG
decomposes into two characters (fi → f + i), while an OVR
decomposes into a character and a modifier (Ø → O + stroke).

### 14.10 Grammar

The grammar production for LIG is defined in Section 12.5:

```ebnf
MERGE_PARAM ::= 'merge:' [a-z] [a-z0-9-]*
LIG_EXPR    ::= 'LIG(' EXPR ',' WS? EXPR
                  ( ',' WS? MERGE_PARAM )? ')'
```

---

## 15. Diacritic Mark Vocabulary

### 15.1 Overview

Diacritics are combining marks that attach to base characters via
the DIA and DIA2 operators (Sections 8.5 and 8.6). LSDL treats
diacritics as first-class elements: they are defined using `@elem`
blocks, occupy diacritic zones, and carry an `attach` anchor that
aligns with the base character's `mark-above` or `mark-below`
anchor.

This section defines the structural requirements for diacritic
elements and the standard diacritic vocabulary. The complete
registry is in Appendix C.

### 15.2 Diacritic Element Requirements

A diacritic element MUST satisfy all of the following:

1. **Zone declaration.** The element MUST declare one of the
   following zones: `diacritic-above`, `diacritic-below`, or
   `x-height` (for through-marks). The zone declaration
   determines anchor resolution behavior in DIA (Section 7.3).

2. **Attach anchor.** The element MUST define an `attach` anchor.
   This anchor aligns with the base character's `mark-above`
   anchor (for `diacritic-above` zone), `mark-below` anchor (for
   `diacritic-below` zone), or is centered on the base bounding
   box (for `x-height` zone through-marks).

3. **Path geometry.** The element MUST define path geometry (it
   MUST NOT use `build: from_expr`). Diacritics are leaf
   elements.

### 15.3 Diacritic Placement

#### 15.3.1 Above Marks

When a diacritic in zone `diacritic-above` is composed with a
base via DIA, the diacritic's `attach` anchor aligns with the
base's `mark-above` anchor. The diacritic is positioned above
the base character.

If the base element does not define a `mark-above` anchor, the
renderer MUST fall back to centering the diacritic horizontally
above the base bounding box, with the diacritic's `attach`
anchor placed at the top edge of the base bounding box.

#### 15.3.2 Below Marks

When a diacritic in zone `diacritic-below` is composed with a
base via DIA, the diacritic's `attach` anchor aligns with the
base's `mark-below` anchor. The diacritic is positioned below
the base character.

If the base element does not define a `mark-below` anchor, the
renderer MUST fall back to centering the diacritic horizontally
below the base bounding box, with the diacritic's `attach`
anchor placed at the bottom edge of the base bounding box.

#### 15.3.3 Through Marks

A diacritic in zone `x-height` used with DIA is treated as a
through-mark (e.g., a combining stroke). The diacritic is
centered on the base element's bounding box center point. Through-
mark placement is semantically equivalent to OVR but accessed via
the DIA operator for uniform syntax in character definitions.

#### 15.3.4 Bounding Box Expansion

When a diacritic is composed with a base via DIA or DIA2, the
resulting composition's bounding box MUST expand to enclose both
the base and the positioned diacritic. The horizontal extent of
the composition is the union of the base and diacritic horizontal
extents. The vertical extent is the union of the base and
diacritic vertical extents.

This expansion affects subsequent compositions that reference the
composed character. For example, if `é = DIA(e, acute)` is used
as the base in a STACK or LR composition, the STACK or LR
operator sees the expanded bounding box that includes the acute
mark.

### 15.4 Stacking Behavior

The "Stacking" column in Appendix C indicates whether a diacritic
may participate in DIA2 compositions (stacking outward from the
base). Diacritics marked `yes` for stacking are compatible with
DIA2. Diacritics marked `no` (such as `cedilla`, `ogonek`, `horn`)
typically occupy fixed positions relative to the base and do not
stack outward.

When DIA2 is used with two above-marks, the first mark (closer
to the base) is placed using standard DIA resolution. The second
mark is placed above the first mark, with its `attach` anchor
aligned to the first mark's topmost coordinate (y-minimum of the
first mark's bounding box), centered horizontally.

When DIA2 is used with one below-mark and one above-mark, the
below-mark attaches to `mark-below` and the above-mark attaches
to `mark-above`, independently. The order in the DIA2 expression
determines which is which: the first mark argument attaches
closest to the base.

When DIA2 is used with two below-marks, the first mark is placed
using standard DIA resolution to `mark-below`. The second mark is
placed below the first mark, with its `attach` anchor aligned to
the first mark's bottommost coordinate (y-maximum of the first
mark's bounding box), centered horizontally.

### 15.5 Diacritic Anchor Override

The default anchor resolution for DIA MAY be overridden using
explicit anchor syntax:

    DIA(o, acute, attach:top-right)

This attaches the diacritic's `attach` anchor to the base
element's `top-right` anchor instead of the default `mark-above`.
The named anchor MUST exist on the base element; a Level 1 parser
MUST reject the expression if it does not.

Anchor override is useful for diacritics that do not attach at the
standard mark position. The horn diacritic (ơ, ư), for example,
attaches to the upper-right of the base rather than centered
above:

    ơ  LATIN-SMALL-O-HORN = DIA(o, horn, attach:top-right) script:Latn ortho:Vie

### 15.6 Standard Diacritic Registry

The standard diacritic registry is defined in Appendix C. It
comprises 24 marks: 13 above, 8 below, and 3 through.

Diacritic elements are members of the closed element registry
(Section 6.7). Their names are reserved and MUST NOT be reused
for non-diacritic elements. The standard diacritic names are:

Above: `acute`, `grave`, `circumflex`, `tilde`, `diaeresis`,
`macron`, `breve`, `caron`, `ring`, `dot-above`, `double-acute`,
`horn`, `comma-above`.

Below: `cedilla`, `ogonek`, `dot-below`, `comma-below`,
`macron-below`, `line-below`, `breve-below`, `ring-below`.

Through: `stroke`, `stroke.diag`, `oblique-stroke`.

### 15.7 Extension Diacritics

Authors MAY define additional diacritic elements using `@elem`
blocks that satisfy the requirements of Section 15.2. Extension
diacritics MUST use names that do not collide with the standard
registry. Extension diacritics SHOULD use the `x-` prefix if
they are application-specific.

Extension diacritics that represent combining marks in the Unicode
standard (e.g., combining marks from the U+0300–U+036F block not
included in the standard registry) SHOULD use a descriptive name
derived from the Unicode character name and SHOULD include a `cp:`
metadata field on any character definition that uses them.

### 15.8 Diacritic-Only Characters

Some Unicode characters consist entirely of a combining mark with
no base character (e.g., the standalone forms of diacritics used
in phonetic notation). These MAY be defined as character
definitions whose expression is a bare element reference to the
diacritic element:

    ˊ  MODIFIER-LETTER-ACUTE = acute cp:U+02CA
    ˋ  MODIFIER-LETTER-GRAVE = grave cp:U+02CB

In these definitions, the diacritic element is used directly as
a character expression without the DIA operator, because there is
no base to attach to. The element's zone and path geometry define
the standalone glyph.

### 15.9 Vietnamese Diacritics

Vietnamese orthography makes extensive use of DIA2, combining
tone marks with base diacritics on vowels. The standard LSDL
diacritic vocabulary covers all Vietnamese combining marks. The
typical patterns are:

    ắ  = DIA2(a, breve, acute)
    ẳ  = DIA2(a, breve, hook-above)
    ẵ  = DIA2(a, breve, tilde)
    ố  = DIA2(o, circumflex, acute)
    ờ  = DIA2(o, horn, grave)

Vietnamese definitions SHOULD include `ortho:Vie` tags for
variant selection.

---

## 16. Style Transforms

### 16.1 Overview

LSDL provides a `@style` block mechanism for defining named
transform presets that can be applied to character definitions
as a group. Style transforms address simple, systematic geometric
modifications such as italic lean or optical weight adjustment
without requiring per-character redefinition.

### 16.2 Style Block Syntax

A style block defines a named transform preset:

    @style STYLE_NAME
    transform: XFORM_EXPR
    @end

The `STYLE_NAME` is a lowercase ASCII identifier (`[a-z]+`). The
`XFORM_EXPR` is a transform operator expression as defined in
Section 9 (sc, sh, or sk).

Example:

    @style italic
    transform: sk(*, kx=2, ky=0)
    @end

### 16.3 The Wildcard Target

Within a `@style` block, the special token `*` in the transform
expression represents "the target expression to which this style
will be applied." The `*` token is valid ONLY within `@style`
blocks; it MUST NOT appear in character definitions or element
definitions.

The `*` token occupies the EXPR position in the transform
operator. When a style is applied, the `*` is replaced by the
target expression.

### 16.4 Style Application

Style application is outside the scope of LSDL evaluation proper.
LSDL defines the style declaration; how and when styles are
applied is a tooling or rendering concern.

A typical application model: a tool reads the `@style italic`
declaration, then for each character in a specified set, wraps
the character's expression in the declared transform. For example,
applying `@style italic` to the character `b = STACK(ascender,
bowl.r)` would produce the evaluated equivalent of
`sk(STACK(ascender, bowl.r), kx=2, ky=0)`.

The tool MAY apply the style to all characters in the file, to
characters matching a `script:` filter, to characters in a
specified Unicode range, or to an explicitly enumerated character
list. The selection mechanism is a tooling decision. LSDL defines
only the transform preset, not its application scope.

### 16.5 Style Block Constraints

1. Style names MUST be unique within a file. Duplicate `@style`
   names are an error.
2. The transform expression MUST contain exactly one `*` token.
3. The `*` token MUST NOT appear outside `@style` blocks.
4. Style blocks MAY appear anywhere in the file after the
   `@metrics` block (if present).
5. A file MAY contain zero or more `@style` blocks.
6. Style blocks are metadata-adjacent: they define a reusable
   transform but do not by themselves alter any character's
   evaluated geometry. Evaluation output is identical whether or
   not `@style` blocks are present.
7. Transform nesting in style blocks follows the same rules as
   Section 9.1: evaluation is inside-out, implementations MUST
   NOT reorder transforms.

### 16.6 Compound Styles

A `@style` block contains exactly one `transform:` line. To
compose multiple transforms (e.g., italic lean plus condensed
scaling), nest the transform operators:

    @style italic-condensed
    transform: sk(sc(*, sx=9, sy=12), kx=2, ky=0)
    @end

In this example, the condensed scaling (`sc`) is applied first
(innermost), then the italic skew (`sk`) is applied to the
result. This follows the standard inside-out evaluation order
of Section 9.1.

Compound styles that require transforms applied in a specific
order MUST nest them in the correct order within a single
`transform:` line. There is no mechanism for composing multiple
`@style` blocks into a single compound style at the LSDL level;
such composition is a tooling concern.

### 16.7 Standard Style Names

The following style names are RECOMMENDED for interoperability.
Implementations SHOULD use these names for the described effects:

| Name          | Typical Transform            | Description            |
|---------------|------------------------------|------------------------|
| `italic`      | `sk(*, kx=2, ky=0)`         | Italic lean            |
| `bold`        | (element width adjustment)    | Bold weight            |
| `condensed`   | `sc(*, sx=9, sy=12)`        | Horizontally condensed |
| `extended`    | `sc(*, sx=15, sy=12)`       | Horizontally extended  |

Note: `bold` cannot be expressed as a pure geometric transform
because it requires changing element `width` values rather than
scaling outlines. The `bold` style name is reserved for
implementations that support width-level modification, but the
mechanism for doing so is outside the scope of LSDL v1.0. A
`@style bold` block SHOULD use `sc` as an approximation if
width modification is unavailable.

### 16.8 Style and Diacritics

When a style transform is applied to a character that includes
diacritics (i.e., a DIA or DIA2 composition), the transform
wraps the entire composition expression, including the diacritic.
This means the diacritic is transformed along with the base
character.

For example, applying `@style italic` to `é = DIA(e, acute)`
produces `sk(DIA(e, acute), kx=2, ky=0)`. Both the base `e`
and the `acute` mark receive the italic skew. This is the
correct behavior for most style transforms, since diacritics
should lean with their base characters in italic.

If a renderer requires diacritics to be excluded from a style
transform (e.g., to keep diacritics upright in italic), that
logic is a rendering concern outside the scope of LSDL. The
LSDL `@style` mechanism applies transforms uniformly to the
entire expression tree.

### 16.9 Style Transform Parameter Bounds

All transform parameters within `@style` blocks are subject to
the same bounds as transform operators in character definitions
(Section 9.1): all TPARAM values MUST be in the range -12 to 24
inclusive. A Level 1 parser MUST reject a `@style` block
containing out-of-range parameters.

### 16.10 Grammar

The grammar production for `@style` is defined in Section 12.8:

```ebnf
STYLE_BLOCK ::= '@style' WS [a-z]+ NL
                'transform:' WS XFORM_EXPR NL '@end' NL
```

The `*` wildcard token is valid only in the EXPR position within
the XFORM_EXPR of a STYLE_BLOCK. A conformant parser MUST reject
`*` in any other context.

---

## 17. Extensibility

### 17.1 Overview

LSDL is designed as a closed language: all operators, element
names, and zone names are enumerated in the specification. This
closure is a deliberate design choice that prevents dialect
fragmentation and guarantees universal parseability. However, the
language provides controlled extensibility points for adaptation
to new requirements without breaking existing parsers.

### 17.2 Extensibility Mechanisms

LSDL provides four extensibility mechanisms, ordered from most
constrained to least constrained:

**Variant tags (open-ended).** Element variant tags (`.tag`
suffixes as described in Section 6.7 and 10.5) are open-ended.
Authors MAY introduce new variant tags at any time without
specification changes. A variant tag creates a new element name
under an existing base element; it does not add a new base element
to the registry. Examples: `bowl.georgian`, `stem.italic`,
`hook.top.deep`.

**Extension metadata (open-ended).** Metadata fields prefixed with
`x-` (Section 4.6) are open-ended. Authors and implementations
MAY define custom metadata for application-specific purposes.
Extension metadata MUST NOT affect evaluation.

**Merge strategy names (open-ended).** The `merge:` parameter
vocabulary for the LIG operator (Section 14.4) is open-ended.
Authors MAY introduce new merge strategy names to describe novel
ligature joining strategies. Unrecognized strategies are a
renderer concern, not a parser error.

**Anchor names (open-ended).** Custom anchor names (Section 7.2)
are open-ended. Authors MAY define application-specific anchors on
elements.

### 17.3 Script Extension

LSDL's primary targets are Latin, Greek, and Cyrillic. Scripts
that share the bicameral alphabetic model (Armenian, Georgian,
Coptic) may be described using LSDL with the following
adaptations:

1. **Metric adjustment.** Override the default vertical metrics
   via `@metrics` to match the target script's proportions
   (Section 5.3). Georgian, for example, has different ascender
   and descender proportions than Latin.

2. **Element variants.** Define script-specific variants of
   existing elements using variant tags: `bowl.georgian`,
   `shoulder.armenian`, etc.

3. **Script tags.** Annotate definitions with the appropriate
   ISO 15924 script tag (Section 4.7).

Scripts that do not share the bicameral alphabetic model (e.g.,
Arabic, Devanagari, CJK) are outside LSDL's scope. CJK scripts
are addressed by CSDL.

### 17.4 Element Registry Extension

Adding a new base element name to the closed element registry
(Section 6.7) is a major version change (Section 4.2.1). A new
base element represents a fundamentally new anatomical category
not expressible as a variant of an existing element.

The process for proposing new base elements is outside the scope
of this specification. In general, a proposed element SHOULD
demonstrate that:

1. It represents a structural category used by multiple characters
   across the target scripts.
2. It cannot be adequately described as a variant of an existing
   element.
3. It has well-defined zone assignment, required anchors, and
   geometric semantics.

### 17.5 Operator Registry Extension

Adding a new composition or transform operator is a major version
change. New operators MUST NOT modify the semantics of existing
operators. A proposed operator SHOULD demonstrate that the
structural pattern it describes cannot be expressed as a
composition of existing operators.

### 17.6 Prohibited Extensions

The following extension patterns are prohibited:

1. **Conditional evaluation.** No mechanism for conditional
   expressions, feature tests, or if/else logic. LSDL remains
   non-Turing.
2. **Macros or templates.** No mechanism for parameterized
   definitions or macro expansion. Elements are defined, not
   generated.
3. **External references.** No import, include, or URL-based
   reference mechanism (Section 4.2.2).
4. **Runtime state.** No variables, accumulators, or evaluation
   state that persists across character definitions.

These prohibitions exist to maintain the guarantees of Section
1.2: determinism, termination, closed operator sets, and universal
parseability. Extensions that require any of these mechanisms
belong in a toolchain layer above LSDL, not in the language
itself.

### 17.7 Version Migration Path

When a future LSDL version introduces new elements, operators, or
other closed-registry additions, files authored against the new
version will be rejected by parsers conformant to the current
version. This is by design: the `@lsdl` version declaration
(Section 4.2) enables parsers to detect version mismatches and
report them clearly.

Toolchains that need to support files across LSDL versions SHOULD
implement multi-version parsing: read the `@lsdl` declaration,
select the appropriate parser version, and process accordingly.
A tool MUST NOT silently ignore unknown operators or element
names from a future version, as this would produce incorrect
geometric output.

Backward compatibility is guaranteed within a major version: a
file valid under LSDL 1.0 will remain valid under LSDL 1.x for
all x, because minor versions may only add metadata fields and
registry entries, not new operators or element names (Section
4.2.1).

### 17.8 Future Directions

The following areas are anticipated as potential targets for
future major versions, noted here for informational purposes
only:

1. Weight axis beyond the 0/1/2 system (a continuous or wider
   integer-range weight model).
2. A structural diff format for expressing how one character
   definition relates to another.
3. Explicit support for scripts beyond the bicameral alphabetic
   family that share enough structural properties with Latin/
   Greek/Cyrillic to benefit from the LSDL composition model.
4. Interpolation between element variants for optical size or
   weight variation (a mechanism analogous to OpenType variable
   font axes, expressed in LSDL's structural vocabulary rather
   than outline coordinates).

Such extensions MUST NOT modify the semantics of existing element
names or operators.

---

## 18. Security Considerations

LSDL is a declarative description language with no executable code,
no I/O, no network access, and no external process invocation.
Evaluation is bounded: the number of elements, tree depth, and
coordinate computations in the output are all linear in the input
size. There is no mechanism by which an LSDL input can cause
superlinear resource consumption.

Implementations SHOULD be capable of processing files covering the
complete Latin, Greek, and Cyrillic repertoires (approximately
2500 characters across all relevant Unicode blocks) and element
reference depths typical of that repertoire. Implementations MAY
impose stricter limits for constrained environments but SHOULD
document them.

---

## 19. References

### 19.1 Normative References

**[BCP 14]**
Best Current Practice 14. Comprises RFC 2119 and RFC 8174.

**[RFC 2119]**
Bradner, S., "Key words for use in RFCs to Indicate Requirement
Levels", BCP 14, RFC 2119, March 1997.

**[RFC 8174]**
Leiba, B., "Ambiguity of Uppercase vs Lowercase in RFC 2119
Key Words", BCP 14, RFC 8174, May 2017.

**[RFC 3629]**
Yergeau, F., "UTF-8, a transformation format of ISO 10646",
STD 63, RFC 3629, November 2003.

**[BCP 47]**
Phillips, A. and M. Davis, "Tags for Identifying Languages",
BCP 47, RFC 5646, September 2009.
https://www.rfc-editor.org/info/bcp47

**[Unicode]**
The Unicode Consortium, "The Unicode Standard", Version 16.0.0
(or later). https://www.unicode.org/versions/latest/

**[UAX #15]**
The Unicode Consortium, "Unicode Standard Annex #15: Unicode
Normalization Forms".
https://www.unicode.org/reports/tr15/

**[ISO 15924]**
ISO 15924:2004, Codes for the representation of names of scripts.
https://www.unicode.org/iso15924/

**[ISO 639]**
ISO 639-1:2002, Codes for the representation of names of
languages.

**[W3C XML]**
Bray, T. et al., "Extensible Markup Language (XML) 1.0 (Fifth
Edition)", W3C Recommendation, November 2008. Section 6:
Notation. https://www.w3.org/TR/xml/#sec-notation

### 19.2 Media Type

The proposed media type is `text/lsdl` with file extension `.lsdl`,
encoded as UTF-8 without BOM. IANA registration is deferred until
specification stability warrants it.

### 19.3 Companion Documents

**[LSDL-PRIMER]**
LSDL Primer — A Human-Writable Guide, Version 1.0 Draft,
2026-02-09. File: `lsdl-primer.md`

**[CSDL]**
CJK Stroke Description Language (CSDL) Specification, Version 1.0
Draft, 2026-02-09. File: `csdl-spec.md`

### 19.4 Informative References

**[OpenType]**
Microsoft Corporation, "OpenType Specification",
https://learn.microsoft.com/en-us/typography/opentype/spec/

---

## Appendix A: Script Coverage Registry

This appendix defines the Unicode blocks covered by LSDL.

### A.1 Latin

| Block Name                    | Range              | Approx. Count |
|-------------------------------|--------------------| --------------|
| Basic Latin (printable)       | U+0020–U+007E      | ~95           |
| Latin-1 Supplement            | U+0080–U+00FF      | ~96           |
| Latin Extended-A              | U+0100–U+017F      | 128           |
| Latin Extended-B              | U+0180–U+024F      | 208           |
| IPA Extensions                | U+0250–U+02AF      | 96            |
| Latin Extended Additional     | U+1E00–U+1EFF      | 256           |
| Latin Extended-C              | U+2C60–U+2C7F      | 32            |
| Latin Extended-D              | U+A720–U+A7FF      | 224           |
| Latin Extended-E              | U+AB30–U+AB6F      | 64            |

### A.2 Greek

| Block Name          | Range              | Approx. Count |
|---------------------|--------------------| --------------|
| Greek and Coptic    | U+0370–U+03FF      | 135           |
| Greek Extended      | U+1F00–U+1FFF      | 233           |

### A.3 Cyrillic

| Block Name             | Range              | Approx. Count |
|------------------------|--------------------| --------------|
| Cyrillic               | U+0400–U+04FF      | 256           |
| Cyrillic Supplement    | U+0500–U+052F      | 48            |
| Cyrillic Extended-A    | U+2DE0–U+2DFF      | 32            |
| Cyrillic Extended-B    | U+A640–U+A69F      | 96            |
| Cyrillic Extended-C    | U+1C80–U+1C8F      | 9             |
| Cyrillic Extended-D    | U+1E030–U+1E08F    | 63            |

### A.4 Combining Marks

| Block Name                              | Range              | Approx. Count |
|-----------------------------------------|--------------------| --------------|
| Combining Diacritical Marks             | U+0300–U+036F      | 112           |
| Combining Diacritical Marks Extended    | U+1AB0–U+1AFF      | 80            |
| Combining Diacritical Marks Supplement  | U+1DC0–U+1DFF      | 64            |
| Combining Marks for Symbols            | U+20D0–U+20FF      | 48            |

### A.5 Alphabetic Presentation Forms

| Block Name                        | Range              | Approx. Count |
|-----------------------------------|--------------------| --------------|
| Alphabetic Presentation Forms     | U+FB00–U+FB06      | 7 (ligatures) |

---

## Appendix B: Standard Element Library

This appendix lists all elements in the closed element registry
with their standard zone assignments and minimum anchor sets.

### B.1 Verticals (4 elements)

| Element      | Zone      | Required Anchors                          |
|--------------|-----------|-------------------------------------------|
| `stem`       | x-height  | top, base, mid, mark-above, mark-below    |
| `ascender`   | ascender  | top, base, mid, mark-above, mark-below    |
| `descender`  | descender | top, base, mid                            |
| `full-stem`  | full      | top, base, mid, mark-above, mark-below    |

### B.2 Curves (12 elements)

| Element       | Zone      | Required Anchors                          |
|---------------|-----------|-------------------------------------------|
| `bowl`        | x-height  | attach, mark-above, mark-below            |
| `bowl.upper`  | x-height  | attach, top, base                         |
| `bowl.lower`  | x-height  | attach, top, base                         |
| `counter`     | x-height  | (implicit; not drawn)                     |
| `arc.top`     | x-height  | left, right, top                          |
| `arc.bot`     | x-height  | left, right, base                         |
| `hook.top`    | ascender  | attach, base                              |
| `hook.bot`    | descender | attach, top                               |
| `loop`        | descender | attach, top                               |
| `ear`         | x-height  | attach                                    |
| `shoulder`    | x-height  | attach, top, base                         |
| `ogee`        | full      | top, base                                 |

### B.3 Horizontals and Diagonals (13 elements)

| Element         | Zone      | Required Anchors                         |
|-----------------|-----------|------------------------------------------|
| `crossbar`      | x-height  | left, right, mid                         |
| `bar.top`       | cap       | left, right                              |
| `bar.bot`       | x-height  | left, right                              |
| `bar.mid`       | x-height  | left, right                              |
| `arm`           | x-height  | attach                                   |
| `leg`           | x-height  | attach, base                             |
| `diagonal`      | cap       | top, base                                |
| `apex`          | cap       | top, left, right                         |
| `vertex`        | x-height  | base, left, right                        |
| `spine`         | x-height  | top, base                                |
| `tail`          | descender | attach                                   |
| `stroke.diag`   | x-height  | mid                                      |
| `stroke.horiz`  | x-height  | left, right                              |

### B.4 Terminals (7 elements)

| Element  | Zone      | Required Anchors |
|----------|-----------|------------------|
| `serif`  | (varies)  | attach           |
| `spur`   | (varies)  | attach           |
| `ball`   | (varies)  | attach           |
| `finial` | (varies)  | attach           |
| `swash`  | (varies)  | attach           |
| `flag`   | (varies)  | attach           |
| `tittle` | x-height  | attach           |

### B.5 Special (3 elements)

| Element        | Zone      | Required Anchors |
|----------------|-----------|------------------|
| `dot`          | (varies)  | attach           |
| `caron.alt`    | x-height  | attach           |
| `comma.shape`  | (varies)  | attach           |

### B.6 Summary

| Category                    | Count |
|-----------------------------|-------|
| Verticals                   | 4     |
| Curves                      | 12    |
| Horizontals and Diagonals   | 13    |
| Terminals                   | 7     |
| Special                     | 3     |
| **Total base elements**     | **39**|

(With standard variants, the effective count is approximately 45.)

---

## Appendix C: Standard Diacritic Library

### C.1 Above Marks (13)

| Name           | Zone             | Unicode Combining | Stacking |
|----------------|------------------|-------------------|----------|
| `acute`        | diacritic-above  | U+0301            | yes      |
| `grave`        | diacritic-above  | U+0300            | yes      |
| `circumflex`   | diacritic-above  | U+0302            | yes      |
| `tilde`        | diacritic-above  | U+0303            | yes      |
| `diaeresis`    | diacritic-above  | U+0308            | yes      |
| `macron`       | diacritic-above  | U+0304            | yes      |
| `breve`        | diacritic-above  | U+0306            | yes      |
| `caron`        | diacritic-above  | U+030C            | yes      |
| `ring`         | diacritic-above  | U+030A            | yes      |
| `dot-above`    | diacritic-above  | U+0307            | yes      |
| `double-acute` | diacritic-above  | U+030B            | yes      |
| `horn`         | diacritic-above  | U+031B            | no       |
| `comma-above`  | diacritic-above  | U+0313            | yes      |

### C.2 Below Marks (8)

| Name            | Zone             | Unicode Combining | Stacking |
|-----------------|------------------|-------------------|----------|
| `cedilla`       | diacritic-below  | U+0327            | no       |
| `ogonek`        | diacritic-below  | U+0328            | no       |
| `dot-below`     | diacritic-below  | U+0323            | yes      |
| `comma-below`   | diacritic-below  | U+0326            | no       |
| `macron-below`  | diacritic-below  | U+0331            | yes      |
| `line-below`    | diacritic-below  | U+0332            | yes      |
| `breve-below`   | diacritic-below  | U+032E            | yes      |
| `ring-below`    | diacritic-below  | U+0325            | yes      |

### C.3 Through Marks (3)

| Name             | Zone      | Unicode Combining | Stacking |
|------------------|-----------|-------------------|----------|
| `stroke`         | x-height  | U+0335/U+0336     | no       |
| `stroke.diag`    | x-height  | U+0337/U+0338     | no       |
| `oblique-stroke` | x-height  | U+0338            | no       |

### C.4 Summary

| Category       | Count |
|----------------|-------|
| Above marks    | 13    |
| Below marks    | 8     |
| Through marks  | 3     |
| **Total**      | **24**|

---

## Appendix D: Complete Example File

```lsdl
@lsdl 1.0

# Metrics (defaults; shown for clarity)
@metrics
cap-top: 0
ascender: 1
cap-height: 2
x-top: 4
baseline: 8
descender: 10
desc-limit: 12
@end

# ============================================================
# Aliases
# ============================================================

@alias acute = acute
@alias cedilla = cedilla
@alias Latn:H = H
@alias Grek:H = Η
@alias Cyrl:H = Н

# ============================================================
# Leaf Element Definitions
# ============================================================

@elem stem
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
width: 1
anchors: top=[6,4] base=[6,8] mid=[6,6]
  mark-above=[6,3] mark-below=[6,9]
@end

@elem stem.l
zone: cap
path: p1 p2
p1 = [2,0]
p2 = [2,8]
width: 1
anchors: top=[2,0] base=[2,8] mid=[2,4]
@end

@elem stem.r
zone: cap
path: p1 p2
p1 = [10,0]
p2 = [10,8]
width: 1
anchors: top=[10,0] base=[10,8] mid=[10,4]
@end

@elem ascender
zone: ascender
path: p1 p2
p1 = [6,1]
p2 = [6,8]
width: 1
anchors: top=[6,1] base=[6,8] mid=[6,4]
  mark-above=[6,0] mark-below=[6,9]
@end

@elem ascender.curved
zone: ascender
path: p1 p2 p3
p1 = [4,1]
p2 = C([8,1] [8,4])
p3 = [6,4]
width: 1
anchors: top=[4,1] base=[6,4] mid=[6,2]
@end

@elem bowl.r
zone: x-height
path: p1 p2 p3 p4
p1 = [6,4]
p2 = C([12,4] [12,8])
p3 = [6,8]
close: true
width: 1
anchors: attach=[6,6] mark-above=[8,3] mark-below=[8,9]
@end

@elem bowl.l
zone: x-height
path: p1 p2 p3 p4
p1 = [6,4]
p2 = C([0,4] [0,8])
p3 = [6,8]
close: true
width: 1
anchors: attach=[6,6] mark-above=[4,3] mark-below=[4,9]
@end

@elem bowl.r.upper
zone: x-height
path: p1 p2 p3
p1 = [6,4]
p2 = C([11,4] [11,6])
p3 = [6,6]
width: 1
anchors: attach=[6,5] top=[8,4] base=[8,6]
@end

@elem bowl.r.lower
zone: x-height
path: p1 p2 p3
p1 = [6,6]
p2 = C([12,6] [12,8])
p3 = [6,8]
width: 1
anchors: attach=[6,7] top=[8,6] base=[8,8]
@end

@elem crossbar
zone: x-height
path: p1 p2
p1 = [2,6]
p2 = [10,6]
width: 1
anchors: left=[2,6] right=[10,6] mid=[6,6]
@end

@elem bar.top
zone: cap
path: p1 p2
p1 = [2,0]
p2 = [10,0]
width: 1
anchors: left=[2,0] right=[10,0] mid=[6,0]
@end

@elem arc.top
zone: x-height
path: p1 p2 p3
p1 = [10,6]
p2 = C([10,4] [6,4])
p3 = [2,6]
width: 1
anchors: left=[2,6] right=[10,6] top=[6,4]
@end

@elem arc.bot
zone: x-height
path: p1 p2 p3
p1 = [2,6]
p2 = C([2,8] [6,8])
p3 = [10,8]
width: 1
anchors: left=[2,6] right=[10,8] base=[6,8]
@end

@elem stroke.diag
zone: x-height
path: p1 p2
p1 = [3,8]
p2 = [9,4]
width: 1
anchors: mid=[6,6]
@end

@elem stroke.horiz
zone: x-height
path: p1 p2
p1 = [2,6]
p2 = [10,6]
width: 1
anchors: left=[2,6] right=[10,6]
@end

# ============================================================
# Diacritic Definitions
# ============================================================

@elem acute
zone: diacritic-above
path: p1 p2
p1 = [5,1]
p2 = [7,0]
width: 1
anchors: attach=[6,2]
@end

@elem grave
zone: diacritic-above
path: p1 p2
p1 = [7,1]
p2 = [5,0]
width: 1
anchors: attach=[6,2]
@end

@elem diaeresis
zone: diacritic-above
path: p1 p2 p3 p4
p1 = [4,1]
p2 = [4,1]
p3 = [8,1]
p4 = [8,1]
width: 1
anchors: attach=[6,2]
@end

@elem tilde
zone: diacritic-above
path: p1 p2 p3
p1 = [3,1]
p2 = C([5,0] [7,2])
p3 = [9,1]
width: 1
anchors: attach=[6,2]
@end

@elem cedilla
zone: diacritic-below
path: p1 p2 p3
p1 = [6,8]
p2 = [5,10]
p3 = C([4,10] [6,11])
width: 1
anchors: attach=[6,8]
@end

# ============================================================
# Case Mappings
# ============================================================

@case A a
@case B b
@case D d
@case E e
@case O o
@case Σ σ final:ς

# ============================================================
# Character Definitions
# ============================================================

# Latin lowercase
b  LATIN-SMALL-B        = STACK(ascender, bowl.r) script:Latn
d  LATIN-SMALL-D        = LR(bowl.l, ascender, 7/5) script:Latn
e  LATIN-SMALL-E        = FRAME(arc.top, crossbar, arc.bot) script:Latn

# Diacritic compositions
é  LATIN-SMALL-E-ACUTE  = DIA(e, acute) script:Latn ortho:Fra,Spa,Por
è  LATIN-SMALL-E-GRAVE  = DIA(e, grave) script:Latn ortho:Fra,Ita
ë  LATIN-SMALL-E-DIAERESIS = DIA(e, diaeresis) script:Latn ortho:Nld,Fra
ñ  LATIN-SMALL-N-TILDE  = DIA(n, tilde) script:Latn ortho:Spa
ç  LATIN-SMALL-C-CEDILLA = DIA(c, cedilla) script:Latn ortho:Fra,Tur,Por
ö  LATIN-SMALL-O-DIAERESIS = DIA(o, diaeresis) script:Latn ortho:Deu,Tur

# Overlay compositions
Ø  LATIN-CAPITAL-O-STROKE = OVR(O, stroke.diag) script:Latn ortho:Dan,Nor
ø  LATIN-SMALL-O-STROKE = OVR(o, stroke.diag) script:Latn ortho:Dan,Nor
ł  LATIN-SMALL-L-STROKE = OVR(l, stroke.horiz) script:Latn ortho:Pol

# Multi-diacritic
ắ  LATIN-SMALL-A-BREVE-ACUTE = DIA2(a, breve, acute) script:Latn ortho:Vie

# Cyrillic
П  CYRILLIC-CAPITAL-PE  = FRAME(stem.l, bar.top, stem.r) script:Cyrl

# Greek
β  GREEK-SMALL-BETA     = STACK(ascender.curved, bowl.r.upper, bowl.r.lower) script:Grek

# Ligatures
ﬁ  LATIN-SMALL-LIGATURE-FI = LIG(f, i, merge:hook-tittle) cp:U+FB01 script:Latn
ﬂ  LATIN-SMALL-LIGATURE-FL = LIG(f, l, merge:hook-ascender) cp:U+FB02 script:Latn
Æ  LATIN-CAPITAL-AE = LIG(A, E, merge:stem-shared) cp:U+00C6 script:Latn
Œ  LATIN-CAPITAL-OE = LIG(O, E, merge:bowl-stem) cp:U+0152 script:Latn

# Style transform
@style italic
transform: sk(*, kx=2, ky=0)
@end
```

---

## Appendix E: Script and Orthography Tag Registry

### E.1 Script Tags (ISO 15924)

| Tag    | Script Name | LSDL Usage                         |
|--------|-------------|------------------------------------|
| `Latn` | Latin       | Latin script characters            |
| `Grek` | Greek       | Greek script characters            |
| `Cyrl` | Cyrillic    | Cyrillic script characters         |

### E.2 Extended Script Tags (ISO 15924)

| Tag    | Script Name | Coverage Status                    |
|--------|-------------|------------------------------------|
| `Armn` | Armenian    | May need element extensions        |
| `Geor` | Georgian    | May need element and metric extensions |
| `Copt` | Coptic      | Partial coverage via Greek elements |

### E.3 Orthography Tags (ISO 639)

| Tag   | Language     | Script | Notes                           |
|-------|--------------|--------|---------------------------------|
| `Fra` | French       | Latn   | é, è, ê, ë, ç, à, ù, û, ü, ô  |
| `Deu` | German       | Latn   | ä, ö, ü, ß                     |
| `Spa` | Spanish      | Latn   | ñ, á, é, í, ó, ú, ü            |
| `Por` | Portuguese   | Latn   | ã, õ, á, é, ç, à               |
| `Ita` | Italian      | Latn   | à, è, é, ì, ò, ù               |
| `Pol` | Polish       | Latn   | ą, ć, ę, ł, ń, ó, ś, ź, ż     |
| `Tur` | Turkish      | Latn   | ç, ğ, ı, İ, ö, ş, ü            |
| `Vie` | Vietnamese   | Latn   | Extensive diacritic system       |
| `Ron` | Romanian     | Latn   | ă, â, î, ș, ț                  |
| `Nld` | Dutch        | Latn   | ë, ï, é                        |
| `Dan` | Danish       | Latn   | æ, ø, å                        |
| `Nor` | Norwegian    | Latn   | æ, ø, å                        |
| `Rus` | Russian      | Cyrl   | Full Cyrillic                    |
| `Bul` | Bulgarian    | Cyrl   | Cyrillic with glyph variants    |
| `Srp` | Serbian      | Cyrl   | Cyrillic with italic variants   |
| `Ukr` | Ukrainian    | Cyrl   | ґ, є, і, ї                     |

### E.4 Tag Selection Guide

When annotating a definition, authors SHOULD:

1. Always include `script:` to identify the script.
2. Include `ortho:` only when the character is specific to certain
   languages or when orthographic variants exist.
3. Use comma-separated `ortho:` values when a character is shared
   across multiple orthographies.
4. Omit `ortho:` for characters universal within their script
   (e.g., basic Latin A–Z needs no ortho tag).

---

*End of LSDL Specification*
