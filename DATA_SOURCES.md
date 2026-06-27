# Data Sources

This document records the provenance of terminology, conventions, and reference data used in the LSDL specification.

## Typography Anatomy Sources

The element vocabulary in Section 6 draws from established typographic anatomy terminology. The following works informed element naming and definitions.

### Karen Cheng, *Designing Type* (2005)

- **Publisher:** Yale University Press
- **ISBN:** 978-0300111507
- **Used for:** Detailed anatomical breakdown of letterforms; informed element categories (verticals, curves, terminals) and specific names (bowl, stem, shoulder, ear, spur, finial)

### Robert Bringhurst, *The Elements of Typographic Style* (4th ed., 2012)

- **Publisher:** Hartley & Marks
- **ISBN:** 978-0881792126
- **Used for:** Foundational typographic terminology; metric zone concepts (x-height, baseline, cap-height); proportional relationships; spacing and composition conventions

### Jost Hochuli, *Detail in Typography* (2008)

- **Publisher:** Editions B42
- **ISBN:** 978-2917855027
- **Used for:** Fine-grained typographic detail; stroke weight conventions; terminal treatments; micro-typography considerations

### Adobe Type Glossary

- **Source:** https://fonts.adobe.com/fonts
- **Accessed:** 2026-02
- **Used for:** Industry-standard element naming (crossbar, counter, tittle, swash); contemporary digital typography conventions

### Google Fonts Knowledge

- **Source:** https://fonts.google.com/knowledge
- **Accessed:** 2026-02
- **Used for:** Accessible definitions cross-referenced against print sources; educational diagrams of letterform anatomy

## Element Derivation by Category

Section 6 organizes elements into five categories. Each category's vocabulary derives from the sources above as follows:

| Category                 | Count | Primary Sources                              |
|--------------------------|-------|----------------------------------------------|
| Verticals (6.2)          | 4     | Cheng (stem anatomy), Bringhurst (zones)     |
| Curves (6.3)             | 12    | Cheng (bowl, shoulder, ogee), Adobe (arc)    |
| Horizontals/Diagonals (6.4) | 13  | Cheng (crossbar, arm, leg), Adobe (spine)    |
| Terminals (6.5)          | 7     | Cheng (serif, ball, finial), Hochuli (spur)  |
| Special (6.6)            | 3     | LSDL-specific (caron.alt, comma.shape)       |

**Total:** 39 base elements (approximately 45 with standard variants)

## Metric System

### Traditional Terms

The vertical metric landmarks in Section 5.2 use established typographic terminology:

| LSDL Landmark  | Traditional Term                    | Source              |
|----------------|-------------------------------------|---------------------|
| `baseline`     | Baseline                            | Universal           |
| `x-top`        | x-height / mean line                | Bringhurst, Cheng   |
| `cap-height`   | Cap height / cap line               | Bringhurst          |
| `ascender`     | Ascender line                       | Bringhurst, Cheng   |
| `descender`    | Descender line                      | Bringhurst, Cheng   |
| `cap-top`      | Top of capitals + diacritics        | LSDL-specific       |
| `desc-limit`   | Descender clearance                 | LSDL-specific       |

### 12-Unit Grid Rationale

The 12-unit grid is shared with CSDL. The value 12 was chosen because:

1. **Divisibility:** 12 divides evenly by 2, 3, 4, and 6
2. **Zone mapping:** Common metric proportions map cleanly (x-height = 4 units, cap-height = 6 units from baseline)
3. **CSDL compatibility:** Maintains coordinate system parity with the CJK sister specification
4. **Traditional grids:** Echoes the em-square subdivision conventions in metal type (e.g., 12pt = 1 pica)

The `/24` override (Section 5.5) provides finer resolution when 12 units are insufficient.

## Unicode Mappings

### Appendix A: Script Coverage

Script coverage derives from the following Unicode blocks:

| Script   | Unicode Blocks                                           | Source Document        |
|----------|----------------------------------------------------------|------------------------|
| Latin    | U+0020-007E, U+0080-00FF, U+0100-024F, U+1E00-1EFF, etc. | Unicode Standard Ch. 7 |
| Greek    | U+0370-03FF (Greek and Coptic), U+1F00-1FFF (Extended)   | Unicode Standard Ch. 7 |
| Cyrillic | U+0400-04FF, U+0500-052F, U+2DE0-2DFF, U+A640-A69F, etc. | Unicode Standard Ch. 7 |

