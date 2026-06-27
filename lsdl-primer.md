# LSDL Primer — A Human-Writable Guide

**Version:** 1.0
**Author:** Mark Atwood
**Date:** 2026-02-09
**Status:** Companion Document (Informative)
**Companion to:** Latin Script Description Language (LSDL) Specification v1.0 [LSDL]

---

## Purpose

This document is a compact, tutorial-style guide to reading and
writing LSDL files. It is informative, not normative. All
definitions, constraints, and conformance requirements live in
[LSDL]. When this primer and [LSDL] disagree, [LSDL] wins.

LSDL describes the structural anatomy of characters in Latin,
Greek, Cyrillic, and related bicameral alphabetic scripts. It is
a sibling format to CSDL (which handles CJK). Both share the
same 12×12 coordinate grid and a similar philosophy: define
primitives once, then compose.

**Core principle:** Most alphabetic characters are compositions
of a small set of structural elements (stems, bowls, arcs,
crossbars, serifs, tails) plus diacritics. LSDL encodes
*anatomy*, not pixels. You define ~40 base shapes, then describe
hundreds of characters as one-line compositions referencing those
shapes and their attachment geometry.

**Key difference from CSDL:** CJK characters tile spatially
(left-right, top-bottom). Alphabetic characters compose along a
*vertical metric system* (baseline, x-height, ascender,
descender) with elements that attach at named *anchor points*
rather than occupying grid quadrants.

All section references (§) refer to [LSDL] unless otherwise noted.

---

## 0. Script Coverage

LSDL targets all characters encodable in the following Unicode
blocks (non-exhaustive list; see [LSDL] Appendix A for the
complete registry):

| Script | Blocks | Approx. Glyphs |
|--------|--------|-----------------|
| Latin  | Basic Latin, Latin-1 Supplement, Latin Extended-A/B/C/D/E, Latin Extended Additional | ~1400 |
| Greek  | Greek and Coptic, Greek Extended | ~400 |
| Cyrillic | Cyrillic, Cyrillic Supplement, Cyrillic Extended-A/B/C/D | ~500 |
| Common | Combining Diacritical Marks, Combining Diacritical Marks Extended | ~200 |

Any character decomposable into the element vocabulary (§3) and
diacritic vocabulary (§6) is in scope. Characters from Armenian,
Georgian, and other scripts that share structural primitives
with the above may be described using LSDL with appropriate
`script:` metadata, but are not required for conformance.

---

## 1. Character Line Format

The inline form (§11) is the primary vehicle:

```
CHAR NAME = COMPOSE(elements) [metadata]
```

Examples (real characters, one line each):

```
A  LATIN-CAPITAL-A      = APEX(stem.l, stem.r, crossbar)
b  LATIN-SMALL-B        = STACK(ascender, bowl.r)
é  LATIN-SMALL-E-ACUTE  = DIA(e, acute)
Ø  LATIN-CAPITAL-O-STROKE = OVR(O, stroke.diag)
ñ  LATIN-SMALL-N-TILDE  = DIA(n, tilde)
Д  CYRILLIC-CAPITAL-DE  = FRAME(stem.l, crossbar.top, stem.r, foot.wide)
β  GREEK-SMALL-BETA     = STACK(ascender.curved, bowl.r.upper, bowl.r.lower)
Ä  LATIN-CAPITAL-A-DIAERESIS = DIA(A, diaeresis)
ő  LATIN-SMALL-O-DOUBLE-ACUTE = DIA(o, double-acute)
Щ  CYRILLIC-CAPITAL-SHCHA = LR3(stem, stem, stem.descender, crossbar.top, crossbar.bot)
```

If the elements are already defined, most characters are one
line. The NAME is the Unicode character name (hyphens replace
spaces; §11.1). The CHAR is the literal Unicode codepoint.

---

## 2. The Metric System (Vertical Zones)

Unlike CJK's uniform bounding box, alphabetic scripts use a
vertical metric with named zones (§4). The 12-unit vertical
axis maps to these landmarks:

```
 0  ─── cap-top        ┐
 1  ─── ascender-top    │ ascender zone
 2  ─── cap-height     ┘
 3  ───
 4  ─── x-top          ┐
 5  ───                 │ x-height zone
 6  ───                 │ (body)
 7  ───                 │
 8  ─── baseline       ┘
 9  ───                 ┐
10  ─── descender-bot   │ descender zone
11  ───                 │
12  ─── desc-limit     ┘
```

