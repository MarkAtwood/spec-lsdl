# LSDL Element Geometry Reference

This document provides detailed geometry specifications for all 39 base elements
in the LSDL Standard Element Library. For each element, it documents canonical
coordinates, anchor positions, width variants, and common variants with ASCII
diagrams.

**Note:** This is informative documentation that supplements the normative
specification. The spec defines WHAT elements are; this document shows HOW to
draw them.

## Coordinate System Reference

LSDL uses a 12x12 grid:
- Origin `[0,0]` is at the **top-left** corner
- X axis increases to the right (0-12)
- Y axis increases **downward** (0-12)
- Center is at `[6,6]`

### Vertical Metric Zones

| Landmark       | y-value | Description                              |
|----------------|---------|------------------------------------------|
| `cap-top`      | 0       | Top of capital letters and diacritics    |
| `ascender`     | 1       | Top of ascender strokes                  |
| `cap-height`   | 2       | Top of capital letter body               |
| `x-top`        | 4       | Top of lowercase body (x-height line)    |
| `baseline`     | 8       | Reference line on which characters sit   |
| `descender`    | 10      | Bottom of descender strokes              |
| `desc-limit`   | 12      | Absolute bottom (descender clearance)    |

### Width Values

- `0` = hairline
- `1` = normal weight
- `2` = bold weight

---

## 1. Verticals (4 elements)

### stem - Vertical straight stroke

**Zone:** x-height (y=4 to y=8)  
**Description:** Basic vertical stroke for lowercase letters  
**Examples:** i, l (body), n, m, h

**Required Anchors:** top, base, mid, mark-above, mark-below

**Canonical Path (width 1):**
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
```

**ASCII Diagram:**
```
    0 1 2 3 4 5 6 7 8 9 10 11 12
  3 . . . . . . ^ . . . . . . .   <- mark-above
  4 . . . . . . * . . . . . . .   <- top
  5 . . . . . . | . . . . . . .
  6 *-----------*-----------*     <- mid, arm.left, arm.right
  7 . . . . . . | . . . . . . .
  8 . . . . . . * . . . . . . .   <- base (baseline)
  9 . . . . . . v . . . . . . .   <- mark-below
```

**Width Variants:**
- `width: 0` - hairline stem (x=6 only, single-pixel width)
- `width: 1` - normal stem (default, shown above)
- `width: 2` - bold stem (thicker stroke, same path)

**Common Variants:**
- `stem.l` - stem positioned left (x=2-4)
- `stem.r` - stem positioned right (x=8-10)

---

### ascender - Stem extending above x-height

**Zone:** ascender (y=1 to y=8)  
**Description:** Vertical stroke from ascender line to baseline  
**Examples:** b, d, h, k, l

**Required Anchors:** top, base, mid, mark-above, mark-below

**Canonical Path (width 1):**
```
@elem ascender
zone: ascender
path: p1 p2
p1 = [6,1]
p2 = [6,8]
width: 1
anchors: top=[6,1] base=[6,8] mid=[6,4]
         mark-above=[6,0] mark-below=[6,9]
@end
```

**ASCII Diagram:**
```
    0 1 2 3 4 5 6 7 8 9 10 11 12
  0 . . . . . . ^ . . . . . . .   <- mark-above (cap-top)
  1 . . . . . . * . . . . . . .   <- top (ascender line)
  2 . . . . . . | . . . . . . .   <- cap-height
  3 . . . . . . | . . . . . . .
  4 . . . . . . * . . . . . . .   <- mid (x-top)
  5 . . . . . . | . . . . . . .
  6 . . . . . . | . . . . . . .
  7 . . . . . . | . . . . . . .
  8 . . . . . . * . . . . . . .   <- base (baseline)
  9 . . . . . . v . . . . . . .   <- mark-below
```

**Width Variants:**
- `width: 0` - hairline
- `width: 1` - normal (default)
- `width: 2` - bold

**Common Variants:**
- `ascender.l` - left-positioned (for b)
- `ascender.r` - right-positioned (for d)

---

### descender - Stem extending below baseline

**Zone:** descender (y=4 to y=10)  
**Description:** Vertical stroke from x-top to descender line  
**Examples:** p, q, y (straight variant)

**Required Anchors:** top, base, mid

**Canonical Path (width 1):**
```
@elem descender
zone: descender
path: p1 p2
p1 = [6,4]
p2 = [6,10]
width: 1
anchors: top=[6,4] base=[6,10] mid=[6,7]
@end
```

**ASCII Diagram:**
```
    0 1 2 3 4 5 6 7 8 9 10 11 12
  4 . . . . . . * . . . . . . .   <- top (x-top)
  5 . . . . . . | . . . . . . .
  6 . . . . . . | . . . . . . .
  7 . . . . . . * . . . . . . .   <- mid
  8 . . . . . . | . . . . . . .   <- baseline
  9 . . . . . . | . . . . . . .
 10 . . . . . . * . . . . . . .   <- base (descender line)
