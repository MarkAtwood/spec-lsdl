# Anchor Placement Guide

This guide documents anchor placement conventions in LSDL. Anchors are named coordinates on elements where other elements attach, serving as the primary mechanism for composition alignment.

## Standard Anchor Names

Every element definition MUST declare at least one anchor point. The following anchor names are standard and SHOULD be used where applicable.

### Structural Anchors

| Anchor | Meaning | Typical Placement |
|--------|---------|-------------------|
| `top` | Top connection point | Top of element's vertical extent |
| `base` | Bottom/baseline connection | Bottom of element, typically at baseline y=8 |
| `mid` | Vertical midpoint | Center of element's vertical extent |
| `left` | Left edge connection | Leftmost point of element |
| `right` | Right edge connection | Rightmost point of element |

### Diacritic Attachment Anchors

| Anchor | Meaning | Typical Placement |
|--------|---------|-------------------|
| `attach` | General attachment point | Used by diacritics; positioned where mark connects to base |
| `mark-above` | Diacritic attachment above | Above the character body, for acute/grave/circumflex etc. |
| `mark-below` | Diacritic attachment below | Below baseline, for cedilla/ogonek etc. |

### Corner Anchors

| Anchor | Meaning | Typical Placement |
|--------|---------|-------------------|
| `top-left` | Upper-left corner | For elements needing corner attachment |
| `top-right` | Upper-right corner | Used for horn diacritic placement (Vietnamese) |
| `bot-left` | Lower-left corner | Bottom-left attachment point |
| `bot-right` | Lower-right corner | Bottom-right attachment point |

### Specialized Anchors

| Anchor | Meaning | Example Use |
|--------|---------|-------------|
| `arm.left` | Left arm connection | Stem elements with horizontal projections |
| `arm.right` | Right arm connection | Stem elements with horizontal projections |
| `top-serif` | Top serif attachment | Serif-style stem elements |
| `bot-serif` | Bottom serif attachment | Serif-style stem elements |

## Zone-Anchor Relationships

Different metric zones typically require different anchor sets:

### X-Height Zone (y=4 to y=8)

Elements in the x-height zone (lowercase body) typically need:

```
                    mark-above [6,3]
                         |
    +-------------------top [6,4]-------------------+
    |                    |                          |
 left [0,6] --------  mid [6,6]  -------- right [12,6]
    |                    |                          |
    +------------------base [6,8]-------------------+
                         |
                    mark-below [6,9]
```

Example from `stem` element:
```lsdl
anchors: top=[6,4] base=[6,8] mid=[6,6]
  arm.left=[0,6] arm.right=[12,6]
  mark-above=[6,3] mark-below=[6,9]
```

### Ascender Zone (y=1 to y=8)

Elements extending above x-height need the full vertical span:

```
                    mark-above [6,0]
                         |
                     top [6,1]
                         |
                     mid [6,4]
                         |
                    base [6,8]
                         |
                    mark-below [6,9]
```

Example from `ascender` element:
```lsdl
anchors: top=[6,1] base=[6,8] mid=[6,4]
  mark-above=[6,0] mark-below=[6,9]
```

### Cap Zone (y=0 to y=8)

Capital letter elements span the full cap height:

```
                     top [2,0]
                         |
                     mid [2,4]
                         |
                    base [2,8]
```

### Descender Zone (y=4 to y=10)

Elements extending below baseline:

```
                     top [6,4]
                         |
                     mid [6,7]
                         |
                    base [6,10]
```

### Diacritic Zones

**Above (y=0 to y=2):** Diacritics in `diacritic-above` zone MUST have an `attach` anchor that aligns with the base's `mark-above`:

```
      [acute mark]
           |
      attach [6,2]  <-- connects to base's mark-above
```

**Below (y=9 to y=12):** Diacritics in `diacritic-below` zone MUST have an `attach` anchor that aligns with the base's `mark-below`:

```
      attach [6,8]  <-- connects to base's mark-below
           |
      [cedilla]
```

## Composition Anchor Resolution

### DIA Resolution Order

When the DIA operator attaches a diacritic to a base, anchors are resolved in this order:

1. **Explicit override:** If `attach:ANCHOR_NAME` is specified, use that anchor
   ```lsdl
   DIA(o, horn, attach:top-right)   # horn attaches to top-right, not mark-above
   ```