Horizontal axis: 0–12, left to right (same as CSDL).

Default zone assignments (overridable per-file via `@metrics`):

| Zone | y-start | y-end | Used by |
|------|---------|-------|---------|
| diacritic-above | 0 | 2 | Diacritics above capitals |
| ascender | 1 | 4 | b, d, f, h, k, l, β |
| cap | 0 | 8 | A, B, C … Z, Α, Β … Ω, А, Б … Я |
| x-height | 4 | 8 | a, c, e, m, n, o … lowercase body |
| baseline | 8 | 8 | (reference line) |
| descender | 8 | 11 | g, p, q, y, β, ξ, ψ |
| diacritic-below | 9 | 12 | cedilla, ogonek, underdot |

```
@metrics
cap-top: 0
ascender: 1
cap-height: 2
x-top: 4
baseline: 8
descender: 10
desc-limit: 12
@end
```

These are defaults. Scripts with unusual vertical proportions
(e.g., Georgian) override via `@metrics` at file scope.

---

## 3. Element Vocabulary (Structural Primitives)

Elements are the atomic anatomical parts of alphabetic glyphs
(§6). Every character is built from these ~45 named elements.

### 3.1 Verticals

| Element | Description | Typical y-span |
|---------|-------------|----------------|
| `stem`  | Vertical straight stroke | x-height or cap |
| `ascender` | Stem extending above x-height | ascender → baseline |
| `descender` | Stem extending below baseline | x-top → descender |
| `full-stem` | Full-height stem | ascender → descender |

### 3.2 Curves

| Element | Description | Notes |
|---------|-------------|-------|
| `bowl`  | Closed round form | as in b, d, p, q, o, О |
| `bowl.upper` | Upper half-bowl | as in B (top), β (top) |
| `bowl.lower` | Lower half-bowl | as in B (bottom), β (bottom) |
| `counter` | Interior of a bowl | (implicit; not drawn) |
| `arc.top` | Open curve, top half | as in c, s (top), С |
| `arc.bot` | Open curve, bottom half | as in s (bottom), ε (bottom) |
| `hook.top` | Curved entry at top | as in f, Γ |
| `hook.bot` | Curved exit at bottom | as in j, J |
| `loop` | Closed curve below baseline | as in g (double-storey) |
| `ear` | Small projection | as in g (single-storey), r |
| `shoulder` | Arch from stem | as in h, m, n |
| `ogee` | S-curve | as in integral, ξ |

### 3.3 Horizontals and Diagonals

| Element | Description | Notes |
|---------|-------------|-------|
| `crossbar` | Horizontal stroke | as in A, H, e, f, Н |
| `bar.top` | Bar at top of glyph | as in T, Г, Т |
| `bar.bot` | Bar at bottom of glyph | as in L, Ц |
| `bar.mid` | Bar at x-height | as in e (crossbar), G |
| `arm` | Horizontal projecting from stem | as in E, F, K, Е, Ж |
| `leg` | Diagonal descending from junction | as in K, R, k |
| `diagonal` | Full-height diagonal | as in N, Z, И |
| `apex` | Meeting point of two diagonals | as in A, Λ, Л |
| `vertex` | Bottom meeting of diagonals | as in V, W |
| `spine` | Central S-curve | as in S, s, З |
| `tail` | Terminal flourish | as in Q, Щ |
| `stroke.diag` | Overlay diagonal slash | as in Ø, ø |
| `stroke.horiz` | Overlay horizontal bar | as in ł, Ħ, đ |

### 3.4 Terminals

| Element | Description | Notes |
|---------|-------------|-------|
| `serif` | Perpendicular terminal | (style-dependent) |
| `spur` | Small serif-like projection | as in b, G |
| `ball` | Circular terminal | as in a, c, f, r (some styles) |
| `finial` | Tapered terminal | as in e, c |
| `swash` | Extended decorative terminal | (style-dependent) |
| `flag` | Small horizontal at top of stem | as in 1, ь |
| `tittle` | Dot above | as in i, j |

### 3.5 Special

| Element | Description | Notes |
|---------|-------------|-------|
| `dot` | Period/point | standalone dot |
| `caron.alt` | Vertical stroke (háček variant) | as in ď, ť, Ľ |
| `comma.shape` | Comma-shaped mark | as in Cyrillic palatal marks |

---

## 4. Composition Operators