```

**Width Variants:**
- `width: 0` - hairline
- `width: 1` - normal (default)
- `width: 2` - bold

**Common Variants:**
- `descender.l` - left-positioned (for q)
- `descender.r` - right-positioned (for p)

---

### full-stem - Full-height stem

**Zone:** full (y=1 to y=10)  
**Description:** Vertical stroke spanning ascender to descender  
**Examples:** Rare; used in certain script combinations

**Required Anchors:** top, base, mid, mark-above, mark-below

**Canonical Path (width 1):**
```
@elem full-stem
zone: full
path: p1 p2
p1 = [6,1]
p2 = [6,10]
width: 1
anchors: top=[6,1] base=[6,10] mid=[6,5]
         mark-above=[6,0] mark-below=[6,11]
@end
```

**ASCII Diagram:**
```
    0 1 2 3 4 5 6 7 8 9 10 11 12
  0 . . . . . . ^ . . . . . . .   <- mark-above
  1 . . . . . . * . . . . . . .   <- top (ascender)
  2 . . . . . . | . . . . . . .
  3 . . . . . . | . . . . . . .
  4 . . . . . . | . . . . . . .   <- x-top
  5 . . . . . . * . . . . . . .   <- mid
  6 . . . . . . | . . . . . . .
  7 . . . . . . | . . . . . . .
  8 . . . . . . | . . . . . . .   <- baseline
  9 . . . . . . | . . . . . . .
 10 . . . . . . * . . . . . . .   <- base (descender)
 11 . . . . . . v . . . . . . .   <- mark-below
```

**Width Variants:**
- `width: 0` - hairline
- `width: 1` - normal (default)
- `width: 2` - bold

---

## 2. Curves (12 elements)

### bowl - Closed round form

**Zone:** x-height (y=4 to y=8)  
**Description:** Full closed circular/oval shape  
**Examples:** o, b (right side), d (left side), p, q

**Required Anchors:** attach, mark-above, mark-below

**Canonical Path (width 1):**
```
@elem bowl
zone: x-height
path: p1 C(p2,p3) C(p4,p5) C(p6,p7) C(p8,p1)
p1 = [2,6]
p2 = [2,4]
p3 = [6,4]
p4 = [10,4]
p5 = [10,6]
p6 = [10,8]
p7 = [6,8]
p8 = [2,8]
close: true
width: 1
anchors: attach=[2,6] mark-above=[6,3] mark-below=[6,9]
@end
```

**ASCII Diagram:**
```
    0 1 2 3 4 5 6 7 8 9 10 11 12
  3 . . . . . . ^ . . . . . . .   <- mark-above
  4 . . . .o----*----o. . . . .   <- top of bowl
  5 . . o . . . . . . . o . . .
  6 * . . . . . . . . . . . . *   <- attach (left), widest point
  7 . . o . . . . . . . o . . .
  8 . . . .o----*----o. . . . .   <- base of bowl (baseline)
  9 . . . . . . v . . . . . . .   <- mark-below
```

**Width Variants:**
- `width: 0` - hairline outline
- `width: 1` - normal stroke (default)
- `width: 2` - bold stroke

**Common Variants:**
- `bowl.l` - left-facing bowl (attach on right at x=10)
- `bowl.r` - right-facing bowl (attach on left at x=2, same as default)
- `bowl.upper` - top half only (y=4 to y=6)
- `bowl.lower` - bottom half only (y=6 to y=8)
- `bowl.full` - standalone round (as in o), no flat attachment side

---

### bowl.upper - Upper half-bowl

**Zone:** x-height (y=4 to y=6)  
**Description:** Top half of a bowl shape  
**Examples:** B (top bowl), beta (top)

**Required Anchors:** attach, top, base

**Canonical Path (width 1):**
```
@elem bowl.upper
zone: x-height
path: p1 C(p2,p3) C(p4,p5)
p1 = [2,6]
p2 = [2,4]
p3 = [6,4]
p4 = [10,4]
p5 = [10,6]
width: 1
anchors: attach=[2,6] top=[6,4] base=[6,6]
@end
```

**ASCII Diagram:**
```
    0 1 2 3 4 5 6 7 8 9 10 11 12
  4 . . . .o----*----o. . . . .   <- top
  5 . . o . . . . . . . o . . .
  6 *-----------*-----------* .   <- attach, base