2. **Zone-based default:**
   - `diacritic-above` zone: diacritic's `attach` aligns with base's `mark-above`
   - `diacritic-below` zone: diacritic's `attach` aligns with base's `mark-below`
   - `x-height` zone (through-marks): centered on base bounding box

3. **Fallback:** If base lacks the required `mark-above` or `mark-below`:
   - Center diacritic horizontally above/below base bounding box
   - Place `attach` at the top/bottom edge of base bounding box

### DIA2 Stacking Behavior

DIA2 attaches two diacritics to a base. The stacking order:

**Two above-marks:**
```lsdl
DIA2(a, breve, acute)   # breve closest to base, acute stacked above
```
```
      acute      <-- second mark (topmost)
      breve      <-- first mark (closest to base)
        a        <-- base character
```
- First mark: attaches via standard DIA resolution to `mark-above`
- Second mark: `attach` aligns to first mark's y-minimum, centered horizontally

**Mixed above/below:**
```lsdl
DIA2(o, ogonek, macron)   # ogonek below, macron above
```
```
      macron     <-- above mark
        o        <-- base character
      ogonek     <-- below mark
```
- Each mark attaches independently: below-mark to `mark-below`, above-mark to `mark-above`
- Order in expression determines which is which (first argument closest to base)

**Two below-marks:**
- First mark: standard DIA resolution to `mark-below`
- Second mark: `attach` aligns to first mark's y-maximum, centered horizontally

### STACK Anchor Inheritance

STACK aligns elements vertically using `top` and `base` anchors:

```lsdl
STACK(ascender, bowl.r)   # produces 'b' structure
```
- First element's `base` aligns with second element's `top`
- Composed result inherits first element's `top` and last element's `base`
- `mark-above` typically comes from topmost element
- `mark-below` typically comes from bottommost element

### LR Anchor Inheritance

LR places elements side-by-side, aligned on baseline:

```lsdl
LR(bowl.l, ascender, 7/5)   # produces 'd' structure
```
- All children align on their `base` anchors
- Composed `left` comes from leftmost element
- Composed `right` comes from rightmost element
- Diacritic anchors: renderer may use center of composed bounding box

## Custom Anchors

### When to Define Custom Anchors

Define custom anchors when:

1. **Non-standard attachment points:** Element has attachment positions that don't fit standard names
2. **Script-specific needs:** Georgian, Armenian, or other scripts may need unique anchors
3. **Style variations:** Different attachment points for serif vs. sans-serif variants

### Naming Conventions

Custom anchor names MUST be:
- Lowercase ASCII identifiers
- May contain dots as separators (e.g., `arm.upper.left`)
- Should be descriptive of position/purpose

Examples of valid custom anchors:
```lsdl
anchors: hook.entry=[4,1] hook.exit=[8,4]
anchors: bowl.junction=[6,6]
anchors: diagonal.top=[3,0] diagonal.base=[9,8]
```

### Declaration Syntax

Custom anchors are declared on the `anchors:` line of an `@elem` block, same as standard anchors:

```lsdl
@elem shoulder
zone: x-height
path: p1 p2 p3
p1 = [2,4]
p2 = C([2,6] [6,4])
p3 = [10,8]
width: 1
anchors: attach=[2,4] top=[2,4] base=[10,8]
  stem.join=[2,6] arch.peak=[6,4]
@end
```

## Visual Examples

### Stem with Full Anchor Set

```
                    mark-above
                        |
   y=3          . . . .[6,3]. . . .
                        |
   y=4  +------------ top ------------+
        |               |              |
   y=6  arm.left ---- mid ---- arm.right
        |               |              |
   y=8  +----------- base ------------+
                        |
   y=9          . . . .[6,9]. . . .
                        |
                    mark-below

        x=0    x=6    x=12
```

### Bowl Element (Right-side)

```
   y=4  +.........attach point at top.........+
        |                                      |
        |        +-------+                     |
        |       /         \                    |
   y=6  |      |   attach  |   [6,6]           |
        |       \  [center]/                   |
        |        +-------+                     |
   y=8  +.........attach point at base........+

        mark-above at [8,3]
        mark-below at [8,9]
```

### Diacritic (Acute) Above Base

```
   y=0      /  [7,0]
           /
   y=1    /   [5,1]
          |
   y=2  attach [6,2]
          :
          :  (gap to base character)
          :
   y=3  mark-above [6,3] on base
          |
   y=4  [base character top]
```