Seven operators describe how elements combine (§8). These
are structurally different from CSDL's spatial tiling operators
because alphabetic characters compose by *attachment* rather
than *partition*.

| Op | Meaning | Example |
|----|---------|---------|
| `STACK(a, b, …)` | Vertical stacking along stem | `STACK(ascender, bowl.r)` = b |
| `LR(a, b)` | Left-right adjacency | `LR(bowl.l, stem)` = d |
| `LR3(a, b, c, …)` | Multi-element horizontal | `LR3(stem, bowl, stem)` = Ж |
| `DIA(base, mark)` | Diacritic attachment | `DIA(e, acute)` = é |
| `DIA2(base, m1, m2)` | Two diacritics | `DIA2(o, dot-above, macron)` = ȱ |
| `OVR(a, b)` | Overlay / superimposition | `OVR(O, stroke.diag)` = Ø |
| `FRAME(parts…)` | Assembled from named attachment points | `FRAME(stem.l, bar.top, stem.r)` = П |

### STACK details

Vertical stacking places elements along a shared vertical axis,
top to bottom. The y-zones are inferred from element types
unless overridden.

```
# b = ascender stem with right-side bowl at x-height
b  LATIN-SMALL-B  = STACK(ascender, bowl.r)

# β = ascender curve into upper bowl into lower bowl
β  GREEK-SMALL-BETA  = STACK(ascender.curved, bowl.r.upper, bowl.r.lower)
```

### LR details

Like CSDL's LR, with proportional splits. Default is 6/6.

```
# d = left bowl + ascender stem
d  LATIN-SMALL-D  = LR(bowl.l, ascender, 7/5)

# m = stem + shoulder + stem + shoulder + stem
m  LATIN-SMALL-M  = LR(stem, shoulder, stem, shoulder, stem, 2/3/2/3/2)
```

### DIA details

The most-used operator. Attaches a diacritic mark to a base
character at a named anchor point (§5).

```
é  = DIA(e, acute)          # acute above
ç  = DIA(c, cedilla)        # cedilla below
ö  = DIA(o, diaeresis)      # two dots above
ắ  = DIA2(a, breve, acute)  # stacked: breve then acute above
ạ  = DIA(a, dot-below)      # dot below
```

Multiple diacritics stack outward from the base: first mark
closest to the glyph, subsequent marks further away.

### FRAME details

For characters assembled from parts at specific positions, using
named attachment points rather than simple stacking.

```
# П = two stems connected by a top bar
П  CYRILLIC-CAPITAL-PE  = FRAME(stem.l, bar.top, stem.r)

# Ж = center stem with symmetric diagonals
Ж  CYRILLIC-CAPITAL-ZHE = FRAME(leg.ul, leg.ur, stem, leg.ll, leg.lr)

# Щ = three stems, two crossbars, descending tail
Щ  CYRILLIC-CAPITAL-SHCHA = FRAME(stem, stem, stem.tail, bar.top, bar.bot)
```

---

## 5. Anchor Points

Anchors (§5) define where elements attach to each other.
Every element exposes named anchors; the composition operators
use these to align parts. This is the key mechanical difference
from CSDL (which uses grid partitioning).

Default anchors on a stem:

```
         top-serif
            │
  top ──────┤
            │
            │
  mid ──────┤──── arm.right
            │
            │
  base ─────┤
            │
         bot-serif
```

Default anchors on a bowl:

```
     mark-above
         │
  ┌──────┤──────┐
  │      │      │
  attach ┤  counter │
  │      │      │
  └──────┤──────┘
         │
     mark-below
```

Anchor resolution rules (§5.3):

1. `DIA` attaches mark's `attach` anchor to base's `mark-above`
   or `mark-below` (direction inferred from mark type).
2. `STACK` aligns elements vertically using `top`/`base` anchors.
3. `LR` aligns elements on the baseline using `base` anchors.
4. `FRAME` uses explicitly named anchors.

Override with explicit anchor syntax:

```
# Attach acute to bowl's top-right instead of center-top
DIA(o, acute, attach:top-right)
```

---

## 6. Diacritic Marks (Combining Marks)

LSDL has a first-class diacritic vocabulary (§6.3). Diacritics
are elements that compose via `DIA()` onto base characters.

### 6.1 Above marks

