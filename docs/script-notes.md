# Greek and Cyrillic Script Notes

This document provides guidance for authoring LSDL definitions for Greek and
Cyrillic scripts, covering element variants, regional orthographies, diacritics,
and edge cases.

---

## Greek Script (Grek)

### Element Variants

Greek characters share structural elements with Latin but require script-specific
variants to capture their distinct proportions and curvature.

| Variant          | Description                                           | Used By          |
|------------------|-------------------------------------------------------|------------------|
| `bowl.greek`     | Greek bowl with different curve tension than Latin    | omicron, theta   |
| `shoulder.greek` | Greek shoulder form                                   | eta, iota, kappa, nu |
| `descender.greek`| Greek descender with different length/angle           | rho, chi, psi    |
| `stem.greek`     | Greek stem proportions                                | iota, tau        |
| `hook.greek`     | Greek hook forms                                      | gamma, xi        |
| `loop.greek`     | Greek loop (distinct from Latin g)                    | zeta, xi         |

Example definitions:

```lsdl
@elem bowl.greek
zone: x-height
# Greek bowl has rounder proportions than Latin
path: p1 p2 p3
p1 = [6,4]
p2 = C([12,4] [12,8] [6,8])
close: true
width: 1
anchors: attach=[6,6] mark-above=[6,3] mark-below=[6,9]
@end

ο  GREEK-SMALL-OMICRON = bowl.greek script:Grek
```

### Special Characters

#### Final Sigma

Greek has a word-final form of sigma. Use `@case` with the `final:` parameter:

```lsdl
Σ  GREEK-CAPITAL-SIGMA  = ... script:Grek
σ  GREEK-SMALL-SIGMA    = ... script:Grek
ς  GREEK-SMALL-FINAL-SIGMA = ... script:Grek

@case Σ σ final:ς
```

The `.final` variant tag documents intent:

```lsdl
@elem sigma.final
zone: x-height
# Curving tail instead of symmetric loop
...
@end
```

#### Beta (Double-Bowl)

Beta stacks two bowls vertically:

```lsdl
β  GREEK-SMALL-BETA = STACK(ascender.curved, bowl.r.upper, bowl.r.lower) script:Grek
```

This pattern applies to other characters with stacked curves (e.g., xi, psi).

### Polytonic Greek Diacritics

Polytonic Greek uses an extended diacritic system beyond modern monotonic Greek.
These combine using DIA and DIA2.

#### Breathing Marks

| Mark              | Zone             | Unicode   | Description            |
|-------------------|------------------|-----------|------------------------|
| `smooth-breathing`| diacritic-above  | U+0313    | Smooth breathing (psili) |
| `rough-breathing` | diacritic-above  | U+0314    | Rough breathing (dasia) |

```lsdl
@elem smooth-breathing
zone: diacritic-above
# Comma-like form curving right
path: p1 p2
p1 = C([5,1] [7,0])
p2 = [6,1]
width: 1
anchors: attach=[6,2]
@end

@elem rough-breathing
zone: diacritic-above
# Comma-like form curving left (reversed smooth)
path: p1 p2
p1 = C([7,1] [5,0])
p2 = [6,1]
width: 1
anchors: attach=[6,2]
@end
```

#### Accents

Polytonic Greek uses three accents that stack with breathing marks:

| Mark         | Zone             | Unicode | Description              |
|--------------|------------------|---------|--------------------------|
| `oxia`       | diacritic-above  | U+0301  | Acute accent (identical to Latin) |
| `varia`      | diacritic-above  | U+0300  | Grave accent (identical to Latin) |
| `perispomeni`| diacritic-above  | U+0342  | Circumflex (tilde-like)  |

The `perispomeni` differs from Latin circumflex:

```lsdl
@elem perispomeni
zone: diacritic-above
# Tilde-shaped Greek circumflex
path: p1 p2 p3
p1 = [4,1]
p2 = C([6,0] [6,0])
p3 = [8,1]
width: 1
anchors: attach=[6,2]
@end
```

#### Iota Subscript

The iota subscript (ypogegrammeni) attaches below vowels:

```lsdl
@elem iota-subscript
zone: diacritic-below
# Small iota shape below baseline
path: p1 p2
p1 = [6,9]
p2 = [6,11]
width: 1
anchors: attach=[6,8]
@end

ᾳ  GREEK-SMALL-ALPHA-YPOGEGRAMMENI = DIA(α, iota-subscript) script:Grek
```

#### Combined Polytonic Marks

Polytonic often requires multiple diacritics. Use DIA2 for two marks, or nest
DIA for three or more:

```lsdl
# Alpha with smooth breathing and acute
ἄ  GREEK-SMALL-ALPHA-PSILI-OXIA = DIA2(α, smooth-breathing, acute) script:Grek

# Alpha with smooth breathing, acute, and iota subscript
ᾄ  GREEK-SMALL-ALPHA-PSILI-OXIA-YPOGEGRAMMENI = DIA(DIA2(α, smooth-breathing, acute), iota-subscript) script:Grek
```

### Historical and Extended Forms

Greek Extended (U+1F00-U+1FFF) contains precomposed polytonic characters. These
can be defined structurally:

```lsdl
# Lowercase vowels with all breathing/accent combinations
ἀ  GREEK-SMALL-ALPHA-PSILI = DIA(α, smooth-breathing) script:Grek
ἁ  GREEK-SMALL-ALPHA-DASIA = DIA(α, rough-breathing) script:Grek
ἂ  GREEK-SMALL-ALPHA-PSILI-VARIA = DIA2(α, smooth-breathing, grave) script:Grek
ἃ  GREEK-SMALL-ALPHA-DASIA-VARIA = DIA2(α, rough-breathing, grave) script:Grek
ἄ  GREEK-SMALL-ALPHA-PSILI-OXIA = DIA2(α, smooth-breathing, acute) script:Grek
ἅ  GREEK-SMALL-ALPHA-DASIA-OXIA = DIA2(α, rough-breathing, acute) script:Grek
ἆ  GREEK-SMALL-ALPHA-PSILI-PERISPOMENI = DIA2(α, smooth-breathing, perispomeni) script:Grek
ἇ  GREEK-SMALL-ALPHA-DASIA-PERISPOMENI = DIA2(α, rough-breathing, perispomeni) script:Grek
```

---

## Cyrillic Script (Cyrl)

### Element Variants

Cyrillic shares many structural elements with Latin but requires script-specific
variants:

| Variant      | Description                                    | Used By           |
|--------------|------------------------------------------------|-------------------|
| `bowl.cyr`   | Cyrillic bowl proportions                      | О, Ф, Ю           |
| `hook.cyr`   | Cyrillic hook/tail (Ц, Щ descending tails)     | Ц, Щ, Щ           |
| `stem.cyr`   | Cyrillic stem (may differ in width/position)   | general           |
| `soft-sign`  | The ь shape (palatalization mark)              | ь, ъ              |
| `shoulder.cyr`| Cyrillic shoulder form                        | Ч, Ы              |

The Cyrillic hook differs from Latin hooks:

```lsdl
@elem hook.cyr
zone: descender
# Short descending tail at baseline right
path: p1 p2 p3
p1 = [10,8]
p2 = [10,10]
p3 = C([11,10] [11,9])
width: 1
anchors: attach=[10,8] top=[10,8]
@end

Ц  CYRILLIC-CAPITAL-TSE = FRAME(stem.l, bar.bot, stem.r, hook.cyr) script:Cyrl
```

### Regional Variants with ortho: Tags

Cyrillic has significant regional variation. Use `ortho:` tags to distinguish
national typographic traditions.

#### Russian (Rus)

Russian uses standard Cyrillic forms:

```lsdl
б  CYRILLIC-SMALL-BE = STACK(hook.top, bowl.cyr) script:Cyrl ortho:Rus
г  CYRILLIC-SMALL-GHE = FRAME(stem, bar.top) script:Cyrl ortho:Rus
д  CYRILLIC-SMALL-DE = FRAME(stem.l.angled, bar.top, stem.r.angled) script:Cyrl ortho:Rus
п  CYRILLIC-SMALL-PE = FRAME(stem.l, bar.top, stem.r) script:Cyrl ortho:Rus
т  CYRILLIC-SMALL-TE = FRAME(stem, bar.top) script:Cyrl ortho:Rus
```