```

---

### bowl.lower - Lower half-bowl

**Zone:** x-height (y=6 to y=8)  
**Description:** Bottom half of a bowl shape  
**Examples:** B (bottom bowl), beta (bottom)

**Required Anchors:** attach, top, base

**Canonical Path (width 1):**
```
@elem bowl.lower
zone: x-height
path: p1 C(p2,p3) C(p4,p5)
p1 = [2,6]
p2 = [2,8]
p3 = [6,8]
p4 = [10,8]
p5 = [10,6]
width: 1
anchors: attach=[2,6] top=[6,6] base=[6,8]
@end
```

**ASCII Diagram:**
```
    0 1 2 3 4 5 6 7 8 9 10 11 12
  6 *-----------*-----------* .   <- attach, top
  7 . . o . . . . . . . o . . .
  8 . . . .o----*----o. . . . .   <- base (baseline)
```

---

### counter - Interior of a bowl

**Zone:** x-height  
**Description:** The interior negative space of a bowl (implicit, not drawn)  
**Examples:** Interior of o, b, d, p, q

**Required Anchors:** (implicit; not drawn)

**Note:** Counter is a semantic element representing the enclosed white space
within a bowl. It has no path geometry and is not rendered.

---

### arc.top - Open curve, top half

**Zone:** x-height (y=4 to y=6)  
**Description:** Open arc curving at top  
**Examples:** c (top), s (top), C (top)

**Required Anchors:** left, right, top

**Canonical Path (width 1):**
```
@elem arc.top
zone: x-height
path: p1 C(p2,p3) C(p4,p5)
p1 = [2,6]
p2 = [2,4]
p3 = [6,4]
p4 = [10,4]
p5 = [10,6]
width: 1
anchors: left=[2,6] right=[10,6] top=[6,4]
@end
```

**ASCII Diagram:**
```
    0 1 2 3 4 5 6 7 8 9 10 11 12
  4 . . . .o----*----o. . . . .   <- top
  5 . . o . . . . . . . o . . .
  6 * . . . . . . . . . . . . *   <- left, right
```

---

### arc.bot - Open curve, bottom half

**Zone:** x-height (y=6 to y=8)  
**Description:** Open arc curving at bottom  
**Examples:** s (bottom), epsilon (bottom)

**Required Anchors:** left, right, base

**Canonical Path (width 1):**
```
@elem arc.bot
zone: x-height
path: p1 C(p2,p3) C(p4,p5)
p1 = [2,6]
p2 = [2,8]
p3 = [6,8]
p4 = [10,8]
p5 = [10,6]
width: 1
anchors: left=[2,6] right=[10,6] base=[6,8]
@end
```

**ASCII Diagram:**
```
    0 1 2 3 4 5 6 7 8 9 10 11 12
  6 * . . . . . . . . . . . . *   <- left, right
  7 . . o . . . . . . . o . . .
  8 . . . .o----*----o. . . . .   <- base
```

---

### hook.top - Curved entry at top

**Zone:** ascender (y=1 to y=4)  
**Description:** Curved hook shape at top of stroke  
**Examples:** f (top), Gamma (top)

**Required Anchors:** attach, base

**Canonical Path (width 1):**
```
@elem hook.top
zone: ascender
path: p1 C(p2,p3)
p1 = [10,1]
p2 = [6,1]
p3 = [6,4]
width: 1
anchors: attach=[10,1] base=[6,4]
@end
```

**ASCII Diagram:**
```
    0 1 2 3 4 5 6 7 8 9 10 11 12
  1 . . . . . . o . . . * . . .   <- attach (entry point)
  2 . . . . . . | . .-' . . . .
  3 . . . . . . | . . . . . . .
  4 . . . . . . * . . . . . . .   <- base (connects to stem)
```

---

### hook.bot - Curved exit at bottom

**Zone:** descender (y=8 to y=10)  
**Description:** Curved hook shape at bottom of stroke  
**Examples:** j (bottom), J (bottom)

**Required Anchors:** attach, top

**Canonical Path (width 1):**
```
@elem hook.bot
zone: descender
path: p1 C(p2,p3)
p1 = [6,8]
p2 = [6,10]
p3 = [2,10]
width: 1
anchors: attach=[2,10] top=[6,8]
@end
```

**ASCII Diagram:**
```
    0 1 2 3 4 5 6 7 8 9 10 11 12
  8 . . . . . . * . . . . . . .   <- top (connects from stem)
  9 . . . . . . | . . . . . . .
 10 . . * . . . o . . . . . . .   <- attach (exit point)