| Mark | Name | Examples |
|------|------|----------|
| `acute` | ´ | é, á, ś, ź, ό, ú |
| `grave` | ` | è, à, ù, ò |
| `circumflex` | ˆ | ê, â, û, ĉ, ŵ |
| `tilde` | ˜ | ñ, ã, õ, ĩ |
| `diaeresis` | ¨ | ö, ü, ä, ë, ï, ÿ |
| `macron` | ¯ | ā, ē, ī, ō, ū |
| `breve` | ˘ | ă, ĕ, ğ, ŭ |
| `caron` | ˇ | č, š, ž, ř, ň, ě |
| `ring` | ˚ | å, ů |
| `dot-above` | ˙ | ż, ė, ġ, ċ, İ |
| `double-acute` | ˝ | ő, ű |
| `horn` | ˛ (above variant) | ơ, ư |
| `comma-above` | ʻ | (transliteration marks) |

### 6.2 Below marks

| Mark | Name | Examples |
|------|------|----------|
| `cedilla` | ¸ | ç, ş, ţ, ķ, ļ |
| `ogonek` | ˛ | ą, ę, į, ų |
| `dot-below` | ̣ | ạ, ẹ, ọ, ụ, ḥ |
| `comma-below` | , | ș, ț (Romanian preferred) |
| `macron-below` | ̱ | ḇ, ḏ, ḵ, ḻ |
| `line-below` | ̲ | (underline diacritics) |
| `breve-below` | ̮ | ḫ |
| `ring-below` | ̥ | ḁ |

### 6.3 Through marks

| Mark | Name | Examples |
|------|------|----------|
| `stroke` | (horizontal) | đ, ħ, ł, ŧ, ɨ |
| `stroke.diag` | (diagonal) | ø, Ø |
| `oblique-stroke` | (angled) | ƚ |

### 6.4 Compound diacritics

Some characters carry multiple diacritics. Use `DIA2` or nested
`DIA` for stacking:

```
# Vietnamese: ắ = a + breve + acute
ắ  = DIA2(a, breve, acute)

# Latvian: ǭ = o + ogonek + macron (below + above)
ǭ  = DIA2(o, ogonek, macron)

# Polish: ź = z + acute + dot-above (but dot suppressed by convention)
# Use canonical form:
ź  = DIA(z, acute)
```

---

## 7. Defining Leaf Elements (Paths)

Only needed for primitives that cannot be decomposed further.
Analogous to CSDL's `@comp` stroke blocks. See §7 and §10.

```
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

@elem bowl.r
zone: x-height
path: p1 p2 p3 p4 p5
p1 = [6,4]
p2 = C([10,4] [12,6])   # cubic control point
p3 = C([12,6] [10,8])
p4 = [6,8]
close: true
width: 1
anchors: attach=[6,6] mark-above=[8,3] mark-below=[8,9]
  top=[8,4] base=[8,8]
