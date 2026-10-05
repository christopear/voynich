# v101 follow-ups: why the coupling gain doubles, and which variants matter — protocol

Written 26 September 2026, after `V101_FINDINGS_2026-09-26.md` and **before**
any computation for this stage.

Known beforehand, all from `V101_FINDINGS_2026-09-26.md` and earlier work:

* The 08 family × folio Currier B gain is +0.0281 on ZL3b and +0.0362 on IT2a.
  On v101 it is +0.0522 in the v101-EVA bridge arm and +0.0646 in COLLAPSED.
  Base accuracy is 74.0% on ZL3b and 68.4% on the bridge arm.
* In the FULL arm the stem-only (base) model is better than in COLLAPSED and
  SHAM, by 0.009–0.022 bits.
* Variant-test calibration used minority rates of about 20%. The real minority
  rates are about 2.3% for y, 0.8% for k and 2.6% for r.

Nothing about hybrids, per-set contributions or low-rate calibration has been
computed.

## Item 1. Decomposing the ZL3b vs v101 coupling gain

### 1.1 Common machinery (fixed)

* **Design:** 08 family × folio crossed design with the original features and
  models (`06_boundary_frontier.Model`), EVA glyph units, and ordinary
  within-line spaces only. The outcome is the **Currier B gain** in bits, with
  whole-manuscript gain as a secondary.
* **Folds:** frozen folio folds. Family folds come from the saved 08 assignment
  (`results/mechanisms_2026-09-24/gate_manifest.json`). A family missing from
  it gets a fold from the project rule applied to the missing families only, so
  every corpus below shares one fold assignment.
* **Reproduction gate R0:** the ZL3b corpus through this machinery must
  reproduce the recorded +0.02805 (to ±0.0001) on 8,013 Currier B
  observations. If it does not, the stage stops and the discrepancy is
  reported.

### 1.2 Corpora

Line pairs = v101 text lines aligned (`line_alignment.csv`) to a ZL3b line
whose descriptor is P0. P0 is the line set 06/08 use.

For each line pair, the ZL3b line string (clean first readings, `.`/`,`
separators) and the v101-EVA line string (argmax transliteration, same
separators) are aligned **character by character**. A letter may match or
substitute only another letter, and a separator only another separator.
Letters and separators can otherwise only be inserted or deleted, at cost 1
each, with a substitution cost of 1. Letters of an unclean word are replaced
by a sentinel that makes any hybrid word containing it unclean. From each
alignment:

| Corpus | Letters from | Spaces (and space type) from |
|---|---|---|
| **ZZ** | ZL3b | ZL3b |
| **ZV** | ZL3b | v101 |
| **VZ** | v101 | ZL3b |
| **VV** | v101 | v101 |

ZZ is ZL3b rebuilt from the alignment. On matched lines it should equal ZL3b's
own tokenisation. The share of ZZ tokens identical to the parser's tokens is
reported as check R1, which requires ≥ 99%.

Two further corpora bracket the line-set effect: **Z-all** (the full ZL3b P0
corpus, R0) and **V-all** (every v101 text line, v101-EVA).

### 1.3 Quantities

G(X) = Currier B gain for corpus X. All differences use a **shared folio
bootstrap**: 2,000 resamples of folios, applied to every corpus at once, with
seed 20260926. This works because all corpora share the folio set.

* **Total gap on common lines:** D = G(VV) − G(ZZ).
* **Spacing effect:** S = ½[(G(ZV) − G(ZZ)) + (G(VV) − G(VZ))].
* **Reading effect:** R = ½[(G(VZ) − G(ZZ)) + (G(VV) − G(ZV))].
* **Interaction:** I = G(VV) − G(VZ) − G(ZV) + G(ZZ).
* **Line-set effects:** L_Z = G(ZZ) − G(Z-all) and L_V = G(VV) − G(V-all).
* Base accuracy and base loss are reported for every corpus.

### 1.4 Decision rules

* If the D interval includes 0, the verdict is **"line-set / observation-set
  driven"**: the gap disappears on common lines, and L_Z and L_V describe where
  it came from.
* Otherwise the verdict is **"spacing-driven"** if S has the sign of D, its
  interval excludes 0, and |S| ≥ 0.5|D|. It is **"reading-driven"** under the
  same conditions for R. If both qualify, the verdict is "both". If neither
  does, it is **"mixed / interaction"**, and I is reported.
* **Secondary, same observations:** observations present in both ZZ and VV
  with the same ZL locus, left word, right word and ordinary space (matched in
  order of occurrence). Their gains under each corpus's own cross-fitted models
  are compared with a folio-cluster interval on the paired difference. A gap
  that persists on identical observations is read as coming from the rest of
  each corpus (training data), not from the test observations.

## Item 2a. Which variant set carries the within-word ending information

The 08 family × folio design on v101 units, as in the V101 Part B coupling
port. The quantity is the **base (stem-only) loss**, and the context gain is
reported alongside. Rows are identical across all arms below.

The sets are the eight eligible sets (d, sh, r, y, k, p, f, cph), plus
**other**: all remaining multi-member classes together (including o/`A`).

For each set S:

* **ADD(S):** COLLAPSED, but with set S's members restored to their v101
  symbols.
* **ADD-SHAM(S):** as ADD(S), but S's member labels are permuted across all
  text occurrences of the class (seeds 1–3, averaged).
* **DROP(S):** FULL, but with set S collapsed.

Rule: S **carries within-word ending information** if base loss
ADD-SHAM(S) − ADD(S) > 0 **and** DROP(S) − FULL > 0, both with folio-cluster
intervals above 0. Currier B and all observations are both reported; the
verdict uses all observations. The context-gain differences are descriptive.

## Item 2b. Variant-test power at realistic minority rates

This is for the three sets whose verdicts may be underpowered: y (n = 15,747,
minority 2.3%), k (8,929, 0.8%) and r (5,847, 2.6%). The minority rate for r
pools x, Y and b.

The Part A machinery is unchanged (collapsed arm, same models, same decision
rule). Synthetic two-member splits are imposed on the base classes o, a, c, 1
and e. Each replicate subsamples n = min(the set's n, the base's occurrences),
with 4 seeds per base, giving 20 replicates per control and set. Controls, at
the set's minority rate r:

* **NULL:** P(B) = r everywhere.
* **LETTER-STRICT:** a random subset of masked-word keys is "spelled with B".
  Keys are drawn in random order until their occurrences reach r/0.9 of the
  total. Those keys get P(B) = 0.9 and all others 0. This is what a real
  letter with 10% transcription noise looks like.
* **LETTER-RATIO:** 25% of keys get q_hi and the rest q_lo, with
  q_hi / q_lo = 12 (as in Part A) and mean r. This is a weaker, diffuse
  word-level effect, reported as sensitivity.

Rules per set:

* **Size:** NULL letter-like rate ≤ 10%. If this fails, the set's verdict is
  not interpretable.
* If LETTER-STRICT letter-like rate ≥ 80%, the Part A verdict "not letter-like"
  **stands, with power against letter-like spelling at the set's own rate**.
  Otherwise it is **downgraded to "underpowered"**.
* LETTER-RATIO power is reported without a rule.

## Outputs

`results/v101_followup_2026-09-26/`: `gain_decomposition.json`,
`variant_ending_sets.json`, `variant_power_lowrate.json`. Code:
`code/22_v101_gain_decomposition.py`, `code/23_v101_variant_followups.py`.
Findings go in `V101_FOLLOWUP_FINDINGS_2026-09-26.md`, with any deviations
listed there.
