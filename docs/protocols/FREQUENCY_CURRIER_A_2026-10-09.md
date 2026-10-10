# Stage 29: frequency decomposition and Currier A transfer

Declared before execution, 9 October 2026. Ledger rows 13, 14 and 18.
This is a descriptive manuscript diagnostic, not a cipher search or a family
rejection test. It addresses where page association resides before choosing a
context-dependent codebook. No meanings or plaintext assignments are fitted.

## Frozen design

Use ZL3b and IT2a already in data/. Select herbal pages using **ZL metadata**,
separately for Currier A and B. In transcription order take the first 16 distinct
folios eligible for 64 clean tokens in all four arms: ZL/IT × split/join doubtful
spaces. Retain one page per folio. Stop if either group has fewer than 16;
do not reduce the count after seeing association. IT is page matched, not glyph
aligned. All four arms take their own first 64 eligible tokens. Joining does not
cross hard gaps. Record exact loci, token spans, page classifications and hashes.

Measure each 16-page panel and its first/last eight-page halves. The halves are
disjoint replication panels, not historically untouched holdouts. No fitting is
performed, so there is no claim of predictive transfer. Do not pool A with B.
Also decompose the five frozen stage-28 manuscript panels and its 12 stored
source passage panels (three sources × four passages), without reselecting text.
These earlier panels have already been inspected; their analysis is prospective
but their data are not new.

## Estimator

For every panel assign word types to fixed **panel-wide count** bins: singleton,
2–4 occurrences, ≥5 occurrences. These are frequency groups, not semantic classes.
Counts and bin memberships are invariant to all token permutations below. No
rank cutoff, tie-breaking, vocabulary pooling or rare-token sentinel is used.

Compute each type's additive contribution to I(word;page | stratum), weighted by
stratum size / total tokens. Sum by frequency bin. Subtract the mean contribution
of 199 whole-token permutations within stratum, seed 2901. Strata are (a) section,
(b) section plus line-first, line-last and paragraph-first-line roles. Shuffle all
tokens together within each stratum, **not separately within bins**. Bin
contributions must sum to the ordinary all-type statistic (raw and corrected).
Report contributions in bits per original token, token mass per bin, null SD,
Monte Carlo SE, and the 2.5/97.5 percentiles of each permutation distribution.
These intervals describe the null, not uncertainty across manuscripts or folios.
No individual-bin significance claims or multiple-testing discoveries are made.

Singleton contributions in an equal-size one-section panel are exactly zero
after correction: their page identity is uninformative relative to the same
sparse null. Do not interpret that as singletons being non-topical. Role
conditioning can change that identity because page/role margins are unequal.

## Calibration and stopping

Before manuscript metrics: check additive equivalence against stage 27's scalar
estimator under identical seeds (tolerance 1e-10); invariance under bijective
word renaming; exact zero for an all-unique balanced panel. On 50 IID panels
(16 × 64, 128 equiprobable types), require absolute mean excess <0.01 bits.
On ten planted panels (16 × 64, each page uses 16 page-exclusive types four
times each), require mean excess >0.2 and all excess in the 2–4 bin. Fail closed
if any gate fails. Synthetic gates validate the estimator, not a cipher solver.

## Interpretation / next decision

If A and B both show positive section- and role-conditioned excess in both
halves and transcriptions, describe directional replication under this sampling;
otherwise report heterogeneity explicitly. Do not turn a sign rule into a
statistical acceptance threshold. Compare the distribution across count groups
to recipe/medical sources without identifying function or content words.

A surviving word-code model remains open, not promoted to decipherment or
comparative support. Frequency concentration can guide the next explicit model;
it cannot establish a lexical interpretation. No page-sticky generator is fitted
in this stage. Its next protocol must include R2, state costs, codeword structure,
and genuinely reserved evaluation under frozen settings.

Outputs: new results/frequency_currier_a_2026-10-09 with manifest, slots,
calibration, machine-readable evidence, readable report; tests and producer
registration; ledger update. Preserve all historical outputs.
