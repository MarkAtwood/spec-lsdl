# LSDL: A Construction Grammar for Latin, Greek, and Cyrillic

## Why This Exists

The absence of a constructive grammar for alphabetic characters has irritated me since I was a preschool autistic nerdling who had to consciously think his way through motor control. While other kids just *wrote*, I had to decompose each letter into steps: stem down, curve right, close the loop. I was reverse-engineering handwriting from first principles because my brain didn't come with the "just do it automatically" module.

Decades later, it turns out I wasn't wrong to think letters should have explicit build instructions. Look at most people's handwriting today. The motor-control-by-osmosis approach isn't working that well for anyone. Maybe a systematic description of how letters are actually constructed—the strokes, the attachments, the proportions—should finally exist.

So here it is.

## The Problem: Nobody Describes How Letters Are Built

Latin, Greek, and Cyrillic characters (and their diacritic-laden descendants across European, Slavic, and Southeast Asian orthographies) exist in several digital representations, and every single one of them throws away structural information.

**Unicode** assigns each character a code point. It tells you "this is U+00E9 LATIN SMALL LETTER E WITH ACUTE" but says nothing about the fact that U+00E9 is composed of an e-shape with an acute mark attached above it, or that the e-shape itself is built from arcs and a crossbar. It encodes *identity*, not *structure*.

**Font formats** (OpenType, TrueType) store the actual rendered outlines as cubic or quadratic Bézier curves. But the compilation process that produces those outlines destroys all component-level structure. You cannot look at a font's glyph data and recover "this letter is a stem with a right-side bowl attached." The anatomical structure (stems, bowls, arcs, serifs, diacritics) has been flattened into raw curves.

**Typographic references** (letter anatomy charts, type design textbooks) annotate characters with structural terminology, but these are informational descriptions, not constructive grammars. They're field notes, not blueprints. You can't evaluate them to produce geometry.

**OpenType's GDEF/GPOS/GSUB tables** encode glyph substitution and positioning rules for rendering engines, but these are layout-engine directives, not structural descriptions of how characters are built from parts.

LSDL (Latin Script Description Language) occupies the gap between all of these. It is a constructive, deterministic language that takes anatomical element primitives, reusable named components, anchor-based attachment, and composition operators as input and produces positioned element geometry as output. Given an LSDL expression, you can evaluate it and get an unambiguous geometric description of a character. It is, essentially, a build specification for alphabetic characters.

## Background: How Alphabetic Characters Work (Minimum Viable Version)

A reader who has never studied typography needs exactly four concepts to follow the rest of this document.

**Elements.** Every alphabetic character is drawn from a set of anatomical parts. A vertical stroke is a *stem*. A rounded closed form is a *bowl*. A horizontal stroke is a *crossbar* or *bar*. A curved entry at the top is a *hook*. There are about 45 named element types (verticals, curves, horizontals, diagonals, terminals). That's it. Every character in Latin, Greek, and Cyrillic is drawn from this set.

**Metric Zones.** Unlike CJK characters that fit in uniform square boxes, alphabetic characters align to a vertical metric system. The *baseline* is where characters sit. The *x-height* is the top of lowercase letters like `a`, `c`, `e`. The *ascender line* is the top of tall lowercase letters like `b`, `d`, `h`. The *descender line* is the bottom of letters that dip below baseline like `g`, `p`, `y`. The *cap height* is the top of capital letters. These landmarks divide the vertical space into zones that govern where elements go.

**Anchors.** Elements attach to each other at named points. A stem has a `top` anchor and a `base` anchor. A bowl has a `mark-above` anchor for diacritics and an `attach` anchor for joining. When you compose elements, the composition operators align these anchor points. This is how alphabetic characters structurally connect: parts attach at specific points, not in spatial quadrants.

**Diacritics.** Alphabetic scripts make heavy use of combining marks: acute (é), grave (è), umlaut (ö), cedilla (ç), caron (č), and dozens more. A single base character can carry multiple stacked diacritics (Vietnamese ắ has both breve and acute). LSDL treats diacritics as first-class elements with their own anchors, and provides dedicated operators for attaching them.

