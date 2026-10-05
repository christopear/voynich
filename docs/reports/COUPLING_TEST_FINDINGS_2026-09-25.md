# Coupling-aware test for terminal alternations: findings

25 September 2026.

* **Protocol:** `COUPLING_TEST_PROTOCOL.md`, committed before implementation.
* **Code:** `code/coupling_test.py`, `code/16_coupling_aware_test.py`, and the
  shared-core code book in `code/slot_cipher.py`.
* **Results:** `results/coupling_test_2026-09-25/`.

## Main finding

**The test does not raise false alarms, but it lacks the power to detect
genuinely distinct units. Under the pre-set rules, its Voynich result is
therefore not interpreted.**

* **Negative result for the method.** On a labelled cipher where both kinds of
  same-stem ending pair exist, the test rarely flags true edge-coupled homophones
  (2.8%, meeting the size rule). It detects only 13.8% of genuinely distinct
  pairs (AUC 0.61). The required power was 50% and AUC 0.80. The reference-logic
  rule also failed. Calibration therefore failed, and per protocol the Voynich
  output is reported without interpretation.
* **Positive, and robust.** The naive test behind the handoff's r/l claim
  (following-initial distributions differ) is actively misleading under edge
  coupling:
  * it flags **69%** of true coupled homophones as different;
  * it separates distinct from same-unit pairs *worse than chance* (AUC 0.42);
  * without coupling it behaves as expected (7% false alarms).

  This confirms and quantifies the concern raised in
  `COUPLED_CIPHER_FINDINGS_2026-09-25.md`.

## Calibration (shared-core slot cipher, known answers)

Syllable types were paired by frequency rank to share a core, with disjoint
terminal sets. Same-stem terminal pairs are therefore either the same unit or
distinct units. ZL3b layout; h = 10, s = 1; seeds 201–203. At most 150 pairs of
each kind were scored per seed, each with up to 20 matched random reference
pairs.

| Coupled regime, β = 2, pooled | Same unit (n = 318) | Distinct units (n = 450) | Rule |
|---|---:|---:|---|
| Residual test significant (p < 0.05) | **2.8%** | **13.8%** | C1: ≤ 10% same (**pass**); C2: ≥ 50% distinct (**fail**) |
| AUC of residual excess, distinct vs same | — | **0.61** | C2: ≥ 0.80 (**fail**) |
| Median reference percentile | 40 | 50 | C3: ≤ 25 same and ≥ 40 distinct (**fail**) |
| Naive test significant | **69.2%** | 63.8% | Contrast (not gated) |
| Naive AUC, distinct vs same | — | 0.42 | Contrast |

In the free regime (β = 0), the residual test has the same low power: 3.0%
against 11.2%, AUC 0.61. The naive test behaves correctly there: 6.8% against
17.6%, AUC 0.62. So the naive test fails *because of* coupling, and the residual
test fails because of *low power*, with or without coupling.

**Why power is low** (post hoc, exploratory). The statistic uses neighbouring
word identities: the top 30 types plus a catch-all. Homophony splits each unit's
contexts across many types. In the coupled cipher the top 30 types cover 16% of
tokens; in Voynich ZL they cover 26%. Most neighbours fall into the catch-all,
and 20–100 occurrences per member leave little signal.

This weakness affects any homophonic text, Voynich included if it is one. It is
not a quirk of the test cipher. A more powerful version would need context
representations that are themselves robust to homophony, for example
neighbour-unit classes from a first-pass clustering, or longer windows. That
would be a new protocol.

## Voynich (reported, not interpreted)

34 same-stem pairs with final glyph n/l/r, each member with at least 20 eligible
occurrences.

| | ZL3b | Takahashi IT2a |
|---|---:|---:|
| Pairs (with reference) | 34 (31) | 34 (32) |
| Residual test significant | 5.9% (2/34: `al/ar`, `ol/or`) | 5.9% |
| Naive test significant | 61.8% | 55.9% |
| Median reference percentile | 30 | 30 |
| Wilcoxon (percentile − 50), p | 0.055 | 0.017 |
| Categories: coupled-compatible / undetermined / distinct-like / no reference | 14 / 16 / 1 / 3 | 15 / 16 / 1 / 2 |
| Pre-set class interpretation | mixed / undetermined | mixed / undetermined |

**Stability.** 19 of 32 shared pairs get the same category in both
transcriptions.

**Sensitivities (ZL):**

| Sensitivity | Median percentile | Wilcoxon p |
|---|---:|---:|
| Finals {n, l, r, m, y} | 35 | 0.11 |
| Z with two next-token glyphs | 30 | 0.053 |
| Left context only | 50 | 0.53 |

**Pairs flagged as coupled-compatible in ZL:**

* `dal/dar`, `otal/otar`, `qotal/qotar`;
* `cheol/cheor`, `sheol/sheor`, `shol/shor`;
* `dain/dair`, `sain/sair`, `ain/air`;
* `sol/sor`, `tol/tor`, `lol/lor`, `tal/tar`, `dchol/dchor`.

Only `al/ar` is distinct-like. `chol/chor`, `ol/or` and `qokal/qokar` had no
matched reference: they are too frequent for frequency-matched partners to
exist.

**Why this is not a finding.** The calibration shows the test cannot tell the two
hypotheses apart in a known cipher: same-unit and distinct-unit pairs give
similar rates. So Voynich's low significance rate and below-median percentiles
cannot be read as support for homophony, even though they resemble the
calibration's same-unit profile. The pre-set class rule also lands in "mixed /
undetermined" on its own terms.

One descriptive observation can be stated safely. After controlling for the
boundary glyphs, Voynich r/l/n alternations show little residual context
difference: only 2 of 34 pairs, near the test's false-alarm rate. The naive test
flags 62%.

**The main consequence stands.** The evidence that r and l "carry information"
is the naive statistic, and that statistic is confounded by edge coupling.

## What this changes

* **Handoff §4.4.** The r/l argument rests on a test now shown to flag 69% of
  true coupled homophones. Whether r/l/n alternations encode different plaintext
  is **open**, and no current statistic in this project can decide it.
* **Method.** A context-residual test needs context features that survive
  homophony, and more occurrences per pair than Voynich provides for most
  alternations. A useful next attempt would:
  * cluster neighbours first, using the §19 model's high-confidence pairs or
    glyph-shape classes;
  * pool evidence across pairs as a class-level test rather than per pair.

  Calibrate it on the shared-core cipher before any Voynich run.
* **Voynich.** Nothing is merged, and no class is proposed.

## Deviations and limitations

* **Protocol.** No deviations. All rules were evaluated as written.
* **Post-hoc material.** The coverage comparison (16% vs 26%) was computed after
  the results from the committed representative texts, and is exploratory.
* **Calibration scope.** Calibration used the syllabic slot cipher only. Its
  realism limits are in `COUPLED_CIPHER_FINDINGS_2026-09-25.md`: tokens too long
  and vocabulary too closed.
* **Determinism.** Seeds are fixed throughout, but this run (about two hours) was
  not re-executed for a byte-level check, unlike the previous two stages.

```bash
OPENBLAS_NUM_THREADS=1 uv run --locked python code/16_coupling_aware_test.py
uv run --locked python -m unittest discover -s code -p 'test_coupling_test.py' -v
```