@end
```

Path syntax: `[x,y]` for line-to, `C([cx,cy] [x,y])` for
quadratic curve-to, `C([c1x,c1y] [c2x,c2y] [x,y])` for cubic
curve-to. Coordinates on the 12×12 grid (§4). `close: true`
closes the path back to p1.

Width: `0`=hairline, `1`=normal, `2`=bold (same as CSDL).

---

## 8. Element Variants (Dot Notation)

Like CSDL's positional variants, elements use dot notation for
contextual forms (§10.5):

```
bowl      # default (right-side, as in b, p)
bowl.l    # left-side (as in d, q)
bowl.full # full round (as in o, O)
stem.l    # left stem in a frame
stem.r    # right stem in a frame
arc.top   # upper arc (as in c top, s top)
arc.bot   # lower arc (as in s bottom)
hook.top  # top hook (as in f)
hook.bot  # bottom hook (as in j)
```

Script-specific variants:

```
stem.cyr       # Cyrillic stem (may differ in serif style)
bowl.greek     # Greek bowl proportion
sigma.final    # ς vs σ
```

---

## 9. Case Mapping

Alphabetic scripts have case pairs. LSDL records these
explicitly (§13.3):

```
@case A a
@case B b
@case Σ σ final:ς
@case Б б
```

The `final:` tag handles context-dependent forms (Greek final
sigma, etc.).

Characters defined with `DIA()` inherit case mapping from their
base:

```
# é inherits case from e → É from E
# No separate @case line needed
```

---

## 10. Script and Orthography Tags

Every character line may carry metadata (§11.3, §13):

```
Ø  LATIN-CAPITAL-O-STROKE = OVR(O, stroke.diag) script:Latn ortho:Dan,Nor
Щ  CYRILLIC-CAPITAL-SHCHA = FRAME(…) script:Cyrl ortho:Rus,Bul
ξ  GREEK-SMALL-XI = STACK(arc.top, arc.mid, arc.bot) script:Grek
```

| Tag | Meaning |
|-----|---------|
| `script:TAG` | ISO 15924 script code (Latn, Grek, Cyrl) |
| `ortho:TAG` | Orthography/language (ISO 639; Dan, Nor, Rus…) |
| `block:NAME` | Unicode block name |
| `cp:U+XXXX` | Codepoint (explicit, when CHAR is ambiguous) |
| `freq:N` | Frequency rank within script |
| `x-KEY:VAL` | Extension metadata |

---

## 11. Aliases

ASCII names for elements and characters (§10.7):

```
@alias stem-with-right-bowl = b.shape
@alias o-shape = bowl.full
@alias yu = Ю
@alias sigma-final = ς
```

After aliasing, both names are interchangeable everywhere.

Script-qualified aliases prevent collisions between scripts that
share visual forms:

```
@alias Latn:H = H    # Latin H
@alias Grek:H = Η    # Greek Eta (looks identical, different codepoint)
@alias Cyrl:H = Н    # Cyrillic En (looks identical, different codepoint)
```

---

## 12. Transforms (Same as CSDL)

Three transforms, same semantics as CSDL (§9). Values are /12
fractions.

| Op | Meaning | Example |
|----|---------|---------|
| `sc(x, sx=N, sy=N)` | Scale | `sc(bowl, sx=8, sy=8)` = small bowl |
| `sh(x, dx=N, dy=N)` | Shift | `sh(dot, dx=0, dy=-2)` = dot raised |
| `sk(x, kx=N, ky=N)` | Skew | `sk(stem, kx=2, ky=0)` = italic lean |

Italic/oblique forms are expressible as skew transforms on the
upright definition:

```
@style italic
transform: sk(*, kx=2, ky=0)
@end
```

---

## 13. Ligatures

Some orthographies require ligatures. LSDL encodes them as
compositions with special metadata (§14):

```
ﬁ  LATIN-SMALL-LIGATURE-FI = LIG(f, i, merge:hook-tittle) cp:U+FB01
ﬂ  LATIN-SMALL-LIGATURE-FL = LIG(f, l, merge:hook-ascender) cp:U+FB02
Æ  LATIN-CAPITAL-AE = LIG(A, E, merge:stem-shared) cp:U+00C6
Œ  LATIN-CAPITAL-OE = LIG(O, E, merge:bowl-stem) cp:U+0152
```

The `merge:` parameter names the structural join strategy:

| Merge | Meaning |
|-------|---------|
| `hook-tittle` | f's hook absorbs i's tittle |
| `hook-ascender` | f's hook merges with l's ascender |
| `stem-shared` | Right stem of first = left stem of second |
| `bowl-stem` | Bowl's right connects to stem's left |

---

## 14. Complete Minimal File

```
@lsdl 1.0

# Metrics (defaults; shown for clarity)
@metrics
cap-top: 0
ascender: 1
x-top: 4
baseline: 8
descender: 10
desc-limit: 12
@end

# Aliases
@alias acute = acute
@alias cedilla = cedilla

# Leaf elements
@elem stem
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
width: 1
anchors: top=[6,4] base=[6,8] mid=[6,6]
  mark-above=[6,3] mark-below=[6,9]
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

@elem ascender
zone: ascender
path: p1 p2
p1 = [6,1]
p2 = [6,8]
width: 1
anchors: top=[6,1] base=[6,8] mid=[6,4]
  mark-above=[6,0] mark-below=[6,9]
@end

@elem crossbar
zone: x-height
path: p1 p2
p1 = [2,6]
p2 = [10,6]
width: 1
anchors: left=[2,6] right=[10,6] mid=[6,6]
@end

# Diacritics (as elements)
@elem acute
zone: diacritic-above
path: p1 p2
p1 = [5,1]
p2 = [7,0]
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

# Case mappings
@case A a
@case B b
@case D d
@case E e

