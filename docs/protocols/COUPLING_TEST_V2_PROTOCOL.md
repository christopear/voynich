# Coupling-aware terminal-alternation test, version 2: protocol

Written 25 September 2026, before implementing or running version 2. It is
intended as an overnight run on the user's machine (`overnight/`). It follows
`COUPLING_TEST_FINDINGS_2026-09-25.md`.

Version 1 had adequate size (2.8% false alarms on true coupled homophones) but no
power (13.8% of distinct pairs detected, AUC 0.61). The post-hoc diagnosis was
that neighbour-word identities are fragmented by homophony: the top 30 types
cover 16% of tokens in the cipher and 26% in Voynich.

Known beforehand: all version 1 results, per pair and aggregate, on the
calibration cipher and on Voynich ZL/IT.

## Changes from version 1 (everything else as in `COUPLING_TEST_PROTOCOL.md`)

### 1. Neighbour representation: distributional classes

For each corpus separately, the context classes are built as follows:

1. **Vocabulary:** types with frequency ≥ 2.
2. **Co-occurrence matrix:** each type's immediate left and right neighbours
   within a line, over the top 2,000 neighbour types, with separate left and
   right blocks and a catch-all column per side. Line edges count as `^`/`$`
   neighbours. Unreadable neighbours are skipped.
3. **Embedding:** positive PMI, truncated SVD to 50 dimensions (deterministic,
   `scipy.sparse.linalg.svds` with a fixed starting vector), then rows
   L2-normalized.
4. **Clustering:** k-means (scikit-learn, `n_init = 10`, `random_state` =
   20260925) into **k** classes.
5. **Neighbour value X:** the neighbour's class. Types with frequency < 2 get the
   class `rare`. Line edges keep `^`/`$`.

The arms are:

* **primary: k = 100**;
* sensitivities: k = 50 and k = 200;
* a **reference arm** repeating version 1's top-30 identity, run on the new
  seeds.

Validity is unchanged. X is a fixed function of the neighbour token, so under
H_coupled, T ⟂ X | Z still holds and the within-Z permutation null stays exact.
The class definition affects power only.

### 2. Pooled class-level test

Each pair keeps 300 within-Z permutation draws. Per draw j, compute
z_j = (null_j − null mean) / null SD. The pooled statistic over a set of pairs is
the mean observed z, and its null is the per-draw mean of the pairs' z_j. Pairs
are permuted independently. p = (1 + #{null ≥ observed}) / 301.

### 3. Calibration size and scope

* Seeds 301–310 (10 seeds), β ∈ {2, 0}.
* **All** eligible same-stem terminal pairs, with no cap.
* 20 matched random references per pair.
* The same shared-core slot cipher and ZL3b layout as version 1.

## Calibration rules (primary arm k = 100, β = 2, pooled over seeds)

Per-pair rules, as in version 1:

* **C1 (size):** ≤ 10% of same-unit pairs have p < 0.05.
* **C2 (power):** ≥ 50% of distinct-unit pairs have p < 0.05, and the ROC-AUC of
  the excess (distinct vs same) is ≥ 0.80.
* **C3 (reference logic):** median reference percentile ≤ 25 for same-unit pairs
  and ≥ 40 for distinct-unit pairs.

Pooled rules. Draw 200 random subsets of 30 pairs (the size of Voynich's pair
set) within each kind, pooled over seeds, with seed 20260925:

* **P1 (size):** ≤ 10% of same-unit subsets have pooled p < 0.05.
* **P2 (power):** ≥ 80% of distinct-unit subsets have pooled p < 0.05.

Per-pair Voynich categories are interpreted only if C1–C3 pass. The pooled
Voynich result is interpreted only if P1–P2 pass. The sensitivity arms and the
reference arm are reported, not gated.

## Voynich application (primary arm)

Corpora are ZL3b and IT2a, parsed with the `06` parser as before. Pairs are the
same-stem pairs with final glyph in {n, l, r}, each member with ≥ 20 eligible
occurrences.

**Per pair:** excess, z, p, reference percentile and category, using version 1's
category rules.

**Pooled:**

* the pooled p over all ZL pairs, and separately over IT pairs;
* **V (Voynich-internal power):** build 200 pseudo-sets. Each pseudo-set takes
  one of its matched random reference pairs for every Voynich pair, and gets the
  pooled test. V is the share of pseudo-sets with p < 0.05. This measures power
  against distinct-like pairs inside Voynich's own context background.

**Interpretation, fixed now** (only if P1–P2 pass):

* **Pooled p < 0.05 on ZL:** r/l/n alternations as a class carry residual context
  beyond boundary glyphs. This is evidence **against** pure edge-conditioned
  homophony for the class.
* **Pooled p ≥ 0.05 on ZL, V ≥ 0.80, and the same outcome on IT:** the class
  behaves like edge-conditioned variants. This is **compatible with** homophony
  (not proof).
* **Pooled p ≥ 0.05 with V < 0.80:** underpowered. No conclusion.
* **ZL and IT disagree:** transcription-sensitive. No conclusion.

## Reproducibility job (runs in the same overnight batch)

Rerun `13_equivalence_classes.py`, `15_coupled_cipher_transfer.py` and
`16_coupling_aware_test.py` on the user's machine with the locked environment.
Report which committed output files change. This is a cross-machine determinism
check only; no scientific rule depends on it.

## Development check (before handing over)

The code is exercised here in a `--smoke` mode only: seed 9001, which is not used
in the real run, with at most 5 pairs per kind, 3 references and 50 permutations.
This only checks that the code runs and writes the expected schema. Smoke outputs
are not examined for results and are not committed.

## Outputs

`results/coupling_test_v2_2026-09-25/`:

* `calibration.json`: per arm, regime and seed, per-pair rows and the rule
  evaluations;
* `voynich.json`;
* `manifest.json`: environment, CPU count, seeds, versions and hashes.

Logs go to `overnight/logs/`.