```

---

### loop - Closed curve below baseline

**Zone:** descender (y=8 to y=11)  
**Description:** Closed loop form below baseline  
**Examples:** g (double-storey)

**Required Anchors:** attach, top

**Canonical Path (width 1):**
```
@elem loop
zone: descender
path: p1 C(p2,p3) C(p4,p5) C(p6,p7) C(p8,p1)
p1 = [6,8]
p2 = [2,8]
p3 = [2,10]
p4 = [2,11]
p5 = [6,11]
p6 = [10,11]
p7 = [10,10]
p8 = [10,8]
close: true
width: 1
anchors: attach=[6,8] top=[6,8]
@end
```

**ASCII Diagram:**
```
    0 1 2 3 4 5 6 7 8 9 10 11 12
  8 . . . . o---*---o . . . . .   <- attach/top (connects to stem)
  9 . . . o . . . . . o . . . .
 10 . . o . . . . . . . o . . .
 11 . . . . o-------o . . . . .   <- bottom of loop
```

---

### ear - Small projection

**Zone:** x-height (y=4 to y=5)  
**Description:** Small curved projection at top of bowl  
**Examples:** g (single-storey), r

**Required Anchors:** attach

**Canonical Path (width 1):**
```
@elem ear
zone: x-height
path: p1 C(p2,p3)
p1 = [6,5]
p2 = [8,4]
p3 = [10,4]
width: 1
anchors: attach=[6,5]
@end
```

**ASCII Diagram:**
```
    0 1 2 3 4 5 6 7 8 9 10 11 12
  4 . . . . . . . . o---* . . .   <- tip of ear
  5 . . . . . . * . . . . . . .   <- attach
```

---

### shoulder - Arch from stem

**Zone:** x-height (y=4 to y=8)  
**Description:** Curved arch connecting stem to another stem  
**Examples:** h, m, n

**Required Anchors:** attach, top, base

**Canonical Path (width 1):**
```
@elem shoulder
zone: x-height
path: p1 C(p2,p3) p4
p1 = [2,6]
p2 = [2,4]
p3 = [6,4]
p4 = [10,4]
p5 = [10,8]
width: 1
anchors: attach=[2,6] top=[6,4] base=[10,8]
@end
```

**ASCII Diagram:**
```
    0 1 2 3 4 5 6 7 8 9 10 11 12
  4 . . . . o---*-------* . . .   <- top arch
  5 . . . o . . . . . . | . . .
  6 * . . . . . . . . . | . . .   <- attach (from stem)
  7 . . . . . . . . . . | . . .
  8 . . . . . . . . . . * . . .   <- base (to second stem)
```

---

### ogee - S-curve

**Zone:** full (y=0 to y=12)  
**Description:** Double-reverse S-curve shape  
**Examples:** integral sign, xi

**Required Anchors:** top, base

**Canonical Path (width 1):**
```
@elem ogee
zone: full
path: p1 C(p2,p3) C(p4,p5)
p1 = [8,1]
p2 = [4,3]
p3 = [8,6]
p4 = [4,9]
p5 = [8,11]
width: 1
anchors: top=[8,1] base=[8,11]
@end
```

**ASCII Diagram:**
```
    0 1 2 3 4 5 6 7 8 9 10 11 12
  1 . . . . . . . . * . . . . .   <- top
  2 . . . . . . . / . . . . . .
  3 . . . . o . / . . . . . . .   <- first inflection
  4 . . . . . / . . . . . . . .
  5 . . . . / . . . . . . . . .
  6 . . . . . . . . o . . . . .   <- center
  7 . . . . . . . . . \ . . . .
  8 . . . . . . . . . . \ . . .
  9 . . . . o . . . . . . . . .   <- second inflection
 10 . . . . . \ . . . . . . . .
 11 . . . . . . . . * . . . . .   <- base
```

---

## 3. Horizontals and Diagonals (13 elements)

### crossbar - Horizontal stroke

**Zone:** x-height (y=5 to y=7, typically y=6)  
**Description:** Horizontal bar at mid-height  
**Examples:** A, H, e, f

**Required Anchors:** left, right, mid

**Canonical Path (width 1):**
```
@elem crossbar
zone: x-height
path: p1 p2
p1 = [1,6]
p2 = [11,6]
width: 1
anchors: left=[1,6] right=[11,6] mid=[6,6]
@end
```

**ASCII Diagram:**
```
    0 1 2 3 4 5 6 7 8 9 10 11 12
  6 . *---------*---------* . .   <- left, mid, right