## Language Design: What LSDL Is and Isn't

LSDL is a domain-specific language with some unusual properties that are worth stating up front, because they define its character.

**It is constructive.** An LSDL expression can be evaluated to produce geometry. It's not a description or annotation; it's a program (in the loosest sense) that outputs positioned elements.

**It is deterministic.** Same input, same output. Always. No randomness, no implementation-defined behavior in evaluation, no context-sensitivity.

**It is non-Turing.** There are no loops, no variables, no conditionals, no recursion, no macros. A character definition is a finite directed acyclic graph of nodes. Evaluation is a single pass: resolve references, compute bounding boxes, align anchors, place children, emit element geometry. Evaluation always terminates. This is a *hard* design constraint that the spec explicitly forbids future versions from relaxing.

**It is closed.** Every operator set (elements, compositions, transforms) is enumerated and finite. A conformant parser must reject any operator it doesn't recognize. This prevents dialect fragmentation: if a parser accepts a file, every other conformant parser will too.

**It is not a font format.** LSDL output is a tree of positioned elements in a coordinate space. How you render those elements (filled outlines, SVG paths, bitmap, calligraphic simulation) is your problem. LSDL describes structure, not aesthetics.

**It is not a text layout engine.** Line breaking, justification, kerning, advance widths: all out of scope.

## File Format

An LSDL file is UTF-8, line-oriented plain text. The conventional extension is `.lsdl`. Files begin with an optional version declaration:

```
@lsdl 1.0
```

The version declaration follows semantic versioning with a strict contract: minor versions can add metadata fields and registry entries, but adding a new element name or composition operator requires a major version bump (because the closed-set enforcement means a v1 parser would reject the new name).

After the declarations come definitions: element definitions, character definitions, case mappings, aliases, and style declarations. Comments begin with `#`.

## The Coordinate System

LSDL divides every bounding box into a 12×12 grid. The origin `[0,0]` is the top-left corner; `[12,12]` is the bottom-right; `[6,6]` is the center. Twelve was chosen because it's evenly divisible by 2, 3, 4, and 6, so halves, thirds, quarters, and sixths all land on integer coordinates without rounding.

The vertical axis is mapped to typographic landmarks:

```
 0  ─── cap-top        ┐
 1  ─── ascender        │ ascender zone
 2  ─── cap-height     ┘
 3  ───
 4  ─── x-top          ┐
 5  ───                 │ x-height zone
 6  ───                 │ (body)
 7  ───                 │
 8  ─── baseline       ┘
 9  ───                 ┐
10  ─── descender       │ descender zone
11  ───                 │
12  ─── desc-limit     ┘
```

For elements that need finer positioning, a `/24` override doubles the grid resolution to 24×24 within a single element block.

## Elements

Elements are the atomic anatomical parts. The approximately 45 named elements fall into categories:

**Verticals:** `stem` (vertical stroke), `ascender` (stem above x-height), `descender` (stem below baseline), `full-stem` (full vertical extent).

**Curves:** `bowl` (closed round form as in b, d, o), `arc.top`/`arc.bot` (open curves), `hook.top`/`hook.bot` (curved entry/exit), `loop`, `ear`, `shoulder` (arch from stem), `ogee` (S-curve).

**Horizontals and Diagonals:** `crossbar`, `bar.top`/`bar.mid`/`bar.bot`, `arm`, `leg`, `diagonal`, `apex`, `vertex`, `spine`, `tail`, `stroke.diag`, `stroke.horiz`.

**Terminals:** `serif`, `spur`, `ball`, `finial`, `swash`, `flag`, `tittle` (dot above i, j).

Elements support **positional variants** via dotted names. The element `bowl` has variants `bowl.l` (left-side, as in d, q), `bowl.r` (right-side, as in b, p), and `bowl.full` (complete round, as in o). Script-specific variants include `stem.cyr` (Cyrillic stem) and `sigma.final` (Greek final sigma).

