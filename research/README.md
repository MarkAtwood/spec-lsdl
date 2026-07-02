# LSDL Research

Experimental work on bidirectional font generation using LSDL structure.

## Projects

### Style Encoder
Extract a learned style embedding from existing fonts. Given Bookman.otf and the LSDL foundation database, produce a 128-dimensional vector that captures "what Bookman is beyond the structure."

### Style Decoder  
Generate OpenType-compatible outlines from LSDL expressions and a style embedding. Enables:
- Font generation from LSDL + style
- Style transfer (Helvetica structure + Garamond style)
- Style interpolation

## Status

Planning phase. See [PLAN.md](PLAN.md) for research roadmap.

## Key Insight

LSDL provides strong structural conditioning. We're not doing open-ended glyph generation — we know `b = STACK(ascender, bowl.r)`. The model only needs to learn how to *render* that known structure in a given style. This makes the problem tractable with small models.
