# Coupling-aware terminal-alternation test, version 3 (cross-fitted): protocol

Written 26 September 2026, before implementing or running version 3. It is to be
run on the user's machine (`overnight/run_v3.sh`). It follows
`COUPLING_TEST_V2_FINDINGS_2026-09-26.md`.

Version 2 raised power (AUC 0.85), but its neighbour classes were learned from
data that contained the tested pairs. That leaked T into X and biased z upward
even with no coupling, which made the pooled test anti-conservative.

Known beforehand: all version 1 and version 2 results, per pair and aggregate,
on the calibration cipher and on Voynich ZL/IT, including the Voynich pairs that
looked distinct-like or coupled-compatible under version 2.

## Changes from version 2 (everything else as in `COUPLING_TEST_V2_PROTOCOL.md`)

### 1. Cross-fitted neighbour classes (the fix)

Pages are assigned to 5 folds: sorted page identifiers, shuffled with seed
20260925, fold = rank mod 5. The same assignment is used for every corpus that
shares the ZL3b page layout, which covers the calibration cipher and ZL3b. IT2a
uses its own pages, with the same rule.

For each fold f:

* neighbour classes (PPMI → SVD → k-means, as in version 2) are learned **only**
  from lines on pages outside f;
* every occurrence of a tested type on a page in f gets
  X = class(neighbour) from that fold's model;
* neighbours unseen in the training folds get `rare`; `^` and `$` are kept.

Under H_coupled, the choices T within fold f are independent of the other folds'
text, so X ⟂ T | Z holds exactly and the within-Z permutation null is valid
again. Z, T, the statistic, the permutations (300), eligibility (≥ 20 occurrences
per member) and the matched references (20 per pair) are unchanged.

### 2. Arms

* **Primary: k = 100 cross-fitted.**
* Sensitivity: k = 50 cross-fitted.
* Reference: top-30 identity. This needs no fitting and is exact already.

k = 200 is dropped because it added nothing in version 2.

### 3. Pooled calibration subsets match Voynich's structure

None of Voynich's 34 pairs share a member. Pooled calibration subsets of 30
pairs are therefore drawn **member-disjoint**: no type appears in two pairs of a
subset, and each subset is drawn within one seed. 200 subsets per kind.

## Calibration rules (primary arm, β = 2, pooled over seeds 301–310)

These are the same thresholds as version 2 (C1–C3, P1, P2), with one gate added.

* **C1:** ≤ 10% of same-unit pairs have p < 0.05.
* **C2:** ≥ 50% of distinct-unit pairs have p < 0.05, and AUC ≥ 0.80.
* **C3:** median reference percentile ≤ 25 for same-unit pairs and ≥ 40 for
  distinct-unit pairs.
* **P1:** ≤ 10% of member-disjoint same-unit subsets have pooled p < 0.05.
* **P2:** ≥ 80% of member-disjoint distinct-unit subsets have pooled p < 0.05.
* **B0 (new, leakage check):** mean z of same-unit pairs lies within ±0.08, in
  **both** regimes (β = 2 and β = 0). That is about 2.5 standard errors for about
  1,000 pairs, and it directly tests the version 2 failure.

Per-pair Voynich categories are interpreted only if C1, C2, C3 and B0 pass. The
pooled Voynich result is interpreted only if P1, P2 and B0 pass.

## Voynich application and interpretation

Unchanged from version 2, with the primary arm now cross-fitted.

* **Corpora:** ZL3b and IT2a.
* **Pairs:** same-stem pairs with final glyph in {n, l, r}.
* **Pooled test:** pooled p and V (Voynich-internal power against matched random
  pairs).

**Interpretation** (when P1, P2 and B0 pass):

* **ZL pooled p < 0.05, and IT agrees:** the class carries residual context
  beyond boundary glyphs. This is evidence against pure edge-conditioned
  homophony.
* **ZL pooled p ≥ 0.05, V ≥ 0.80, and IT agrees:** compatible with
  edge-conditioned variants of one unit (not proof).
* **V < 0.80:** underpowered.
* **ZL and IT disagree:** transcription-sensitive, no conclusion.

This is the final attempt at this question with context statistics. If the
calibration fails again, the question is recorded as not decidable by this
method and no version 4 follows.

## Development check (in the cloud container, before handover)

As before: unit tests, plus a `--smoke` run (seed 9101, not used in the real run;
at most 5 pairs per kind; 3 references; 50 permutations). Only completion and
output schema are checked. Smoke outputs are not examined for results and are
not committed.

## Outputs

`results/coupling_test_v3_2026-09-26/`, containing `calibration.json`,
`voynich.json` and `manifest.json`. Logs go to `overnight/logs_v3/`.
