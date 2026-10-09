# Word-code alternatives, prospective stage 28 — 9 October 2026

Ledger row 13. Motivated by stage 27 and Claude's review, not an independent
initial hypothesis. Test whether fixed disjoint alternative codewords per source
word can jointly approach Voynich's token fingerprints. This is a forward-model
screen, not blind key search or decipherment. No historically attested particular
codebook is claimed; opaque labels test equality patterns, not glyph morphology.

## Model and invariant

One normalized source word -> one apparent ciphertext token. Each word owns
one, two or three disjoint codewords. Choices are IID, page/layout independent,
with the same probabilities for every word. Grid:
(1), (.9,.1), (.75,.25), (.5,.5), (.8,.1,.1), (.6,.2,.2), (1/3,1/3,1/3).
All codewords decode uniquely. No merging, inflection reduction, nulls, state,
selective content dictionary or altered spacing. Code identifiers are opaque
permuted integers; codeword-internal strings carry no linguistic features.

Since U=f(C) and C independent of page P given U, I(C;P)=I(U;P) in the
population (data processing in both directions). Finite-sample plug-in MI may
rise after splitting types; permutation-excess MI may fall as repeats become
sparse. Neither is a universal plaintext-information ceiling.

## Sources, partition and budget

Use the frozen stage-27 prepared Celsus, Pliny and Italian culinary recipe
chapters. Keep its first floor(N/5) eligible chapters excluded. Split the
remaining eligible chapters in file order into two halves. Draw 16 distinct
chapters from the first half for development seeds 7,19; from the second half
for validation seeds 31,43. No chapter crosses that partition. Within each
chapter sample a contiguous 64-WORD span, once per panel, shared by all grid
settings. Literary controls are not extended this round.

For each of 3 sources × 4 passage panels × 7 settings, encode with seeds
101–106: 504 ciphertext panels. Every panel must pass exact known-key round-trip
validation. Seeds are Monte Carlo sensitivity, not independent texts. Each
panel has 16 pages × 64 tokens. Development uses the stage-27 split-arm layout;
validation uses the additional-page layout below. Randomness is explicitly
fixed by (passage seed, encoding seed), shared across settings where possible.

## Actual manuscript and replication

Primary development target: existing ZL3b split arm on 16 folios. Sensitivities:
its existing joined-space arm and IT2a first 64 clean split tokens on those exact
pages (page-matched, not glyph/token-aligned, same manuscript).
Additional-page target: first eight eligible remaining herbal folios and first
eight starred-text (I=S) folios in ZL file order, excluding all original folios;
>=64 clean tokens, one page per folio. These are additional pages, not historically
unseen data. Biological pages are insufficient for another disjoint eight-folio
panel, so the section change is explicit. Repeat IT2a on those same pages.
Condition on the actual section and original line/paragraph roles. No reflow.
Do not interpret a section-specific difference as a source-language verdict.

## Joint comparison, calibration and stopping

Measure all-type within-section and role-conditioned permutation-excess MI
(199 permutations, as stage 27), type/token ratio, top-ten share, hapax-type
share and adjacency repetition. Primary four-vector: TTR, top-ten share,
within-section excess MI, role-conditioned excess MI. Define descriptive
neighbourhood scales (.05, .04, .05, .05), fixed before execution. A panel is
inside the neighbourhood if the maximum absolute scaled difference is <=1.
These are screening tolerances, NOT calibrated rejection thresholds or claims
of statistical compatibility. Report all four signed residuals and all grid
settings; no cherry-picking different settings for different statistics.

Calibration before manuscript scoring: use the first development recipe panel,
all seven configurations and independent target encoding seeds 901,902. Compare
each synthetic target to coordinate-wise median fingerprints from seeds101–106
for every configuration; select by minimum max-scaled distance with grid-order
ties. Report 14 distances and selected parameter settings; exact parameter
recovery is not required because parameters may be non-identifiable. Require
>=12/14 targets inside the declared neighbourhood or stop before interpreting
manuscript fits. Also test exact decoder recovery and the population MI identity
on a finite enumerated distribution. No calibration-based tolerance adjustment.

On original ZL development target, select one configuration PER SOURCE by
minimizing the max-scaled distance to median fingerprints over 2 passage panels
×6 encoding draws (12 replicates). Freeze that configuration. Evaluate unchanged
on the 12 validation draws and additional-page target; give joint hit counts,
per-panel values and Monte Carlo dispersion. No parameter reselection on IT,
joined spaces or validation target. Report development/reference dispersion,
not an IID confidence interval from treating seeds as independent manuscripts.

If no configuration is in the joint neighbourhood, label "no joint match in
this bounded screen"; do not exclude word codes. If a setting transfers, call
it a candidate for further fingerprints, not decipherment. Glyph shape, coding
capacity per glyph, uncertain source language, scribal abbreviation, content
lexicons and independent readings remain outside this stage. Keep all prior
results unchanged and commit this protocol before execution.