```

**Width Variants:**
- `width: 0` - hairline
- `width: 1` - normal (default)
- `width: 2` - bold

---

### bar.top - Bar at top of glyph

**Zone:** cap (y=0 to y=2)  
**Description:** Horizontal bar at cap height  
**Examples:** T, Gamma

**Required Anchors:** left, right

**Canonical Path (width 1):**
```
@elem bar.top
zone: cap
path: p1 p2
p1 = [0,2]
p2 = [12,2]
width: 1
anchors: left=[0,2] right=[12,2]
@end
```

**ASCII Diagram:**
```
    0 1 2 3 4 5 6 7 8 9 10 11 12
  2 *-----------------------* .   <- left, right (cap-height)
```

---

### bar.bot - Bar at bottom of glyph

**Zone:** x-height (y=8)  
**Description:** Horizontal bar at baseline  
**Examples:** L, Tse (Cyrillic)

**Required Anchors:** left, right

**Canonical Path (width 1):**
```
@elem bar.bot
zone: x-height
path: p1 p2
p1 = [0,8]
p2 = [12,8]
width: 1
anchors: left=[0,8] right=[12,8]
@end
```

**ASCII Diagram:**
```
    0 1 2 3 4 5 6 7 8 9 10 11 12
  8 *-----------------------* .   <- left, right (baseline)
```

---

### bar.mid - Bar at x-height

**Zone:** x-height (y=4)  
**Description:** Horizontal bar at x-height  
**Examples:** e (crossbar), G

**Required Anchors:** left, right

**Canonical Path (width 1):**
```
@elem bar.mid
zone: x-height
path: p1 p2
p1 = [2,4]
p2 = [10,4]
width: 1
anchors: left=[2,4] right=[10,4]
@end
```

**ASCII Diagram:**
```
    0 1 2 3 4 5 6 7 8 9 10 11 12
  4 . . *---------------* . . .   <- left, right (x-top)
```

---

### arm - Horizontal projecting from stem

**Zone:** x-height (y=4 to y=8)  
**Description:** Short horizontal stroke projecting from a vertical  
**Examples:** E, F, K, Cyrillic Zhe

**Required Anchors:** attach

**Canonical Path (width 1):**
```
@elem arm
zone: x-height
path: p1 p2
p1 = [6,6]
p2 = [12,6]
width: 1
anchors: attach=[6,6]
@end
```

**ASCII Diagram:**
```
    0 1 2 3 4 5 6 7 8 9 10 11 12
  6 . . . . . . *-----------* .   <- attach, end
```

**Common Variants:**
- `arm.l` - arm projecting left
- `arm.r` - arm projecting right (default)
- `arm.upper` - arm at upper position (y=4)
- `arm.lower` - arm at lower position (y=8)

---

### leg - Diagonal descending from junction

**Zone:** x-height (y=4 to y=8)  
**Description:** Diagonal stroke descending from a junction  
**Examples:** K, R, k

**Required Anchors:** attach, base

**Canonical Path (width 1):**
```
@elem leg
zone: x-height
path: p1 p2
p1 = [6,6]
p2 = [12,8]
width: 1
anchors: attach=[6,6] base=[12,8]
@end
```

**ASCII Diagram:**
```
    0 1 2 3 4 5 6 7 8 9 10 11 12
  6 . . . . . . * . . . . . . .   <- attach
  7 . . . . . . . \ . . . . . .
  8 . . . . . . . . . . . . * .   <- base
```

**Common Variants:**
- `leg.l` - leg descending to left
- `leg.r` - leg descending to right (default)

---

### diagonal - Full-height diagonal

**Zone:** cap (y=0 to y=8)  
**Description:** Diagonal stroke spanning full cap height  
**Examples:** N, Z, Cyrillic I

**Required Anchors:** top, base

**Canonical Path (width 1):**
```
@elem diagonal
zone: cap
path: p1 p2
p1 = [0,0]
p2 = [12,8]
width: 1
anchors: top=[0,0] base=[12,8]
@end
```

**ASCII Diagram:**
```
    0 1 2 3 4 5 6 7 8 9 10 11 12
  0 * . . . . . . . . . . . . .   <- top
  1 . \ . . . . . . . . . . . .
  2 . . \ . . . . . . . . . . .
  3 . . . \ . . . . . . . . . .
  4 . . . . . \ . . . . . . . .
  5 . . . . . . \ . . . . . . .
  6 . . . . . . . . \ . . . . .
  7 . . . . . . . . . \ . . . .
  8 . . . . . . . . . . . . * .   <- base