#### Bulgarian (Bul)

Bulgarian italic forms differ from Russian, particularly for lowercase. Note
that LSDL describes upright forms; italic is applied via `@style`. The different
letterforms are documented for renderers that select structural variants based
on language:

```lsdl
# Bulgarian often has distinct upright forms too
в  CYRILLIC-SMALL-VE = ... script:Cyrl ortho:Bul
г  CYRILLIC-SMALL-GHE = ... script:Cyrl ortho:Bul  # May differ from Russian
д  CYRILLIC-SMALL-DE = ... script:Cyrl ortho:Bul  # Different from Russian
ж  CYRILLIC-SMALL-ZHE = ... script:Cyrl ortho:Bul
к  CYRILLIC-SMALL-KA = ... script:Cyrl ortho:Bul
```

#### Serbian (Srp)

Serbian Cyrillic has distinctive italic forms for several letters. Define
separate character entries:

```lsdl
# Serbian б (italic form has curved top unlike Russian)
б  CYRILLIC-SMALL-BE = STACK(ascender.curved, bowl.cyr) script:Cyrl ortho:Srp

# Serbian г (cursive-like form in italic)
г  CYRILLIC-SMALL-GHE = ... script:Cyrl ortho:Srp

# Serbian д (different from Russian д in italic)
д  CYRILLIC-SMALL-DE = ... script:Cyrl ortho:Srp

# Serbian п (italic differs from Russian)
п  CYRILLIC-SMALL-PE = ... script:Cyrl ortho:Srp

# Serbian т (italic has descender-like form)
т  CYRILLIC-SMALL-TE = ... script:Cyrl ortho:Srp
```

When duplicate characters exist (same literal character with different `ortho:`
tags), the renderer selects based on orthographic context. If no context is
available, the last definition in file order applies.

#### Ukrainian (Ukr)

Ukrainian has four letters not in Russian:

```lsdl
# Ukrainian Ghe with upturn (not in Russian)
ґ  CYRILLIC-SMALL-GHE-UPTURN = FRAME(stem, bar.top, hook.top) script:Cyrl ortho:Ukr
Ґ  CYRILLIC-CAPITAL-GHE-UPTURN = FRAME(stem, bar.top, hook.top) script:Cyrl ortho:Ukr

# Ukrainian Ye (Latin E shape)
є  CYRILLIC-SMALL-UKRAINIAN-IE = ... script:Cyrl ortho:Ukr
Є  CYRILLIC-CAPITAL-UKRAINIAN-IE = ... script:Cyrl ortho:Ukr

# Ukrainian/Belarusian I (Latin I shape)
і  CYRILLIC-SMALL-BYELORUSSIAN-UKRAINIAN-I = stem script:Cyrl ortho:Ukr
І  CYRILLIC-CAPITAL-BYELORUSSIAN-UKRAINIAN-I = stem script:Cyrl ortho:Ukr

# Ukrainian Yi (I with diaeresis)
ї  CYRILLIC-SMALL-YI = DIA(і, diaeresis) script:Cyrl ortho:Ukr
Ї  CYRILLIC-CAPITAL-YI = DIA(І, diaeresis) script:Cyrl ortho:Ukr
```

### Special Elements

#### Soft Sign and Hard Sign

The soft sign (ь) and hard sign (ъ) share structure:

```lsdl
@elem soft-sign
zone: x-height
# Vertical stem with rightward bowl at bottom
path: p1 p2 p3
p1 = [4,4]
p2 = [4,8]
p3 = C([4,8] [10,8] [10,6])
width: 1
anchors: top=[4,4] base=[4,8] mid=[6,6] mark-above=[6,3]
@end

ь  CYRILLIC-SMALL-SOFT-SIGN = soft-sign script:Cyrl
ъ  CYRILLIC-SMALL-HARD-SIGN = FRAME(bar.top, soft-sign) script:Cyrl
```

#### Iotified Vowels

Several Cyrillic vowels have iotified forms (with leading Й sound):