# Characters
b  LATIN-SMALL-B      = STACK(ascender, bowl.r) script:Latn
d  LATIN-SMALL-D      = LR(bowl.l, ascender, 7/5) script:Latn
e  LATIN-SMALL-E      = FRAME(arc.top, crossbar, arc.bot) script:Latn
é  LATIN-SMALL-E-ACUTE = DIA(e, acute) script:Latn ortho:Fra,Spa,Por
ç  LATIN-SMALL-C-CEDILLA = DIA(c, cedilla) script:Latn ortho:Fra,Tur,Por

# Cyrillic
П  CYRILLIC-CAPITAL-PE = FRAME(stem.l, bar.top, stem.r) script:Cyrl
Д  CYRILLIC-CAPITAL-DE = FRAME(stem.l.angled, bar.top, stem.r.angled, foot.l, foot.r) script:Cyrl

# Greek
β  GREEK-SMALL-BETA   = STACK(ascender.curved, bowl.r.upper, bowl.r.lower) script:Grek
```

---

## 15. Reading LSDL: A Cheat Sheet

Ask these questions in order:

1. **What character?** The literal glyph and Unicode name on the left of `=`.
2. **How is it composed?** The operator: STACK, LR, DIA, OVR, FRAME, LIG.
3. **What are the elements?** The arguments inside the parentheses.
4. **Any diacritics?** If DIA/DIA2, what mark and where.
5. **Proportions?** If split given, read it. Otherwise default.
6. **What script?** The `script:` tag.
7. **Any metadata?** Trailing `ortho:` `freq:` `cp:` tags.

If an element is not defined in the current file, either it is
a known primitive defined in the standard library (see [LSDL]
Appendix B), or it needs an `@elem` block.

The typical workflow: define the ~45 structural elements once
(see [LSDL] Appendix B), define the ~30 diacritics once (see
[LSDL] Appendix C), then describe hundreds of characters as
one-line compositions.

---

## 16. Comparison: LSDL vs CSDL

| Aspect | CSDL (CJK) | LSDL (Latin/Greek/Cyrillic) |
|--------|------------|----------------------------|
| Grid | 12×12 uniform | 12×12 with metric zones |
| Primitives | 37 stroke types | ~45 anatomical elements |
| Composition | Spatial tiling (LR, TB, SUR) | Attachment-based (STACK, DIA, FRAME) |
| Primary mechanism | Grid partitioning | Anchor points |
| Variants | Positional (.left, .top) | Contextual (.l, .r, .cyr, .greek) |
| Case | N/A | @case mapping |
| Diacritics | Rare | First-class (DIA operator) |
| Ligatures | N/A | LIG operator |
| Stroke order | Defined (build:) | N/A (not culturally relevant) |
| Typical leaf count | ~214 radicals | ~45 elements + ~30 diacritics |
| Typical char definition | 1 line | 1 line |

---

## 17. Quick Reference Card

```
COMPOSE:  STACK LR LR3 DIA DIA2 OVR FRAME LIG
SPLIT:    proportional ratio (values summing to 12 preferred)
ZONES:    cap-top ascender x-top baseline descender desc-limit
ANCHORS:  top base mid mark-above mark-below attach
          arm.left arm.right top-serif bot-serif