```

**Common Variants:**
- `diagonal.l` - descending left-to-right (default)
- `diagonal.r` - descending right-to-left (mirrored)

---

### apex - Meeting point of two diagonals (top)

**Zone:** cap (y=0 to y=4)  
**Description:** Point where two diagonal strokes meet at top  
**Examples:** A, Lambda, Cyrillic El

**Required Anchors:** top, left, right

**Canonical Path (width 1):**
```
@elem apex
zone: cap
path: p1 p2 p3
p1 = [0,8]
p2 = [6,0]
p3 = [12,8]
width: 1
anchors: top=[6,0] left=[0,8] right=[12,8]
@end
```

**ASCII Diagram:**
```
    0 1 2 3 4 5 6 7 8 9 10 11 12
  0 . . . . . . * . . . . . . .   <- top (apex point)
  1 . . . . . / . \ . . . . . .
  2 . . . . / . . . \ . . . . .
  3 . . . / . . . . . \ . . . .
  4 . . / . . . . . . . \ . . .
  5 . / . . . . . . . . . \ . .
  6 . . . . . . . . . . . . . .
  7 / . . . . . . . . . . . . \
  8 * . . . . . . . . . . . . *   <- left, right (base)
```

---

### vertex - Bottom meeting of diagonals

**Zone:** x-height (y=4 to y=8)  
**Description:** Point where two diagonal strokes meet at bottom  
**Examples:** V, W

**Required Anchors:** base, left, right

**Canonical Path (width 1):**
```
@elem vertex
zone: x-height
path: p1 p2 p3
p1 = [0,4]
p2 = [6,8]
p3 = [12,4]
width: 1
anchors: base=[6,8] left=[0,4] right=[12,4]
@end
```

**ASCII Diagram:**
```
    0 1 2 3 4 5 6 7 8 9 10 11 12
  4 * . . . . . . . . . . . . *   <- left, right (top)
  5 . \ . . . . . . . . . . / .
  6 . . \ . . . . . . . . / . .
  7 . . . \ . . . . . . / . . .
  8 . . . . . . * . . . . . . .   <- base (vertex point)
```

---

### spine - Central S-curve

**Zone:** x-height (y=4 to y=8)  
**Description:** S-shaped central stroke  
**Examples:** S, s, Cyrillic Ze

**Required Anchors:** top, base

**Canonical Path (width 1):**
```
@elem spine
zone: x-height
path: p1 C(p2,p3) C(p4,p5)
p1 = [10,4]
p2 = [6,4]
p3 = [6,6]
p4 = [6,8]
p5 = [2,8]
width: 1
anchors: top=[10,4] base=[2,8]
@end
```

**ASCII Diagram:**
```
    0 1 2 3 4 5 6 7 8 9 10 11 12
  4 . . . . . . o . . . * . . .   <- top
  5 . . . . . . . \ . . . . . .
  6 . . . . . . . . o . . . . .   <- center inflection
  7 . . . . . / . . . . . . . .
  8 . . * . o . . . . . . . . .   <- base
```

---

### tail - Terminal flourish

**Zone:** descender (y=8 to y=11)  
**Description:** Decorative tail extending below baseline  
**Examples:** Q, Cyrillic Shcha

**Required Anchors:** attach

**Canonical Path (width 1):**
```
@elem tail
zone: descender
path: p1 C(p2,p3)
p1 = [6,8]
p2 = [8,10]
p3 = [10,11]
width: 1
anchors: attach=[6,8]
@end
```

**ASCII Diagram:**
```
    0 1 2 3 4 5 6 7 8 9 10 11 12
  8 . . . . . . * . . . . . . .   <- attach (baseline)
  9 . . . . . . . \ . . . . . .
 10 . . . . . . . . o . . . . .
 11 . . . . . . . . . . * . . .   <- tip
```

---

### stroke.diag - Overlay diagonal slash

**Zone:** x-height (y=4 to y=8)  
**Description:** Diagonal stroke overlaying a character  
**Examples:** Oslash, oslash

**Required Anchors:** mid

**Canonical Path (width 1):**
```
@elem stroke.diag
zone: x-height
path: p1 p2
p1 = [2,8]
p2 = [10,4]
width: 1
anchors: mid=[6,6]
@end
```

**ASCII Diagram:**
```
    0 1 2 3 4 5 6 7 8 9 10 11 12
  4 . . . . . . . . . . * . . .   <- top-right
  5 . . . . . . . . . / . . . .
  6 . . . . . . * . / . . . . .   <- mid
  7 . . . . . / . . . . . . . .
  8 . . * . . . . . . . . . . .   <- bottom-left
```

---

### stroke.horiz - Overlay horizontal bar

**Zone:** x-height (y=6)  
**Description:** Horizontal stroke overlaying a character  
**Examples:** lstroke, Hbar, dbar

**Required Anchors:** left, right

**Canonical Path (width 1):**
```
@elem stroke.horiz
zone: x-height
path: p1 p2
p1 = [2,6]
p2 = [10,6]
width: 1
anchors: left=[2,6] right=[10,6]
@end
```

**ASCII Diagram:**
```
    0 1 2 3 4 5 6 7 8 9 10 11 12
  6 . . *---------------* . . .   <- left, right
