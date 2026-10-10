# v101 follow-ups: findings

26 September 2026. Protocol: `V101_FOLLOWUP_PROTOCOL.md` (commit `da6f33a`,
written before any computation for this stage). Results are in
`results/v101_followup_2026-09-26/`.

## Summary

* **Why v101 gives about twice ZL3b's coupling gain: spacing (pre-set verdict
  "spacing-driven").** On the 3,876 lines common to both transcriptions, the
  gap is +0.015 bits in Currier B [0.006, 0.024]. v101's spacing accounts for
  +0.017 [0.011, 0.022] of it, and v101's glyph readings for −0.002
  [−0.007, 0.003]. On identical observations the two transcriptions give the
  same gain.
* **Specifically (post hoc):** v101 writes a full space at most places where
  ZL3b marks an *uncertain* space (804 positions, 608 in Currier B). Those
  observations carry a gain of **+0.19 bits** [0.12, 0.26], against +0.03 at
  spaces both transcriptions agree on. ZL3b's own uncertain spaces showed the
  same thing (+0.15 bits, `FRONTIER_FINDINGS_2026-09-24.md`), but 08 excludes
  them. The next-initial coupling is **strongest where word separation is
  ambiguous**. Nothing here says the manuscript's effect is larger than we
  thought.
* **Variant-test power at real minority rates (2b): the verdicts stand.** For
  y, k and r, the test detects a letter-like split at each set's own rate and
  size in 90–100% of replicates, with no false alarms. "Not letter-like" is now
  powered for all six calibrated sets. A diffuse word-level effect (LETTER-RATIO)
  would still be missed at these rates (0% detection).
* **Which variant set predicts endings (2a): the pre-set rule is invalid here.**
  The rule flags d, r and k. A post hoc locality check shows that the
  differences sit almost entirely in rows whose input does *not* change. They
  are spillover from refitting shared model coefficients, not information in
  the variants; where the variants actually change a stem, collapsing them
  predicts as well or better.
* **The earlier within-word caveat is explained.** In
  `V101_FINDINGS_2026-09-26.md`, the FULL arm's better stem-only prediction
  comes, where it is local at all, from the ambiguous symbol `A` (read by EVA
  as o or a), not from glyph variants. The FULL − COLLAPSED paired contrasts in
  Part B of those findings are also partly spillover. The file is annotated
  accordingly.

## Item 1. Decomposing the ZL3b vs v101 gain

`code/22_v101_gain_decomposition.py`, `gain_decomposition.json`. The design is
08 family × folio, with Currier B ordinary spaces and the frozen folio and
family folds.

**Gates.** R0 passed: ZL3b reproduces +0.02805 on 8,013 observations exactly.
R1 passed: rebuilding ZL3b from the character alignment gives 100% identical
tokens.

| Corpus | Letters | Spaces | N (B) | Base accuracy | Gain, bits | 95% folio CI |
|---|---|---|---:|---:|---:|---|
| Z-all (08, all P0 lines) | ZL3b | ZL3b | 8,013 | 74.0% | +0.0281 | [0.017, 0.039] |
| ZZ (common lines) | ZL3b | ZL3b | 7,997 | 73.9% | +0.0275 | [0.017, 0.038] |
| VZ | v101 | ZL3b | 8,290 | 74.2% | +0.0244 | [0.014, 0.034] |
| ZV | ZL3b | v101 | 8,788 | 72.7% | +0.0429 | [0.031, 0.053] |
| VV (common lines) | v101 | v101 | 9,117 | 72.3% | +0.0423 | [0.030, 0.053] |
| V-all (all v101 text lines) | v101 | v101 | 9,230 | 72.3% | +0.0411 | [0.029, 0.051] |

Shared-folio bootstrap, Currier B (whole manuscript in brackets):

| Quantity | Estimate [95% CI] |
|---|---|
| D = VV − ZZ | **+0.0148** [0.0056, 0.0236] (all: +0.0105 [0.0032, 0.0169]) |
| S, spacing effect | **+0.0167** [0.0108, 0.0220] (all: +0.0126 [0.0079, 0.0168]) |
| R, reading effect | −0.0018 [−0.0068, 0.0030] (all: −0.0022 [−0.0070, 0.0020]) |
| I, interaction | +0.0025 [−0.0001, 0.0054] |
| L_Z = ZZ − Z-all | −0.0006 [−0.0015, 0.0000] |
| L_V = VV − V-all | +0.0012 [−0.0002, 0.0026] |

