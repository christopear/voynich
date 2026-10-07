# Boundary generalization and physical layout: prospective protocol

Written 24 September 2026, before fitting the new models. This extends the existing
boundary experiment; it does not treat proposed hidden cuts as known word boundaries.

## Questions and primary comparisons

1. Does the following initial improve prediction of a token's n/l/r terminal on
   held-out physical folios? Does that improvement persist when the exact stem is
   also absent from training? A stem is the entire token minus its final n/l/r.
2. Does this incremental information transfer from ordinary spaces to drawing
   interruptions and physical line boundaries? Does coordinate position improve
   terminal prediction after controlling for stem, following initial, hand,
   Currier language, section and ordinal position in the line?

Success means improved held-out probability forecasts, not decipherment or proof
of phonology. A negative result is informative. There is no claimed probability
that any model class is the manuscript's true generation mechanism.

## Corpus and exclusions

Use the existing ZL3b-n transcription (13 May 2025), paragraph text P0 only.
Preserve certain '.', uncertain ',', drawing '<->', line and paragraph gaps.
Uncertain readings, illegible tokens and extended glyph codes are excluded from
primary observations without joining their neighbours. Keep the first alternative
for alignment only, marking its token uncertain. Comments inside words must not
create artificial boundaries. Apostrophes and braces flag uncertain primary
tokens. Right-justified titles Pt do not become ordinary line continuations.
Cross-line observations require consecutive numbered P0 loci on the same page.
All physical sides/foldouts with the same f-number share a fold.

Use public voynichese coordinate boxes from the lrozanova/voynich-units archive,
pinned to commit 956a7c4fc39981f4d116fa3f4edfccce6d065571. This reuse is data
reuse, not a claim to introduce coordinate alignment. Exact token matching blocks
of length at least three are required, with adjacent coordinate entries and
compatible vertical positions for within-line pairs. Do not collapse distinct
glyph sequences to improve matches. Report coverage and alignment limitations.

## Splits and models

Assign sorted folio groups and sorted stems to five balanced, seeded shuffled
folds (seed 20260924). Save the assignments. Folio evaluation excludes both sides
of each test folio. Crossed evaluation trains on records outside BOTH the test
folio fold and the test stem fold, and evaluates their intersection (25 fits per
model). This is stronger than holding out a token while reusing its page.

Fit multinomial L2 logistic regression, C=1, fixed features, no tuning on outcomes.
Structural features: stem glyph length, first/last one and two glyphs, glyph
counts. Nuisance features: hand, Currier language, section, relative ordinal
position and paragraph start. Context adds the next initial and its interactions
with the stem suffix and hand. Folio-only models additionally have exact stem
identity and stem-by-initial interactions; crossed models never have stem IDs.
The terminal itself must never enter the predictors. Categories are fitted on
training rows only. Smoothed training terminal frequencies are a reference.

Primary measure: paired reduction in held-out negative log probability, in bits
per terminal. Also accuracy difference, Brier score, sample size and coverage.
Use 2,000 percentile bootstraps of paired differences clustered separately by
physical folio and exact stem. These are conditional-on-fitted-model intervals,
not refitted-model or independent-token confidence intervals. Do not present the
separate intervals as a full two-way cluster bootstrap. Show fold and subgroup
effects. Context-scrambling within test folio is a diagnostic, not a definitive
conditional randomization test.

## Hidden-cut extension

Generate candidates in held-out folios using training-folio token frequencies
only. A joined token has at least six glyphs, training frequency <=2; each side
has at least two glyphs; the left ends n/l/r. Require pooled frequency of all
three left-terminal variants >=5 and exact right frequency >=5. Rank cuts by
pooled-left-frequency times right-frequency, not exact left-terminal frequency.
Keep one candidate per joined type per test fold. Report type/family dependence.
Train terminal predictors on visible ordinary spaces only. Compare with/without
following initial on precisely the same selected candidates. This evaluates
consistency of hypotheses, not accuracy of segmentation: true boundaries are
unknown. Selection still conditions on n/l/r and a known right side.

## Layout extension

Apply ordinary-space trained models, with identical folds, to drawing gaps,
uncertain spaces, within-paragraph line breaks and paragraph breaks. Compare
context gain across these gap classes, acknowledging differing stem support and
nonrandom placement of illustrations. Inspect an additional model fitted to all
gap classes with boundary-specific features as a sensitivity analysis.

For coordinate-matched ordinary spaces and drawing interruptions, compare the
full context model with and without the current token's normalized horizontal
START position. Include ordinal position in both. Normalize by page-wide box
extent; use ten fixed bins plus a linear term. Never use the token's own right
edge, width or gap after it as a predictor of its terminal: those are mechanically
affected by writing that terminal. Start position is still observational and not
a measurement of intended available writing space. Report held-out effects and
by-gap effects; do not interpret association as causal geometry dependence.

## Scope and interpretation

No language identification, semantic translation or meaningfulness inference
follows from predictive boundary structure. Compare the contribution with
Currier's known line/boundary effects, Steckley's drawing-interruption work and
Rozanova/Temerev's 2026 separator/coordinate analysis. Novelty sought here is the
joint generalization test, selection correction and conditional predictive
layout analysis, not rediscovery of those effects. Record deviations explicitly.