```

---

## 4. Terminals (7 elements)

### serif - Perpendicular terminal

**Zone:** (varies)  
**Description:** Small perpendicular stroke at end of stem  
**Examples:** Style-dependent; seriffed typefaces

**Required Anchors:** attach

**Canonical Path (width 1):**
```
@elem serif
zone: x-height
path: p1 p2 p3
p1 = [4,8]
p2 = [6,8]
p3 = [8,8]
width: 1
anchors: attach=[6,8]
@end
```

**ASCII Diagram:**
```
    0 1 2 3 4 5 6 7 8 9 10 11 12
  8 . . . . *---*---* . . . . .   <- serif at baseline
               ^
              attach
```

**Common Variants:**
- `serif.top` - at top of stem
- `serif.bot` - at bottom of stem (default)
- `serif.l` - bracketed left serif
- `serif.r` - bracketed right serif
- `serif.bilateral` - full bilateral serif

---

### spur - Small serif-like projection

**Zone:** (varies)  
**Description:** Small decorative projection, smaller than full serif  
**Examples:** b (bottom), G (bar)

**Required Anchors:** attach

**Canonical Path (width 1):**
```
@elem spur
zone: x-height
path: p1 p2
p1 = [6,8]
p2 = [8,8]
width: 1
anchors: attach=[6,8]
@end
```

**ASCII Diagram:**
```
    0 1 2 3 4 5 6 7 8 9 10 11 12
  8 . . . . . . *---* . . . . .   <- small projection
               ^
              attach
```

---

### ball - Circular terminal

**Zone:** (varies)  
**Description:** Round ball-shaped terminal  
**Examples:** a (some styles), c (some styles), f, r

**Required Anchors:** attach

**Canonical Path (width 1):**
```
@elem ball
zone: x-height
path: p1 C(p2,p3) C(p4,p5) C(p6,p7) C(p8,p1)
p1 = [8,4]
p2 = [9,4]
p3 = [10,5]
p4 = [10,6]
p5 = [9,6]
p6 = [8,6]
p7 = [8,5]
p8 = [8,4]
close: true
width: 1
anchors: attach=[8,5]
@end
```

**ASCII Diagram:**
```
    0 1 2 3 4 5 6 7 8 9 10 11 12
  4 . . . . . . . . o-o . . . .
  5 . . . . . . . . * | . . . .   <- attach (center)
  6 . . . . . . . . o-o . . . .
```

---

### finial - Tapered terminal

**Zone:** (varies)  
**Description:** Tapered end of a curved stroke  
**Examples:** e (arm), c (terminals)

**Required Anchors:** attach

**Canonical Path (width 1):**
```
@elem finial
zone: x-height
path: p1 p2 C(p3,p4)
p1 = [10,5]
p2 = [11,5]
p3 = [12,5]
p4 = [12,6]
width: 1
anchors: attach=[10,5]
@end
```

**ASCII Diagram:**
```
    0 1 2 3 4 5 6 7 8 9 10 11 12
  5 . . . . . . . . . . *-->  .   <- tapered end
                       ^
                      attach
```

---

### swash - Extended decorative terminal

**Zone:** (varies)  
**Description:** Elongated decorative stroke extension  
**Examples:** Style-dependent; decorative/script typefaces

**Required Anchors:** attach

**Canonical Path (width 1):**
```
@elem swash
zone: x-height
path: p1 C(p2,p3) C(p4,p5)
p1 = [6,8]
p2 = [8,8]
p3 = [10,9]
p4 = [11,10]
p5 = [12,10]
width: 1
anchors: attach=[6,8]
@end
```

**ASCII Diagram:**
```
    0 1 2 3 4 5 6 7 8 9 10 11 12
  8 . . . . . . * . . . . . . .   <- attach
  9 . . . . . . . . . . o . . .
 10 . . . . . . . . . . . . * .   <- extended tip
```

---

### flag - Small horizontal at top of stem

**Zone:** (varies)  
**Description:** Short horizontal stroke at top of stem  
**Examples:** 1, Cyrillic soft sign

**Required Anchors:** attach

**Canonical Path (width 1):**
```
@elem flag
zone: x-height
path: p1 p2
p1 = [4,4]
p2 = [6,4]
width: 1
anchors: attach=[6,4]
@end
```

**ASCII Diagram:**
```
    0 1 2 3 4 5 6 7 8 9 10 11 12
  4 . . . . *---* . . . . . . .   <- flag at top
               ^
              attach
