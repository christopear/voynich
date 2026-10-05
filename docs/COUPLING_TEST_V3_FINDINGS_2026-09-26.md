# Coupling-aware test, version 3 (cross-fitted): findings, and closure of the question

26 September 2026. Protocol: `COUPLING_TEST_V3_PROTOCOL.md`, committed before the
code. The run was on the user's machine: 20 workers, 14 min 40 s, commit
`9e811dd`. Results are in `results/coupling_test_v3_2026-09-26/` and the status
log in `overnight/logs_v3/`.

## Summary

* **The leakage fix works.** Same-unit mean z is +0.005 (β = 2) and −0.023
  (β = 0), within ±0.08, so B0 passes. In version 2 it was +0.10 to +0.17.
* **The pooled test is valid and powerful on the calibration cipher.** P1 is
  5.5% false alarms on member-disjoint subsets of 30 true-homophone pairs, and P2
  detects 98.5% of distinct-pair subsets. The pooled gate therefore passes.
* **Per-pair power collapses once the leak is removed.** Only 11.7% of distinct
  pairs are detected (AUC 0.67), so C2 fails. **Most of version 2's apparent
  power gain (AUC 0.85) was the leak itself.**
  `COUPLING_TEST_V2_FINDINGS_2026-09-26.md` is corrected accordingly.
* **Voynich: no conclusion, by the pre-set rules.** The pooled result is
  p = 0.120 on ZL3b and p = 0.030 on IT2a, so the transcriptions disagree. The
  test is also underpowered *inside Voynich*: sets of matched random Voynich
  pairs are detected only 71.5% (ZL) and 60% (IT) of the time, below the 80%
  required.
* **As the protocol pre-declared, this closes the question.** Whether Voynich
  r/l/n alternations encode different units or edge-conditioned variants of one
  unit is **not decidable with context statistics on this corpus**. No version 4
  follows.

## Calibration (shared-core slot cipher, seeds 301–310, all eligible pairs)

| Arm | β | Same-unit mean z (B0) | False alarms, per pair | Distinct detected, per pair | AUC | Median reference percentile, same / distinct | Pooled size (disjoint subsets) | Pooled power |
|---|---|---:|---:|---:|---:|---|---:|---:|
| **k = 100 cross-fitted (primary)** | 2 | **+0.005** | 1.3% | **11.7%** | 0.67 | 25 / 55 | **5.5%** | **98.5%** |
| k = 100 cross-fitted | 0 | −0.023 | 2.0% | 11.4% | 0.67 | 25 / 50 | 3.5% | 98.0% |
| k = 50 cross-fitted | 2 | −0.007 | 2.3% | 13.1% | 0.67 | 25 / 50 | 6.0% | 98.0% |
| Top-30 identity | 2 | +0.013 | 3.4% | 13.2% | 0.62 | 35 / 50 | 4.5% | 84.0% |

For the primary arm the gates came out as:

| Gate | Result |
|---|---|
| B0 leakage check | pass |
| C1 size | pass |
| C2 power | **fail** |
| C3 reference logic | pass |
| P1 pooled size | pass |
| P2 pooled power | pass |

So:

* **Per-pair Voynich categories:** not interpretable.
* **Pooled Voynich result:** eligible for interpretation, subject to the Voynich
  rules.

**The naive test**, the handoff's r/l logic, again flags **70.7%** of true
coupled homophones as different, against 5.3% without coupling. Across versions
1 to 3, using different seeds and 1,093 pairs in version 3, this is the most
stable result of the whole line of work.

## Voynich (pooled result evaluated under the pre-set rules)

| | ZL3b | IT2a |
|---|---:|---:|
| Pairs (none share a member) | 34 | 34 |
| Pooled mean z | +0.17 | +0.33 |
| Pooled p | 0.120 | **0.030** |
| V: detection of matched random pairs | 71.5% | 60.0% |
| Median reference percentile | 40 | 47.5 |
| Per-pair p < 0.05 | 8.8% | 11.8% |
| Naive test p < 0.05 | 61.8% | 55.9% |
| Categories: coupled-compatible / undetermined / distinct-like / no reference (not interpretable) | 11 / 17 / 3 / 3 | 8 / 20 / 4 / 2 |

**Pre-set interpretation:** *"ZL and IT disagree: transcription-sensitive, no
conclusion."* Even if they had agreed, the ZL result (p ≥ 0.05 with V < 0.80)
would have been classed as underpowered.

**Descriptive only.** Both transcriptions put r/l/n pairs between the calibration
profiles. Mean z is positive but small. Median reference percentiles (40 and
47.5) sit between the true-homophone profile (25) and the distinct-unit profile
(50–55). The data do not clearly resemble either hypothesis, and the test cannot
separate them at this sample size.

## Why the question cannot be decided this way

* **Context signal is weak.** In Voynich, even random pairs of *different* word
  types with matched frequency are hard to tell apart from their neighbours once
  boundary glyphs are controlled (V = 60–72% for pools of 34 pairs). Distinct
  r/l/n pairs, which share a stem and hence much of their distribution, would be
  harder still.
* **Homophony fragments contexts.** Neighbour identities are split across
  spellings. Distributional classes can undo that only if they are learned
  in-sample, which leaks the answer. Cross-fitting removes the leak and most of
  the power with it.
* **The corpus is fixed.** Most r/l/n pairs have 20–300 occurrences per member.
  More seeds or permutations cannot add information that the manuscript does not
  contain.

## What stands

* **The naive r/l argument is invalid under edge coupling.** It flags 71% of true
  coupled homophones. The handoff's §4.4 claim that "r ≠ l because following
  contexts differ" does not establish different plaintext.
* **Voynich r/l/n unit identity is an open question,** now documented as not
  decidable by context-residual tests on current transcriptions. Deciding it
  would need non-distributional evidence, for example palaeographic, positional
  or cross-manuscript evidence, or a much larger comparable corpus.
* **Method lessons**, useful beyond Voynich:
  * Distributional features learned in-sample leak into permutation tests.
    Cross-fit them, and add an explicit null-regime bias gate.
  * A pooled test needs its calibration subsets to match the target's
    dependence structure (here, member-disjoint pairs).
  * Both version 2 flaws were caught only because calibration included a
    no-coupling regime and gates were fixed in advance.

## Deviations

* **Protocol:** none. All rules were evaluated as written.
* **Log file:** the job log `10_coupling_v3.log` was not committed, because the
  repository `.gitignore` excludes `*.log`. The status log and all result files
  were committed.
