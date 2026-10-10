# Voynich: plaintext source sensitivity under the frozen context-choice mechanism

Stage 34, 9 October 2026. [Frozen protocol](../../docs/protocols/SOURCE_SENSITIVITY_2026-10-09.md),
committed at 75e54f8 before execution. Evidence label: **search found no fit in
a bounded forward-model grid**, for every source. No plaintext was recovered and
no key was searched for.

**In one paragraph.** With stage 33's mechanism frozen, two Latin medical
sources replaced the Italian recipes. Neither fits. They fit worse, for a reason
that is now explicit. Under a whole-word code, the cipher inherits the
plaintext's vocabulary richness, and inflected Latin prose has far more distinct
words per 512 tokens than Voynich (cipher TTR 0.76–0.82 against 0.61–0.64).
Its larger vocabulary also pushes codewords long (5.2–5.3 glyphs against
4.3–4.5). Celsus does bring more page association than recipes and Pliny less,
as predicted, and coupling is unchanged across sources, also as predicted. By
the preregistered rule this mechanism line stops here.

## Results by source (development medians; selected rule per source)

Residuals are in scale units against B_ZL_split_early: TTR, top-ten, section,
role, count≥5, length, glyph entropy, coupling.

| Source | Types | Selected rule | Dev max | Residuals of selected rule | Reserved B hits | Best reserved B |
| --- | --- | --- | --- | --- | --- | --- |
| celsus | 14,669 | edge_refresh | 2.83 | **+2.8**, −1.8, +0.7, −0.5, −0.5, +1.7, +0.5, −2.4 | 0/12 | 2.90 |
| pliny | 16,026 | edge_refresh | 3.85 | **+3.9**, −1.9, −0.2, −0.7, −0.7, +1.8, +0.9, −2.2 | 0/12 | 3.44 |
| cucina (= stage 33) | 1,484 | edge_max | 1.16 | −1.1, +0.5, −1.2, −1.2, −1.1, +0.1, −0.6, −0.7 | 0/12 | 2.33 |
| R2 (all sources) | — | level 2, no coupling | 2.10 | glyph entropy +2.1, coupling −2.1 | 0/6 | 4.67 |

No rule hits any B target for any source, selected or not (descriptive
all-rule table in `evidence.json`). The only within-neighbourhood draws are
cucina on Currier A: iid 4/12 (stage 32's result, reproduced) and edge 3/12.
Both use the one recipe passage; Latin sources give none. That A result remains
a single-source, single-panel observation. It is not replicated here and is not
a fit.

Calibration: celsus 15/16, pliny 16/16, cucina 16/16 (gate 12). Discrimination
is 100% for all three.

## Predictions

| Prediction | Outcome |
| --- | --- |
| 1. Celsus raises and Pliny lowers page association, tracking plaintext | Holds. IID cipher section excess: celsus 0.072, cucina 0.053, pliny 0.039. Plaintext on the same rows: celsus 0.066–0.148, cucina 0.078–0.100, pliny 0.032–0.070 |
| 2. Latin raises TTR | Holds, strongly: 0.76–0.82 vs cucina 0.56 and Voynich 0.61–0.64 |
| 3. edge_max coupling similar across sources | Holds: 0.091 / 0.097 / 0.085 |

## Why the Latin sources fail (post hoc decomposition, labelled)

For a disjoint two-variant code, the cipher's TTR is roughly the plaintext's
plus the extra types the variants create:

| Source | Plaintext TTR (four passages) | IID cipher TTR (median) | Mean letters per word |
| --- | --- | --- | --- |
| celsus | 0.66–0.73 | 0.763 | 5.57 |
| pliny | 0.74–0.82 | 0.822 | 5.95 |
| cucina | 0.45–0.49 | 0.579 | 4.30 |
| Voynich B (target) | — | 0.61–0.64 | — |

Under this construction, Voynich's vocabulary richness would need a plaintext
with TTR near 0.5 per 512 tokens. That is between these Italian recipes and
these Latin medical texts. Inflected Latin, written out and coded whole word by
whole word, carries too many distinct forms. This is a constraint on
**whole-word codes of Latin**. It does not exclude Latin under codes that
separate stems from endings, abbreviate, or drop inflection. Those are different
representations.

## What this changes

1. **The whole-word code line has reached its useful end on these measures.**
   Across stages 31–34, shape, length and frequency/length structure are solved,
   and coupling is partly solved by context choice. Page association and
   vocabulary richness now depend mainly on which plaintext is chosen, and these
   sources have not supplied them jointly.
2. **Latin, coded word by word, does not reproduce Voynich's vocabulary size;
   these Italian recipes come closer.** Two Latin sources and one Italian source
   cannot identify a language or genre. Choosing among three sources after the
   fact is itself selection.
3. **Next directions are different representations**, not more parameters here:
   * a stem-plus-ending (morphological) code, which would let Latin inflection
     map onto Voynich's prefix/suffix structure while holding the type count
     down;
   * the label/crib route (semantic constraints from drawings), still gated on
     independent alignment.

No decipherment, readings, family rejection or comparative support is claimed.
Each source contributes two development and two validation passages; seeds are
not independent sources.

## Verification

`python -m voynich.laboratory.source_verify` checks hashes. It rebuilds all 18
codebooks and replays all 504 records (288 cipher, 216 R2 copies) with
round-trips. It confirms cucina and R2 panels are token-identical to stage 33,
and recomputes calibration, plaintext association, selection, comparisons and
the all-rule table for every source. Deviations: none.
