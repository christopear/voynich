# Coupling-aware test, version 2 (overnight run): findings

26 September 2026. Protocol: `COUPLING_TEST_V2_PROTOCOL.md`, committed before the
run. The run was on the user's machine (Ubuntu, Python 3.14.4), on commit
`5f5eff7`. Results are in `results/coupling_test_v2_2026-09-25/` and logs in
`overnight/logs/`.

## Summary

* **The pre-set gates fail, so the Voynich result is not interpreted.**
  * Per-pair calibration misses C2 narrowly: 48.4% of distinct pairs detected,
    against a required 50%.
  * Pooled calibration fails P1: 14% false alarms, against a limit of 10%.
* **Distributional classes greatly increase power.** Per-pair AUC rises from
  0.61 to 0.85. Detection of distinct units rises from 13% to 48% while false
  alarms stay at 5%. Reference percentiles now separate cleanly: median 5 for
  same-unit pairs and 55 for distinct pairs.
* **The pooled failure has an identified cause (post hoc).** Neighbour classes
  are learned from the same corpus that contains the tested pairs, which leaks T
  into X. That makes the test anti-conservative for frequent pairs, *even when
  there is no coupling at all*. The fix is cross-fitting.
* **Cross-machine reproducibility is confirmed.** Stages 13, 15 and 16 rerun on
  different hardware and Python build agree with the committed outputs to at
  most 8 × 10⁻¹³ relative difference. No count, p-value, category or decision
  changed.

## Calibration (shared-core slot cipher, seeds 301–310, all eligible pairs)

| Arm, β = 2 | Same-unit / distinct pairs | False alarms (same, p < 0.05) | Detected (distinct) | AUC | Median reference percentile, same / distinct | Pooled size, 30-pair subsets | Pooled power |
|---|---|---:|---:|---:|---|---:|---:|
| **k = 100 (primary)** | 1,093 / 1,694 | 5.0% | **48.4%** | **0.85** | 5 / 55 | **14.0%** | 100% |
| k = 50 | same | 4.5% | 51.1% | 0.86 | 5 / 55 | 15.5% | 100% |
| k = 200 | same | 4.3% | 44.2% | 0.83 | 5 / 50 | 15.5% | 100% |
| Top-30 identity (version 1 method) | same | 3.4% | 13.2% | 0.62 | 35 / 50 | 7.0% | 82.5% |

For the primary arm the gates came out as:

| Gate | Result |
|---|---|
| C1 size | pass |
| C2 power | **fail**: 48.4%, just under 50% (the AUC of 0.85 passes) |
| C3 reference logic | pass |
| P1 pooled size | **fail** |
| P2 pooled power | pass |

k = 50 would pass C2, but it is a sensitivity arm and cannot be substituted
after the fact.

**The naive test** (following-initial MI, the handoff's r/l logic) reproduces the
version 1 finding at ten times the sample. It flags **70.7%** of true coupled
homophones as different, and 5.3% without coupling.

## Why the pooled test fails (post hoc)

Under an exact null, per-pair z-scores average 0. For same-unit pairs they
average +0.10 to +0.17 in all three class arms, **including β = 0**, where the
terminal is drawn independently of everything (so the null holds by
construction). The bias grows with sample size: about +0.03 to +0.07 for pairs
with fewer than 80 occurrences, and about +0.3 to +0.47 for pairs with 160 or
more. The identity arm shows no bias (+0.01, +0.005).

**Diagnosis.** The neighbour classes are estimated from the full corpus,
including the tested pair's own occurrences. A neighbour word that happens to
occur more often next to A than next to B acquires a context vector, and so a
class, that reflects this. X is then partly a function of the observed T, and
the within-Z permutation (which keeps classes fixed) is no longer an exact null.

The protocol's statement that "X is a fixed function of the neighbour token, so
the null is exact" was wrong: the function is estimated from the data being
tested.

**This is a design error, not noise.** Individual p-values still look roughly
calibrated (4–5% below 0.05), because the effect is small per pair. Pooling
exposes it.

**Candidate fix, for a new protocol.** Cross-fit the classes: split pages into
folds, learn neighbour classes on the other folds, and test occurrences in the
held-out fold. Under H_coupled, T in a held-out fold is independent of classes
learned elsewhere, so the null becomes exact again. A cheaper alternative is to
build the context matrix with all same-stem terminal variants merged into one
column, so that classes cannot separate A from B.

## Voynich (reported, not interpreted)

| | ZL3b | IT2a |
|---|---:|---:|
| Pairs (none share a member) | 34 | 34 |
| Per-pair p < 0.05 | 20.6% | 14.7% |
| Naive test p < 0.05 | 61.8% | 55.9% |
| Pooled mean z, p | +0.50, p = 0.010 | +0.43, p = 0.013 |
| V: power against matched random pairs | 100% | 100% |
| Median reference percentile | 40 | 27.5 |
| Categories: coupled-compatible / undetermined / distinct-like / no reference | 12 / 13 / 6 / 3 | 16 / 12 / 4 / 2 |

The pooled Voynich signal cannot be read as evidence of residual context. The
same leakage inflates z for frequent pairs, and most Voynich pairs are frequent;
examples include `al/ar` (489 occurrences), `dol/dor` (159) and `okal/okar`
(246). Per-pair categories are not interpretable either, because C2 failed.

**Descriptive only:**

* **Most distinct-looking:** `dol/dor` in both transcriptions (p = 0.003 and
  0.007), `al/ar` in both, and `okal/okar` in ZL.
* **Coupled-compatible in both transcriptions:** 9 pairs, among them `otal/otar`,
  `dain/dair`, `shol/shor`, `cheol/cheor`, `qotol/qotor`, `kol/kor` and
  `dchol/dchor`.
* **Stability:** 17 of 31 shared pairs got the same category in both
  transcriptions.

## Reproducibility job

| File group | Numeric differences | Largest relative difference | Discrete changes |
|---|---:|---:|---|
| Stage 13 (4 files) | 106 | 6.9 × 10⁻¹³ | none |
| Stage 15 (2 files) | 95 | 8.0 × 10⁻¹³ | none |
| Stage 16 calibration | 31 | 4.3 × 10⁻¹⁵ | none |
| Stage 16 `voynich.json` | 0 | — | byte-identical |

The manifests differ only in the recorded Python version (3.14.0rc2 here,
3.14.4 on the user's machine). Stage results are reproducible across machines to
about 12 significant digits.

## Run notes

* **Workers.** The runner set `OMP_NUM_THREADS=1` before calling `nproc`, which
  obeys that variable. It therefore used 1 worker although 20 CPUs were
  available. The run still finished in 3 h 09 min, because the user's machine is
  much faster than the estimate assumed. This is fixed in `run_overnight.sh`.
* **Stage 16 runtime.** Stage 16 took 8 minutes there, against about 2 hours in
  the cloud container.

## Deviations

None in execution. The post-hoc diagnosis above (z-bias analysis by arm, regime
and sample size) was run after the results, from the committed per-pair rows.