## Composition Operators

Seven operators describe how elements combine:

| Operator | Meaning | Example |
|----------|---------|---------|
| `STACK(a, b, …)` | Vertical stacking along stem axis | `STACK(ascender, bowl.r)` = b |
| `LR(a, b)` | Left-right adjacency | `LR(bowl.l, ascender)` = d |
| `LR3(a, b, c)` | Three-way horizontal | Multi-stem characters |
| `DIA(base, mark)` | Diacritic attachment | `DIA(e, acute)` = é |
| `DIA2(base, m1, m2)` | Two diacritics | `DIA2(a, breve, acute)` = ắ |
| `OVR(a, b)` | Overlay / superimposition | `OVR(O, stroke.diag)` = Ø |
| `FRAME(parts…)` | Assembled from anchor points | `FRAME(stem.l, bar.top, stem.r)` = П |

The `DIA` operator is the most frequently used. Approximately half of all Latin Extended characters are base+diacritic compositions.

Layout operators support proportional splits: `LR(bowl.l, ascender, 7/5)` gives 7 grid units to the left part and 5 to the right. Split values are proportional ratios; values summing to 12 align neatly with grid boundaries.

## Transform Operators

Three transform operators modify the geometry of a child expression:

| Operator | Meaning | Example |
|----------|---------|---------|
| `sc(expr, sx=N, sy=N)` | Scale | `sc(bowl, sx=8, sy=8)` = 2/3 size bowl |
| `sh(expr, dx=N, dy=N)` | Shift | `sh(dot, dx=0, dy=-2)` = dot raised 2 units |
| `sk(expr, kx=N, ky=N)` | Skew | `sk(stem, kx=2, ky=0)` = italic lean |

Scale factors are expressed as fractions of 12: `sx=12` means 100%, `sx=6` means 50%. Transforms compose inside-out; implementations must not reorder them.

## Quick Examples

Most characters are one-line definitions:

```
# Basic Latin
A  LATIN-CAPITAL-A      = APEX(stem.l, stem.r, crossbar)
b  LATIN-SMALL-B        = STACK(ascender, bowl.r)
d  LATIN-SMALL-D        = LR(bowl.l, ascender, 7/5)
e  LATIN-SMALL-E        = FRAME(arc.top, crossbar, arc.bot)

# Diacritic compositions
é  LATIN-SMALL-E-ACUTE  = DIA(e, acute)
ç  LATIN-SMALL-C-CEDILLA = DIA(c, cedilla)
ö  LATIN-SMALL-O-DIAERESIS = DIA(o, diaeresis)
ñ  LATIN-SMALL-N-TILDE  = DIA(n, tilde)

# Stacked diacritics (Vietnamese)
ắ  LATIN-SMALL-A-BREVE-ACUTE = DIA2(a, breve, acute)

# Overlays
Ø  LATIN-CAPITAL-O-STROKE = OVR(O, stroke.diag)
ł  LATIN-SMALL-L-STROKE = OVR(l, stroke.horiz)

# Cyrillic
П  CYRILLIC-CAPITAL-PE  = FRAME(stem.l, bar.top, stem.r) script:Cyrl
Д  CYRILLIC-CAPITAL-DE  = FRAME(stem.l.angled, bar.top, stem.r.angled, foot.l, foot.r) script:Cyrl

# Greek
β  GREEK-SMALL-BETA     = STACK(ascender.curved, bowl.r.upper, bowl.r.lower) script:Grek
```

Leaf elements are defined with explicit path geometry:

```
@elem stem
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
width: 1
anchors: top=[6,4] base=[6,8] mid=[6,6]
  mark-above=[6,3] mark-below=[6,9]
@end

@elem acute
zone: diacritic-above
path: p1 p2
p1 = [5,1]
p2 = [7,0]
width: 1
anchors: attach=[6,2]
@end
```

## Case Mapping

Alphabetic scripts have case pairs. LSDL records these explicitly:

```
@case A a
@case B b
@case Σ σ final:ς
@case É é
```

The `final:` tag handles context-dependent forms like Greek final sigma.

## Ligatures

Ligatures are compositions with structural join semantics:

```
ﬁ  LATIN-SMALL-LIGATURE-FI = LIG(f, i, merge:hook-tittle) cp:U+FB01
Æ  LATIN-CAPITAL-AE = LIG(A, E, merge:stem-shared) cp:U+00C6
```

The `merge:` parameter names the structural strategy: `hook-tittle` (f's hook absorbs i's tittle), `stem-shared` (right stem of first = left stem of second).

## Script and Orthography Tags

Definitions can carry metadata:

```
Ø  LATIN-CAPITAL-O-STROKE = OVR(O, stroke.diag) script:Latn ortho:Dan,Nor
Щ  CYRILLIC-CAPITAL-SHCHA = FRAME(…) script:Cyrl ortho:Rus,Bul
```

| Tag | Meaning |
|-----|---------|
| `script:TAG` | ISO 15924 script code (Latn, Grek, Cyrl) |
| `ortho:TAG` | Orthography/language (ISO 639: Fra, Dan, Rus…) |
| `block:NAME` | Unicode block name |
| `cp:U+XXXX` | Explicit Unicode code point |

## Scope and Coverage

LSDL targets approximately 2500 characters across:

- **Latin:** Basic Latin through Latin Extended-E and Latin Extended Additional (~1400 characters)
- **Greek:** Greek and Coptic, Greek Extended (~400 characters)
- **Cyrillic:** Cyrillic through Cyrillic Extended-D (~500 characters)
- **Combining marks:** Combining Diacritical Marks and extensions (~200 marks)

Scripts that share the bicameral alphabetic model (Armenian, Georgian, Coptic) can be described using LSDL with metric overrides and script-specific element variants.

## LSDL vs CSDL

LSDL is a sibling format to CSDL (CJK Stroke Description Language). Both share the same 12×12 coordinate grid, the same transform operators, and the same design philosophy: define primitives once, then compose. The key differences reflect the structural nature of each script family:

| Aspect | CSDL (CJK) | LSDL (Latin/Greek/Cyrillic) |
|--------|------------|----------------------------|
| Grid | 12×12 uniform | 12×12 with metric zones |
| Primitives | 37 stroke types | ~45 anatomical elements |
| Composition | Spatial tiling (LR, TB, SUR) | Attachment-based (STACK, DIA, FRAME) |
| Primary mechanism | Grid partitioning | Anchor points |
| Case | N/A | @case mapping |
| Diacritics | Rare | First-class (DIA operator) |
| Ligatures | N/A | LIG operator |
| Typical char definition | 1 line | 1 line |

## Security

LSDL is a declarative description language with no executable code, no I/O, no network access, and no external process invocation. Evaluation is bounded: the number of elements, tree depth, and coordinate computations in the output are all linear in the input size. There is no mechanism by which an LSDL input can cause superlinear resource consumption. The attack surface is essentially zero.

## What LSDL Makes Possible

LSDL fills a representation gap that has existed for decades. With a constructive grammar for character structure, several things become tractable that weren't before.

Font toolchains could accept LSDL input and generate outlines, preserving structural metadata through the compilation process. Educational software could present letters as build instructions rather than opaque images. Structural search becomes possible: find all characters that contain `bowl` with an attached diacritic. Systematic comparison across scripts and orthographies can be done programmatically. Automated consistency checking can verify that an element used in hundreds of characters is defined identically everywhere. And machine learning systems working on character recognition or generation could use the structural decomposition as training signal rather than treating letters as undifferentiated pixel patterns.

The language is deliberately austere. Approximately 45 element types, 8 composition operators, 3 transforms, a 12×12 grid with metric zones. That's the entire vocabulary. The constraint is the point: by refusing to be a programming language, LSDL guarantees that every file is parseable, every expression terminates, and every implementation agrees on the output.