**Reference:** The Unicode Consortium, "The Unicode Standard", Version 16.0.0. https://www.unicode.org/versions/latest/

### Appendix C: Diacritics

The standard diacritic library maps to Unicode combining characters:

| Unicode Block                        | Range          | LSDL Diacritics    |
|--------------------------------------|----------------|--------------------|
| Combining Diacritical Marks          | U+0300-036F    | acute, grave, etc. |
| Combining Diacritical Marks Extended | U+1AB0-1AFF    | Extended marks     |
| Combining Diacritical Marks Supplement | U+1DC0-1DFF  | Supplement marks   |

### Appendix E: Orthography Tags

Tag registries derive from ISO standards:

| LSDL Feature  | Source Standard                                  |
|---------------|--------------------------------------------------|
| Script tags   | ISO 15924 (Codes for representation of scripts)  |
| Language tags | ISO 639-1/639-3 (Codes for language names)       |
| Tag structure | BCP 47 (Tags for Identifying Languages)          |

**References:**
- ISO 15924:2004, https://www.unicode.org/iso15924/
- ISO 639-1:2002
- BCP 47, RFC 5646, https://www.rfc-editor.org/info/bcp47

## Greek and Cyrillic Sources

### Unicode Standard

- **Source:** The Unicode Consortium, "The Unicode Standard", Chapters 7-8
- **Used for:** Character repertoire, canonical decomposition, combining mark behavior, script-specific properties

### Paratype Resources

- **Source:** https://www.paratype.com/
- **Used for:** Cyrillic script design guidance; orthographic variants for Bulgarian, Serbian, and other Slavic languages; historical letterform references

### Gerry Leonidas (University of Reading)

- **Works:** Academic papers on Greek type design; Type@Cooper lectures
- **Used for:** Greek script design principles; distinction between Greek and Latin letterform anatomy; historical Greek typography

These sources informed the Greek-specific and Cyrillic-specific variant tags (`.greek`, `.cyr`) in Section 6.7 and the script-aware element definitions.

## Comparison to CSDL

LSDL and CSDL are sibling specifications for different script families. This section documents their shared aspects and deliberate differences.

### Shared Aspects

| Feature          | Shared Design                                           |
|------------------|--------------------------------------------------------|
| Grid system      | 12x12 coordinate grid, origin at top-left              |
| Transform ops    | `sc` (scale), `sh` (shift), `sk` (skew) with same semantics |
| Closed registry  | Fixed element vocabulary; Level 1 parsers reject unknown elements |
| File format      | UTF-8 text, line-oriented, `#` comments               |
| Version header   | `@csdl 1.0` / `@lsdl 1.0` at line 1                   |

### Differences

| Aspect              | CSDL (CJK)                        | LSDL (Latin/Greek/Cyrillic)        |
|---------------------|-----------------------------------|-------------------------------------|
| **Composition**     | Grid partitioning (quadrants)     | Anchor-based attachment            |
| **Metrics**         | Uniform bounding box              | Named typographic zones            |
| **Elements**        | Stroke primitives (31 types)      | Anatomical parts (39 types)        |
| **Primary operator**| `PART` (quadrant placement)       | `STACK`, `LR`, `DIA` (attachment)  |
| **Stroke data**     | Explicit stroke sequences         | Implicit (path in @elem block)     |
| **Scripts**         | Han/CJK unified ideographs        | Latin, Greek, Cyrillic alphabets   |

### Rationale

The difference in composition model reflects fundamental script differences:

- **CJK:** Characters are spatially partitioned into regions (radicals occupy quadrants). CSDL's `PART` operator with quadrant coordinates is natural.
- **Alphabetic:** Characters are built by attaching anatomical parts at specific points. LSDL's anchor-based `STACK`/`LR`/`DIA` operators reflect how typographers conceptualize letterforms.

The metric system difference reflects script geometry:

- **CJK:** Uniform em-square; all characters fill the same bounding box
- **Alphabetic:** Variable vertical extent; lowercase x-height, ascenders, descenders, capitals, and diacritics occupy distinct zones

## Verification

To verify element and diacritic coverage against Unicode:

```bash
# Check Latin block coverage
python3 tools/check_coverage.py --script Latn

# Check combining mark mappings
python3 tools/check_coverage.py --block "Combining Diacritical Marks"

# Validate orthography tag assignments
python3 tools/validate_ortho.py
```

(Tools are placeholders for future implementation.)