PATH:     [x,y]  C([cx,cy] [x,y])  C([c1x,c1y] [c2x,c2y] [x,y])
GRID:     12×12, origin top-left
VARIANT:  name.tag  (bowl.l, stem.cyr, sigma.final)
XFORM:    sc(_, sx=, sy=)  sh(_, dx=, dy=)  sk(_, kx=, ky=)
META:     script: ortho: block: cp: freq: x-*:
CASE:     @case UPPER lower [final:FORM]
ALIAS:    @alias name = target  |  @alias Script:name = target
WIDTH:    0=hairline  1=normal  2=bold
FILE:     @lsdl 1.0
```

---

## Appendix A: Coverage Checklist

A conforming LSDL implementation MUST be able to describe all
characters in the following Unicode blocks. [LSDL] Appendix A
contains the full codepoint-by-codepoint registry.

### Latin

- U+0000–007F Basic Latin (printable subset)
- U+0080–00FF Latin-1 Supplement
- U+0100–017F Latin Extended-A
- U+0180–024F Latin Extended-B
- U+0250–02AF IPA Extensions
- U+1E00–1EFF Latin Extended Additional
- U+2C60–2C7F Latin Extended-C
- U+A720–A7FF Latin Extended-D
- U+AB30–AB6F Latin Extended-E

### Greek

- U+0370–03FF Greek and Coptic
- U+1F00–1FFF Greek Extended

### Cyrillic

- U+0400–04FF Cyrillic
- U+0500–052F Cyrillic Supplement
- U+2DE0–2DFF Cyrillic Extended-A
- U+A640–A69F Cyrillic Extended-B
- U+1C80–1C8F Cyrillic Extended-C
- U+1E030–1E08F Cyrillic Extended-D

### Combining Marks

- U+0300–036F Combining Diacritical Marks
- U+1AB0–1AFF Combining Diacritical Marks Extended
- U+1DC0–1DFF Combining Diacritical Marks Supplement
- U+20D0–20FF Combining Diacritical Marks for Symbols

---

## 18. Tooling

LSDL includes command-line tools for validation, inspection, and rendering.

### lsdl-validate

Validates LSDL files for syntax and semantic correctness.

```bash
lsdl-validate myfile.lsdl
lsdl-validate lib/*.lsdl --strict
```

Checks performed:
- Syntax correctness (blocks, operators, coordinates)
- Element references resolve (no undefined elements)
- Anchor point validity
- Metric zone consistency
- Duplicate definition detection

### lsdl-dump

Inspects LSDL file structure and contents.

```bash
lsdl-dump myfile.lsdl              # Full structure dump
lsdl-dump myfile.lsdl --stats      # Summary statistics
lsdl-dump myfile.lsdl --elements   # List defined elements
lsdl-dump myfile.lsdl --chars      # List character definitions
```

### lsdl-render

Renders LSDL definitions to SVG (coming soon).

```bash
lsdl-render myfile.lsdl -o output.svg
lsdl-render myfile.lsdl --char=é --size=100
```

### Python Module

The tools are also available as a Python module:

```bash
python3 -m lsdl.cli.validate file.lsdl
python3 -m lsdl.cli.dump file.lsdl --stats
```

---

## 19. Standard Libraries

LSDL ships with pre-defined element and character libraries. Import these
to avoid re-defining common primitives.

| Library | Contents | Count |
|---------|----------|-------|
| `lib/elements-base.lsdl` | Base structural elements (stems, bowls, arcs, etc.) | 39 elements |
| `lib/diacritics.lsdl` | Combining diacritical marks | 24 diacritics |
| `lib/basic-latin.lsdl` | A-Z uppercase, a-z lowercase | 52 characters |
| `lib/latin-extended.lsdl` | Accented Latin characters | ~300 characters |
| `lib/greek.lsdl` | Greek alphabet (upper and lower) | ~100 characters |
| `lib/cyrillic.lsdl` | Cyrillic alphabet | ~150 characters |
| `lib/ligatures.lsdl` | Standard ligatures (fi, fl, ff, etc.) | ~20 ligatures |

### Usage

```
@lsdl 1.0
@import lib/elements-base.lsdl
@import lib/diacritics.lsdl

# Now all base elements and diacritics are available
ñ  LATIN-SMALL-N-TILDE = DIA(n, tilde) script:Latn ortho:Spa
```

---

## 20. Quick Start

### Validate an LSDL file

```bash
lsdl-validate myfile.lsdl
```

### Inspect file structure

```bash
lsdl-dump myfile.lsdl --stats
```

### Check with Python module

```bash
python3 -m lsdl.cli.validate file.lsdl
```

### Create a minimal LSDL file

1. Start with `@lsdl 1.0`
2. Import the standard libraries (or define your own elements)
3. Define characters as one-line compositions
4. Validate with `lsdl-validate`

Example workflow:

```bash
# Create a new file
cat > test.lsdl << 'EOF'
@lsdl 1.0
@import lib/elements-base.lsdl
@import lib/diacritics.lsdl

ë  LATIN-SMALL-E-DIAERESIS = DIA(e, diaeresis) script:Latn
EOF

# Validate
lsdl-validate test.lsdl

# Inspect
lsdl-dump test.lsdl --stats
```

---

## References

**[LSDL]**
Latin Script Description Language (LSDL) Specification, Version 1.0 Draft, 2026-02-09.

**[CSDL]**
CJK Stroke Description Language (CSDL) Specification, Version 1.0 Draft, 2026-02-09.

**[Unicode]**
The Unicode Standard, Version 16.0.

**[ISO 15924]**
ISO 15924:2004, Codes for the representation of names of scripts.

**[OpenType]**
OpenType Specification, Version 1.9. (Informative reference for
anchor point and metric zone conventions.)