**Verdict (pre-set): spacing-driven**, in Currier B and in the whole
manuscript. Restricting to common lines changes almost nothing (L_Z, L_V ≈ 0).

**Same observations (secondary).** 6,295 Currier B observations (79% of ZZ)
exist identically in ZZ and VV. On them, VV − ZZ = +0.0024 [−0.0040, 0.0090]:
no difference. The gap lives in the observations each transcription's spacing
creates or removes, not in how the shared ones are predicted.

### Where the spacing differs (post hoc)

`code/22b_v101_spacing_posthoc.py`, `spacing_posthoc.json`. Each ordinary space
in ZV is classed by what ZL3b has in the same aligned column, and each ZZ space
by what v101 has.

| ZV ordinary spaces, by ZL3b column (Currier B) | N | Gain | 95% folio CI | Base → context accuracy |
|---|---:|---:|---|---|
| ZL3b ordinary space (agreement) | 7,948 | +0.032 | [0.020, 0.043] | 73.6% → 76.2% |
| **ZL3b uncertain space** | **608** | **+0.190** | [0.116, 0.259] | 63.0% → 74.8% |
| ZL3b no space (v101 splits a ZL token) | 171 | +0.080 | [−0.023, 0.179] | 67.8% → 71.3% |
| ZL3b drawing gap | 61 | −0.042 | [−0.224, 0.147] | 72.1% → 63.9% |

In the other direction, v101 almost never drops a ZL3b ordinary space: 15 cases
in the whole manuscript, and 49 turned into uncertain spaces.

**Reading.** ZL3b and v101 mostly disagree about *whether a doubtful space is a
space*. v101 resolves most of ZL3b's uncertain spaces as full spaces. The
coupling at those positions is six times stronger than at clear spaces, which
lifts v101's average. On ZL3b alone, including uncertain spaces with ordinary
ones would give nearly the same result (ZV ≈ VV). So the manuscript-level
effect is best described as **a modest coupling at clear word spaces
(≈ +0.03 bits), much stronger at doubtful spaces (≈ +0.15 to +0.19)**. It is
positive but not significant where v101 splits a token that ZL3b writes as one
word, which echoes the hidden-boundary transfer.

That gradient is the most informative new result in this stage (post hoc,
needs its own test). The n/l/r ↔ next-glyph dependence is strongest where the
"words" are least clearly separated. This fits a regularity of glyph sequences
that operates across weak boundaries (orthographic or phonotactic within a
larger unit) better than a dependence between independent words. It does not
distinguish meaningful text from generated text.

## Item 2b. Variant-test power at real minority rates

`code/23_v101_variant_followups.py 2b`, `variant_power_lowrate.json`. There are
20 replicates per control and set, at each set's own n and minority rate.

| Set | n | Minority rate | NULL flagged | LETTER-STRICT detected | LETTER-RATIO detected | Verdict |
|---|---:|---:|---:|---:|---:|---|
| y | 15,747 | 2.3% | 0% | **100%** | 0% | not letter-like stands (powered) |
| k | 8,929 | 0.8% | 0% | **90%** | 0% | not letter-like stands (powered) |
| r | 5,847 | 2.6% | 0% | **100%** | 0% | not letter-like stands (powered) |

The test catches rare variants that are consistently tied to the words they
spell, which is what a real letter looks like. It does not catch a weak,
diffuse word preference at these rates. That limit is stated in the V101
findings.

## Item 2a. Which variant set predicts endings

`code/23_v101_variant_followups.py 2a`, `variant_ending_sets.json`. All
observations; positive = the variants help.

| Set | Base loss ADD-SHAM − ADD | Base loss DROP − FULL | Pre-set rule |
|---|---|---|---|
| d | +0.0129 [0.0105, 0.0154] | +0.0021 [0.0002, 0.0040] | carries |
| r | +0.0029 [0.0022, 0.0036] | +0.0028 [0.0019, 0.0037] | carries |
| k | +0.0046 [0.0034, 0.0058] | +0.0030 [0.0020, 0.0040] | carries |
| sh | +0.0001 [−0.0024, 0.0026] | −0.0040 [−0.0063, −0.0016] | no |
| y, p, f, cph | intervals include 0 or have opposite signs | | no |
| other (incl. `A`) | +0.0029 [−0.0015, 0.0074] | +0.0032 [−0.0013, 0.0075] | no |