```lsdl
# Iotified A (Я)
Я  CYRILLIC-CAPITAL-YA = ... script:Cyrl  # R-like form reversed
я  CYRILLIC-SMALL-YA = ... script:Cyrl

# Iotified E (Е)
# Standard Е/е already serves this function

# Iotified U (Ю)
Ю  CYRILLIC-CAPITAL-YU = LR(stem, bowl.cyr) script:Cyrl
ю  CYRILLIC-SMALL-YU = LR(stem, bowl.cyr) script:Cyrl

# Ukrainian iotified E (Є)
# See Ukrainian section above
```

---

## Shared Concerns

### Script Mixing and Homoglyphs

Many characters appear visually identical across scripts but have different
Unicode code points. LSDL uses script-qualified aliases to disambiguate:

```lsdl
@alias Latn:A = A    # U+0041 Latin Capital A
@alias Grek:A = Α    # U+0391 Greek Capital Alpha
@alias Cyrl:A = А    # U+0410 Cyrillic Capital A

@alias Latn:H = H    # U+0048 Latin Capital H
@alias Grek:H = Η    # U+0397 Greek Capital Eta
@alias Cyrl:H = Н    # U+041D Cyrillic Capital En

@alias Latn:O = O    # U+004F Latin Capital O
@alias Grek:O = Ο    # U+039F Greek Capital Omicron
@alias Cyrl:O = О    # U+041E Cyrillic Capital O
```

These homoglyphs may share the same element definition:

```lsdl
# All three O characters can use the same structural definition
O  LATIN-CAPITAL-O = bowl.full script:Latn
Ο  GREEK-CAPITAL-OMICRON = bowl.full script:Grek
О  CYRILLIC-CAPITAL-O = bowl.full script:Cyrl
```

### Case Mapping Edge Cases

#### Greek Special Cases

Greek has several case mapping edge cases:

```lsdl
# Sigma with final form
@case Σ σ final:ς

# Iota with dialytika becomes two characters when uppercased
# (ϊ -> Ϊ is straightforward, but accented forms are complex)
@case Ϊ ϊ
```

#### Cyrillic Titlecase

Some Cyrillic digraphs have titlecase forms distinct from uppercase:

```lsdl
# Lje, Nje, etc. in Serbian have titlecase = first letter capital
# LSDL does not have a dedicated titlecase mechanism; these are
# application-level concerns
```

### Mathematical and Technical Usage

Greek letters are heavily used in mathematics. When defining Greek characters,
consider their dual role:

```lsdl
# Greek letters used as mathematical symbols
π  GREEK-SMALL-PI = ... script:Grek
Σ  GREEK-CAPITAL-SIGMA = ... script:Grek  # Also summation
Δ  GREEK-CAPITAL-DELTA = ... script:Grek  # Also change/difference
Ω  GREEK-CAPITAL-OMEGA = ... script:Grek  # Also ohm symbol

# Note: Unicode has separate code points for some mathematical uses:
# U+2126 Ω OHM SIGN (canonically equivalent to U+03A9)
# U+2206 ∆ INCREMENT (distinct from U+0394)
```

Cyrillic letters appear less frequently in mathematics but occur in physics
and engineering notation in Slavic-language contexts.

---

## Summary

| Concern                | Greek                                      | Cyrillic                                |
|------------------------|--------------------------------------------|-----------------------------------------|
| **Element variants**   | `.greek` suffix for bowls, shoulders, etc. | `.cyr` suffix for hooks, bowls, etc.    |
| **Special forms**      | Final sigma (ς)                            | Soft sign (ь), hard sign (ъ)            |
| **Diacritics**         | Polytonic system (breathing, accents, iota subscript) | Limited (Ukrainian ї, ё)   |
| **Regional variants**  | Monotonic vs. polytonic                    | Russian, Bulgarian, Serbian, Ukrainian  |
| **Homoglyphs**         | Many shared with Latin                     | Many shared with Latin and Greek        |
| **Case mapping**       | Final sigma rule                           | Standard with some digraph complications|

When authoring LSDL for Greek or Cyrillic:

1. Always include `script:Grek` or `script:Cyrl`
2. Use `ortho:` tags for language-specific variants
3. Define script-specific element variants as needed
4. Handle homoglyphs via script-qualified aliases
5. Use DIA/DIA2 for diacritic combinations
