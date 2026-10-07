# Coupling-aware equivalence test for terminal alternations: protocol

Written 25 September 2026, before implementing or running this test. It follows
`COUPLED_CIPHER_FINDINGS_2026-09-25.md`. There, edge-conditioned homophones
differed *more* in following context than unrelated pairs did. The naive r/l
test (distinct following-initial distributions) therefore cannot separate
distinct units from coupled homophones.

Known beforehand:

* the R0/R1 slot-cipher results;
* the descriptive E3 numbers for 32 Voynich same-stem r/l pairs;
* the 16/48 naive r/l result.

No residual-context statistic of the kind below has been computed on any corpus.

## Hypotheses for a same-stem pair A = stem+x, B = stem+y

* **H_coupled (edge-conditioned homophones).** A and B encode one unit. The
  choice between them depends only on the adjacent boundary glyphs. Given those
  glyphs, the choice (T = A or B) is independent of the neighbouring *words*.
* **H_distinct.** A and B encode different units, so their neighbouring words
  differ even after conditioning on boundary glyphs.

## Statistic (fixed)

For each eligible occurrence of A or B, with neighbouring slots on the same line:

* **Z** = (last glyph of the previous token or `^` at line start, first glyph of
  the next token or `$` at line end). EVA glyph units.
* **X_left:** the previous token's identity if it is among the corpus's 30 most
  frequent types, otherwise `*`; `^` at line start.
* **X_right:** the same for the next token; `$` at line end.
* Occurrences next to an unreadable/uncertain token are excluded.

**S = I(T; X_left | Z) + I(T; X_right | Z)**, plug-in estimates weighted by
stratum.

The null permutes T within Z strata: 300 permutations, seed 20260925, with the
same permutation used for both terms. Reported quantities:

* the excess (S minus the null mean);
* z = excess / null SD;
* p = (1 + #{null ≥ S}) / 301.

**Naive comparison.** I(T; next initial glyph), with T permuted unconditionally,
300 permutations. This is the logic of the handoff's r/l test.

**Eligibility.** A and B each need ≥ 20 eligible occurrences. They must share
everything except the final EVA glyph unit.

* In Voynich the final glyphs must lie in {n, l, r}, the primary set.
  {n, l, r, m, y} is reported as a sensitivity.
* In the calibration cipher the terminals are the code-book terminals.

## Calibration cipher: shared-core slot cipher (known answers)

`slot_cipher` is extended so that pairs of syllable types share one core. The
syllable types are sorted by frequency and paired by adjacent rank.

* Each pair's 6 terminals {"", y, n, l, r, m} are split at random into two
  disjoint sets of 3.
* Unit a uses prefixes × its terminals, and unit b likewise. Each unit takes
  h = 10 of its 12 combinations, with s = 1.
* Any leftover unpaired type keeps its own core and all 6 terminals.
* The code book stays invertible, because terminal sets are disjoint within a
  shared core.

This yields both kinds of same-stem (same prefix + core) terminal pairs in one
corpus:

* **same-unit pairs:** coupled or free homophones;
* **distinct-unit pairs.**

Regimes: β = 2 (coupled, as R1) and β = 0 (free). Seeds 201, 202, 203. The ZL3b
layout template and the Alfonsi syllable stream are used as before.

Per seed and regime, at most 150 eligible pairs of each kind are scored, sampled
with a seeded RNG.

**Matched random reference** (used both in calibration and on Voynich). For each
scored pair (A, B), draw 20 reference pairs (X, Y):

* X and Y are distinct types from *different* stems (neither is A or B);
* each has a frequency within 0.8–1.25× of A's and B's frequency respectively;
* each has the same final glyph as A and B respectively, so the boundary-glyph
  coupling on their right side is comparable;
* the same eligibility rules apply.

Run the same statistic on each (X, Y). The pair's **reference percentile** is the
share of its reference excesses that are at or below its own excess. Random
pairs of frequent types are assumed to be mostly distinct units. In the
calibration cipher this can be checked directly.

## Calibration rules (must pass before Voynich is interpreted)

These apply to the coupled regime (β = 2), pooled over its three seeds.

* **C1, size.** Among same-unit pairs, at most 10% have p < 0.05 on S.
* **C2, power.** Among distinct-unit pairs, at least 50% have p < 0.05, and the
  ROC-AUC of the S-excess (distinct vs same-unit) is at least 0.80.
* **C3, reference logic.** The median reference percentile is ≤ 25 for same-unit
  pairs and ≥ 40 for distinct-unit pairs.

**Contrast, reported and not gated.** The naive test's significant fraction among
same-unit pairs at β = 2 and at β = 0 (it should flag coupled homophones
spuriously), and the S rules evaluated at β = 0.

If C1–C3 fail, the Voynich results are reported as uninterpretable, and the
failure is the finding.

## Voynich application

**Corpora.**

* ZL3b P0: the `06` parser, clean tokens, with uncertain tokens as gaps.
* **Stability:** Takahashi IT2a, parsed the same way.

**Pairs.** All eligible same-stem pairs whose final glyphs lie in {n, l, r}. For
each pair, report:

* S excess, z and p;
* naive p;
* the matched-reference percentile;
* the category, as follows:
  * **coupled-compatible:** p ≥ 0.05 **and** reference percentile ≤ 25;
  * **distinct-like:** p < 0.05 **and** reference percentile ≥ 50;
  * **undetermined:** otherwise.

**Aggregate (primary Voynich outcome).**

* The median reference percentile over all ZL pairs.
* A two-sided Wilcoxon signed-rank test of (percentile − 50).
* Counts per category.

**Interpretation, fixed now:**

* Median percentile ≤ 25 with Wilcoxon p < 0.05: r/l/n alternations as a class
  behave like edge-conditioned variants of one unit, once boundary glyphs are
  controlled. This is *compatible with* homophony. It does not prove it: shared
  plaintext is not observable, and the pairs could also be distinct but
  near-synonymous units.
* Median percentile ≥ 40, or Wilcoxon not significant with median ≥ 40: the
  alternations carry context information beyond the boundary glyphs, like random
  distinct pairs. This is evidence against pure edge-conditioned homophony for
  these pairs.
* Anything between: mixed or undetermined. Per-pair categories are reported
  without a class-level claim.
* Stability: category agreement between ZL and IT for shared pairs, reported.

**Sensitivities, reported only:**

* terminal set {n, l, r, m, y};
* Z extended to the first *two* glyph units of the next token, which checks
  whether coupling beyond one glyph drives residuals;
* X restricted to the left side only.

## Limits declared in advance

* **Coupling beyond Z.** Coupling that depends on more than the adjacent glyphs
  would produce residual context under H_coupled, reading as "distinct-like".
  The two-glyph Z sensitivity checks only one extension of this.
* **Weak context.** Voynich word order carries little information (earlier work
  found a whole-token order signal of about 0.06 bits/boundary). Power on real
  distinct units may be low. The matched random reference measures that power
  inside Voynich instead of assuming it.
* **Random pairs as a stand-in for distinct units.** This assumes random pairs
  are mostly distinct units. If Voynich had massive homophony, the reference
  would be conservative.
* **Scope.** No meanings are assigned, and nothing is merged in any
  representation on this basis alone.

## Outputs

`results/coupling_test_2026-09-25/`:

* `calibration.json`: per-pair statistics, rules C1–C3 and contrasts;
* `voynich.json`: ZL and IT per-pair results, aggregates and sensitivities;
* `manifest.json`.

Deviations will be recorded in `COUPLING_TEST_FINDINGS_2026-09-25.md`.