**These verdicts should not be used.** The r minority forms occur in only 12
stems among 14,192 observations, and k's in 30. A 0.003-bit average over
14,192 rows is about 40 bits, far more than 12 rows can plausibly carry. A
locality check (post hoc, `code/23b_v101_locality_posthoc.py`,
`locality_posthoc.json`) splits each paired difference into rows whose input
changes and rows whose input is identical:

| Comparison (B − A) | Rows with changed stem | Bits in changed rows | Bits in unchanged rows | Mean abs. shift per unchanged row |
|---|---:|---:|---:|---:|
| DROP r − FULL | 12 | −6.2 | +46.4 | 0.013 |
| DROP k − FULL | 30 | −0.8 | +43.8 | 0.013 |
| DROP d − FULL | 429 | −6.0 | +35.9 | 0.043 |
| DROP sh − FULL | 242 | −24.2 | −31.9 | 0.034 |
| **DROP other − FULL** | **411** | **+104.5** | −59.6 | 0.058 |
| COLLAPSED − FULL | 1,315 | +73.2 | +81.0 | 0.110 |
| Bijective relabel of `o` (noise floor) | 8,481 | −0.1 | −0.0 | 0.0001 |

* **Numerical noise is negligible** (relabelling a symbol shifts rows by 0.0001
  bits). The spillover is real refitting, not optimiser noise. The logistic fits
  converge in about 420 of the 1,200 iterations allowed.
* **For d, r and k, the positive verdicts come entirely from unchanged rows.**
  Changing a handful of training rows re-weights shared features (stem length,
  last glyph), which moves predictions for thousands of unrelated short stems.
  Where d, r or k variants actually appear, collapsing them predicts as well or
  better. The folio-clustered intervals treat these ripples as per-row
  evidence, so they are too narrow for this question.
* **The only substantial local benefit is from "other", and 370 of its 411
  changed stems contain `A`.** `A` is the symbol that EVA readers split between
  o (59%) and a (30%). Collapsing it to o mis-transcribes about a third of its
  occurrences, so this is a mapping ambiguity, not variant information.
* **Implication for `V101_FINDINGS_2026-09-26.md` Part B.** The FULL arm's
  better base loss (+0.009 to +0.022 bits) is about half spillover, and the
  local half is mostly `A`. The FULL − COLLAPSED gain contrasts (for example
  "variants are noise" in the 06 design) are also mostly spillover (−44.8 of
  −71.3 bits on unchanged rows). The ported verdicts therefore say "no evidence
  that variants help". They should not be read as evidence that variants hurt.
  A note has been added there.

## What this stage changes

* The project's strongest result is restated with a better description:
  **Currier B next-initial coupling of n/l/r endings, ≈ +0.03 bits at clear
  spaces, several times stronger at doubtful spaces.** Transcriptions differ in
  how many doubtful spaces they count as spaces, which is why ZL3b, IT2a and
  v101 report different averages.
* v101's glyph variants: not letter-like, now with calibrated power at their
  own rates, and no local contribution to ending prediction.
* **Method lesson.** Paired per-row comparisons between model *representations*
  need a locality check: changed rows vs unchanged rows, plus a relabelling
  noise floor. Refit spillover can produce "significant" paired differences from
  a dozen rows. This affects the Part B paired contrasts in the V101 findings.
  It does not affect item 1, which compares corpora with a shared folio
  bootstrap, or the variant test itself.

## Suggested next test (not run)

Pre-register the gradient across boundary types: coupling gain at clear
spaces < doubtful spaces < hidden (token-internal) boundaries. Use ZL3b
uncertain spaces, v101/ZL3b disagreements and `boundary.py` hidden cuts, with a
matched-stem design so that composition cannot explain it.

## Deviations

* **Post hoc additions:** `22b` (spacing categories), `23b` (locality), and
  the `A` attribution. None has a pre-set rule.
* **2a rule not used.** The pre-set rule was applied and is reported, but it
  is judged invalid for its purpose because of the locality diagnostics. This
  is a deviation in interpretation, stated openly.
* **V-all differs from last round's bridge arm** (+0.041 here vs +0.052). This
  stage uses the saved 08 family folds (with missing families assigned by the
  project rule) and 08's folio filter, which drops f70. The earlier bridge arm
  used fold groups built from v101 stems. Neither run was altered.
* **Multiprocessing:** the post hoc scripts use the fork start method, because
  Python 3.14's default forkserver cannot pickle functions from dynamically
  loaded modules. Results do not depend on this.
