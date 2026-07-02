# LSDL Research Plan: Bidirectional Font Generation

Two related projects that close the loop between LSDL structure and font files.

## Overview

```
OpenType ──► Style Encoder ──► style_vec[128] ──┐
(Bookman)        (learned)                       │
                                                 ▼
              LSDL structure ──► Style Decoder ──► OpenType output
              (foundation db)       (learned)
```

**Project 1:** Style Encoder — extract style embedding from existing font  
**Project 2:** Style Decoder — render LSDL + style embedding → font outlines

---

## Project 1: Style Encoder

### Day 1: Registration Prototype

Get AI to write a registration module that aligns LSDL structure to font outlines.

**Input:** Font file + LSDL expression for a glyph  
**Output:** Outline segments labeled by LSDL element

```python
register("Bookman.otf", "b", "STACK(ascender, bowl.r)")
# → {"ascender": [bezier segments...], "bowl.r": [bezier segments...]}
```

**Key constraint:** LSDL anchors are landmarks. `ascender.base` meets `bowl.r.top`. Use anchor positions to initialize, refine from there.

Validate on 10 glyphs from 3 fonts. Fix failures. Should work by end of day.

### Day 2: Registration at Scale

Run registration on Google Fonts subset (pick 200 diverse fonts with good Latin coverage).

- Parallelize across fonts
- Log failures, categorize failure modes
- Target: 85%+ glyphs register successfully

Filter to fonts where registration works. That's your training set.

### Day 3: Encoder Model

Simple architecture:

```
per-element outlines → small CNN each → concat → MLP → style_vec[128]
```

Or even simpler: flatten all outline points, linear projection. Start dumb, add complexity only if needed.

Training: contrastive loss. Glyphs from same font should embed nearby; different fonts should separate.

```python
loss = triplet_loss(anchor=encode(font_a, glyph_1),
                    positive=encode(font_a, glyph_2),
                    negative=encode(font_b, glyph_1))
```

Train overnight. Check clusters in morning.

### Day 4: Validation

- Do serif/sans fonts separate in embedding space?
- Nearest neighbors: is Bookman near other transitional serifs?
- PCA: do top components mean anything?

If clustering is bad, debug. If good, encoder is done.

---

## Project 2: Style Decoder

### Day 1-2: Decoder Model

**Architecture:**

```
LSDL tree ──► tree flatten ──► transformer encoder ──┐
                                                      ├──► transformer decoder ──► control points
style_vec[128] ──► project to d_model ───────────────┘
```

Or simpler: per-element MLP that takes (element_type, style_vec) → outline for that element. Compose per LSDL structure.

**Output format:** Sequence of (x, y, on_curve) tuples. Convert to cubic Beziers post-hoc.

**Training data:** Registration output from Project 1. Each (lsdl_expr, font_id, target_outline) is a training example.

### Day 3: Training + Debug

Train decoder. Visualize outputs. Fix obvious failures (self-intersections, wrong scale, etc.).

Iterate: if outputs are bad, try different architecture, more data, different loss.

### Day 4: OpenType Output

Wire up fontTools to emit actual .otf files:

```python
def generate_font(lsdl_db, style_vec, output_path):
    outlines = {char: decode(expr, style_vec) for char, expr in lsdl_db}
    write_otf(outlines, output_path)
```

Validate: does the output font render? Pass fontbakery checks?

---

## Combined Timeline

| Day | Morning | Afternoon |
|-----|---------|-----------|
| 0 | Corpus collection | Parse all fonts, filter broken ones |
| 1 | Registration prototype | Debug on diverse fonts |
| 2 | Registration at scale | Start encoder architecture |
| 3 | Train encoder | Evaluate encoder, start decoder |
| 4 | Train decoder | OpenType integration |
| 5 | End-to-end test | Buffer / polish |

**Total: ~1 week** for working prototype of both directions.

Day 0 can run in background while doing other things. Scrape font directories, extract metadata, filter to fonts with Latin coverage and parseable outlines.

---

## What Success Looks Like

**Minimum:**
- `encode(Bookman.otf)` → 128-dim vector
- `decode(lsdl_db, that_vector)` → .otf file that looks vaguely Bookman-ish

**Good:**
- Generated font is visually similar to source
- `0.5 * encode(Futura) + 0.5 * encode(Garamond)` produces coherent hybrid
- Embedding space clusters by style (serif/sans, weight, width)

**Great:**
- Style transfer works (Helvetica structure in Garamond style)
- Individual embedding dimensions are interpretable
- Can generate novel styles by sampling embedding space

---

## Infrastructure

**Already have:**
- LSDL parser, evaluator, foundation database
- Python environment

**Need:**
- fontTools (`pip install fonttools`)
- PyTorch (`pip install torch`)

**Training corpus:** Everything. Models are not derivative works (current legal consensus). Train on:
- Google Fonts (~1500 libre fonts)
- Adobe Fonts catalog
- Monotype/Linotype classics (Helvetica, Times, Palatino, Univers, Frutiger...)
- System fonts (whatever's installed)
- Historical digitizations
- Anything you can parse

Target: 3000-5000 fonts covering the full typographic landscape. The embedding space should know where Helvetica lives, not just its libre imitators.

**Compute:** Single GPU for training. Laptop CPU fine for inference.

---

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Registration fails on many fonts | Filter aggressively; 100 clean fonts > 500 messy ones |
| Encoder doesn't cluster meaningfully | Try different architectures; add supervised signal (serif/sans labels) |
| Decoder outputs garbage | Start with per-element MLPs (simpler); add structure gradually |
| Generated fonts don't validate | Debug with fontbakery; fix table issues incrementally |
| Embedding is uninterpretable | Probe with known categories; compare to Metafont params; accept if it works |

---

## Open Questions to Resolve Early

1. **Embedding size:** Start with 128. If PCA shows 90% variance in 32 dims, shrink it.

2. **Which glyphs matter for style?** Probably 'a', 'e', 'g', 'n', 'o'. Could encode just those and interpolate for rest.

3. **How to handle variable fonts?** Punt for v1. Treat each instance as separate font.

4. **Does Metafont emerge?** Check if learned dimensions correlate with Knuth's parameters (stem width, contrast, superness, slant). If they do, that's validation. If not, we learned something new.