### Composed Character: e-acute

```
   y=0            /     <-- acute top
                 /
   y=1          /
                |
   y=2      attach      <-- acute attach point
                :
   y=3      mark-above  <-- e's mark-above anchor
                |
   y=4      +--top--+   <-- arc.top of 'e'
           /         \
   y=6    | crossbar  |
           \         /
   y=8      +--base-+   <-- arc.bot of 'e'
```

## Common Mistakes

### Forgetting mark-above on Base Characters

**Problem:** Base character lacks `mark-above`, causing diacritics to misalign.

```lsdl
# WRONG: no diacritic anchors
@elem stem
zone: x-height
anchors: top=[6,4] base=[6,8] mid=[6,6]
@end

# CORRECT: includes diacritic anchors
@elem stem
zone: x-height
anchors: top=[6,4] base=[6,8] mid=[6,6]
  mark-above=[6,3] mark-below=[6,9]
@end
```

**Symptom:** DIA compositions fall back to bounding-box centering, producing inconsistent results across characters.

### Inconsistent Naming Across Variants

**Problem:** Variant elements use different anchor names for the same conceptual position.

```lsdl
# INCONSISTENT: variants use different names
@elem bowl
anchors: attach=[6,6] mark-above=[6,3]
@end

@elem bowl.l
anchors: center=[6,6] dia-above=[4,3]   # Different names!
@end
```

**Solution:** Use identical anchor names for corresponding positions:

```lsdl
@elem bowl
anchors: attach=[6,6] mark-above=[8,3] mark-below=[8,9]
@end

@elem bowl.l
anchors: attach=[6,6] mark-above=[4,3] mark-below=[4,9]  # Same names, different coords
@end
```

### Anchors Outside Bounding Box

**Problem:** Anchor coordinates placed outside the element's path geometry.

```lsdl
# PROBLEMATIC: mark-above at y=1, but element only spans y=4 to y=8
@elem stem
zone: x-height
path: p1 p2
p1 = [6,4]
p2 = [6,8]
anchors: mark-above=[6,1]   # Outside element's y-span
@end
```

**Guidance:** While not strictly forbidden, anchors far outside the path geometry can cause unexpected composition results. Diacritic anchors should be positioned just outside the element's visual bounds (e.g., `mark-above` at y=3 for an x-height element spanning y=4 to y=8).

### Missing attach Anchor on Diacritics

**Problem:** Diacritic element lacks required `attach` anchor.

```lsdl
# INVALID: diacritic without attach
@elem acute
zone: diacritic-above
path: p1 p2
p1 = [5,1]
p2 = [7,0]
width: 1
anchors: top=[7,0] base=[5,1]   # Missing attach!
@end
```

**Correct:**
```lsdl
@elem acute
zone: diacritic-above
path: p1 p2
p1 = [5,1]
p2 = [7,0]
width: 1
anchors: attach=[6,2]   # Required for DIA composition
@end
```

### Conflicting Anchor Positions in Compositions

**Problem:** Elements used together have incompatible anchor positions.

```lsdl
# bowl.l expects stem on right at x=12
@elem bowl.l
anchors: attach=[6,6] right=[12,6]
@end

# But stem.l is at x=2
@elem stem.l
zone: cap
anchors: top=[2,0] base=[2,8] mid=[2,4]
@end

# Composition may not align as expected
d = LR(bowl.l, stem.l)   # Misaligned if using right/left anchors
```

**Solution:** Ensure elements designed to compose together have compatible anchor coordinates, or use explicit splits in LR to control positioning.

## Reference: Standard Element Anchor Requirements

From Appendix B of the LSDL specification:

| Element Category | Required Anchors |
|-----------------|------------------|
| Verticals (stem, ascender, descender, full-stem) | top, base, mid, mark-above, mark-below |
| Bowls (bowl, bowl.upper, bowl.lower) | attach, mark-above, mark-below or top, base |
| Arcs (arc.top, arc.bot) | left, right, top/base |
| Hooks (hook.top, hook.bot) | attach, base/top |
| Bars (crossbar, bar.top, bar.bot, bar.mid) | left, right, (mid) |
| Terminals (serif, spur, ball, finial, swash, flag, tittle) | attach |
| Diacritics (all) | attach |