```

---

### tittle - Dot above

**Zone:** x-height (y=2 to y=3)  
**Description:** Small dot above letter body  
**Examples:** i, j

**Required Anchors:** attach

**Canonical Path (width 1):**
```
@elem tittle
zone: x-height
path: p1
p1 = [6,3]
width: 1
anchors: attach=[6,4]
@end
```

**ASCII Diagram:**
```
    0 1 2 3 4 5 6 7 8 9 10 11 12
  3 . . . . . . * . . . . . . .   <- dot
  4 . . . . . . ^ . . . . . . .   <- attach (connects to stem top)
```

**Note:** Tittle is typically rendered as a small filled circle, not a path stroke.

---

## 5. Special (3 elements)

### dot - Period/point

**Zone:** (varies)  
**Description:** Standalone dot/period  
**Examples:** Period, ellipsis components, decimal point

**Required Anchors:** attach

**Canonical Path (width 1):**
```
@elem dot
zone: x-height
path: p1
p1 = [6,8]
width: 1
anchors: attach=[6,8]
@end
```

**ASCII Diagram:**
```
    0 1 2 3 4 5 6 7 8 9 10 11 12
  8 . . . . . . * . . . . . . .   <- dot at baseline
               ^
              attach
```

**Note:** Rendered as a small filled circle, not a path stroke.

---

### caron.alt - Vertical stroke (hacek variant)

**Zone:** x-height (y=1 to y=4)  
**Description:** Vertical stroke variant of caron/hacek  
**Examples:** dcaron, tcaron, Lcaron

**Required Anchors:** attach

**Canonical Path (width 1):**
```
@elem caron.alt
zone: x-height
path: p1 p2
p1 = [9,1]
p2 = [9,4]
width: 1
anchors: attach=[9,4]
@end
```

**ASCII Diagram:**
```
    0 1 2 3 4 5 6 7 8 9 10 11 12
  1 . . . . . . . . . * . . . .   <- top of stroke
  2 . . . . . . . . . | . . . .
  3 . . . . . . . . . | . . . .
  4 . . . . . . . . . * . . . .   <- attach
```

**Note:** Used in Czech/Slovak typography where the standard caron would collide with ascenders.

---

### comma.shape - Comma-shaped mark

**Zone:** (varies)  
**Description:** Comma-shaped diacritical mark  
**Examples:** Cyrillic palatal marks, cedilla variants

**Required Anchors:** attach

**Canonical Path (width 1):**
```
@elem comma.shape
zone: diacritic-below
path: p1 C(p2,p3)
p1 = [6,9]
p2 = [6,10]
p3 = [5,11]
width: 1
anchors: attach=[6,9]
@end
```

**ASCII Diagram:**
```
    0 1 2 3 4 5 6 7 8 9 10 11 12
  9 . . . . . . * . . . . . . .   <- attach (top of comma)
 10 . . . . . . | . . . . . . .
 11 . . . . . * . . . . . . . .   <- tail curves left
```

---

## Appendix A: Element Summary by Category

| Category                  | Count | Elements |
|---------------------------|-------|----------|
| Verticals                 | 4     | stem, ascender, descender, full-stem |
| Curves                    | 12    | bowl, bowl.upper, bowl.lower, counter, arc.top, arc.bot, hook.top, hook.bot, loop, ear, shoulder, ogee |
| Horizontals and Diagonals | 13    | crossbar, bar.top, bar.bot, bar.mid, arm, leg, diagonal, apex, vertex, spine, tail, stroke.diag, stroke.horiz |
| Terminals                 | 7     | serif, spur, ball, finial, swash, flag, tittle |
| Special                   | 3     | dot, caron.alt, comma.shape |
| **Total**                 | **39**|  |

## Appendix B: Standard Anchor Reference

| Anchor Name    | Typical Position | Description                           |
|----------------|------------------|---------------------------------------|
| `top`          | y=4 or y=0       | Top connection point                  |
| `base`         | y=8              | Bottom/baseline connection            |
| `mid`          | y=6              | Vertical midpoint                     |
| `attach`       | varies           | General attachment point              |
| `mark-above`   | y=3              | Diacritic attachment above            |
| `mark-below`   | y=9              | Diacritic attachment below            |
| `arm.left`     | x=0, y=6         | Left arm connection                   |
| `arm.right`    | x=12, y=6        | Right arm connection                  |
| `top-serif`    | y=3              | Top serif attachment                  |
| `bot-serif`    | y=9              | Bottom serif attachment               |
| `left`         | x=0-2            | Left edge connection                  |
| `right`        | x=10-12          | Right edge connection                 |

## Appendix C: Variant Tag Reference

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
