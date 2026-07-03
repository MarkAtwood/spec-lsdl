# LSDL Stroke Order Convention

## Principles

1. **Pull over push**: Downstrokes and rightward strokes preferred (natural for right-handed writers)
2. **Top-to-bottom**: Vertical strokes descend
3. **Left-to-right**: Horizontal strokes move rightward
4. **Counterclockwise bowls**: Closed curves wind counterclockwise (matches fill convention)
5. **Main stroke first**: Primary structural element before details
6. **Minimize lifts**: Continuous strokes where natural

## Path Direction Encoding

For elements with `path:` definitions:
- First point is stroke start
- Subsequent points follow stroke direction
- `close: true` paths should wind counterclockwise for fills

## Composition Order

For multi-element compositions, child order implies stroke sequence:

```
FRAME(elem1, elem2, elem3)  # stroke order: 1, 2, 3
LR(left, right, gap)        # stroke order: left, right
STACK(top, bottom)          # stroke order: top, bottom
```

## A-Z Uppercase Audit

| Letter | Current Definition | Stroke Order | Notes |
|--------|-------------------|--------------|-------|
| A | `APEX(stem.l, stem.r, crossbar.cap)` | 1,2,3 ✓ | Left diagonal, right diagonal, crossbar |
| B | `LR(stem.l, STACK(bowl.upper, bowl.lower), 3/9)` | 1,2,3 ✓ | Stem, upper bowl, lower bowl |
| C | `STACK(arc.top.cap, arc.bot.cap)` | ✗ | Should be single counterclockwise stroke |
| D | `LR(stem.l, bowl.r.cap, 3/9)` | 1,2 ✓ | Stem, then bowl clockwise |
| E | `FRAME(stem.l, arm.top, arm.mid, arm.bot)` | 1,2,3,4 ✓ | Stem, then arms top-to-bottom |
| F | `FRAME(stem.l, arm.top, arm.mid)` | 1,2,3 ✓ | Stem, then arms top-to-bottom |
| G | `FRAME(arc.top.cap, arc.bot.cap, bar.mid)` | ✗ | Arc should be one stroke, bar second |
| H | `FRAME(stem.l, crossbar.cap, stem.r)` | ✗ | Should be: stem.l, stem.r, crossbar |
| I | `stem.l` | 1 ✓ | Single stroke top-to-bottom |
| J | `STACK(stem.r, hook.bot)` | 1,2 ✓ | Continuous stroke possible |
| K | `FRAME(stem.l, diagonal.l, leg.cap)` | ✗ | Diagonal should be arm (in), leg (out) |
| L | `FRAME(stem.l, arm.bot)` | 1,2 ✓ | Stem down, arm right |
| M | `FRAME(stem.l, apex, stem.r)` | 1,2,3 ✓ | Left stem, apex zigzag, right stem |
| N | `FRAME(stem.l, diagonal, stem.r)` | 1,2,3 ✓ | Left stem, diagonal, right stem |
| O | `bowl.cap` | 1 ✓ | Single counterclockwise stroke |
| P | `LR(stem.l, bowl.upper, 3/9)` | 1,2 ✓ | Stem, bowl clockwise |
| Q | `FRAME(bowl.cap, tail)` | 1,2 ✓ | Bowl, then tail |
| R | `FRAME(stem.l, bowl.upper, leg.cap)` | 1,2,3 ✓ | Stem, bowl, leg |
| S | `FRAME(arc.top.cap, spine.cap, arc.bot.cap)` | ✗ | Should be single continuous curve |
| T | `FRAME(bar.top, stem)` | ✗ | Should be: stem, bar.top (or bar first is acceptable) |
| U | `FRAME(stem.l, arc.bot.cap, stem.r)` | ✗ | Single stroke or: left down, arc, right up |
| V | `vertex.cap` | 1 ✓ | Left diagonal down, right diagonal up |
| W | `LR(vertex.cap, vertex.cap, 6/6)` | 1,2 ✓ | Left V, right V |
| X | `OVR(diagonal, diagonal.l)` | 1,2 ✓ | Down-right diagonal, down-left diagonal |
| Y | `FRAME(diagonal.l, stem, diagonal)` | ✗ | Should be: diagonal.l, diagonal, stem |
| Z | `FRAME(bar.top, diagonal, bar.bot.cap)` | 1,2,3 ✓ | Top bar, diagonal, bottom bar |

## Issues Found and Fixed

### Uppercase (fixed)
- **H**: `FRAME(stem.l, stem.r, crossbar.cap)` - crossbar now last ✓
- **T**: `FRAME(stem, bar.top)` - stem now first ✓
- **Y**: `FRAME(diagonal.l, diagonal, stem)` - stem now last ✓
- **C, G, S, U**: Now single-stroke elements (arc.c.cap, arc.g.cap, curve.s.cap, arc.u.cap) ✓

### Lowercase (fixed)
- **c, s, u**: Now single-stroke elements (arc.c, curve.s, arc.u) ✓
- **e**: `FRAME(crossbar.low, arc.top, arc.bot)` - crossbar now first ✓
- **p**: `FRAME(descender, bowl.r)` - descender now first ✓

### STACK Visual vs Stroke Order
- **i, j**: STACK orders elements visually (tittle above stem), but stroke order is stem-first
- Documented in comments; STACK remains visual ordering operator

## Proposed Fixes

### 1. Reorder FRAME arguments

```lsdl
# Before
H = FRAME(stem.l, crossbar.cap, stem.r)
# After  
H = FRAME(stem.l, stem.r, crossbar.cap)

# Before
Y = FRAME(diagonal.l, stem, diagonal)
# After
Y = FRAME(diagonal.l, diagonal, stem)
```

### 2. Add stroke-order metadata (optional)

For cases where composition order can't encode stroke order:

```lsdl
T = FRAME(bar.top, stem) stroke-order:[2,1]
```

Or use explicit ordering in FRAME:

```lsdl
T = FRAME(stem, bar.top)  # stem first
```

### 3. Define single-stroke elements for continuous curves

```lsdl
@elem arc.c.cap  # C-shape, single counterclockwise stroke
  zone: [cap-height]
  path: ...
  
@elem curve.s.cap  # S-shape, single top-to-bottom stroke
  zone: [cap-height]
  path: ...
```

Then:
```lsdl
C = arc.c.cap
S = curve.s.cap
```

## Element Path Direction Rules

For element definitions:

| Element Type | Start Point | Direction |
|-------------|-------------|-----------|
| `stem.*` | Top | Descend |
| `arm.*`, `bar.*` | Left | Rightward |
| `diagonal` (NW-SE) | Top-left | Down-right |
| `diagonal.l` (NE-SW) | Top-right | Down-left |
| `bowl.*`, `arc.*` | Top | Counterclockwise |
| `hook.*` | Junction | Outward curve |
| `leg.*` | Junction | Down-outward |

## Validation

A stroke-order linter could check:
1. FRAME/LR/STACK argument order matches convention
2. Element paths start at conventional points
3. Closed paths wind counterclockwise
