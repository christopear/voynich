# v101 stage: glyph-variant test and ports of earlier analyses — protocol

Written 26 September 2026, after the v101 parser and the v101 → EVA mapping were
built (commit `b8872d5`) and **before** any variant, position, scribe or
port statistic was computed on v101.

Known beforehand: all earlier project results (ZL3b and IT2a), and the step 1
outputs in `results/v101_2026-09-26/` (`mapping.json`, `agreement.json`,
`line_alignment.csv`). Those give symbol counts, EVA images, alignment purity
and word agreement (v101 vs ZL3b 89.7% exact; IT2a vs ZL3b 90.1%). No
statistic about where or in which context a variant occurs has been looked at.

## 0. Data and shared definitions

* **Corpus:** v101 *text* lines (sub-locus is an integer), 3,978 lines. Label,
  ring and radial lines are excluded throughout. Words containing `*` or `?` are
  unclean and never used as targets or context (they break neighbourhoods, as in
  the ZL3b parser).
* **Metadata:** Currier language `$L`, hand `$H`, section `$I` and quire `$Q`
  come from the ZL3b page header of the same page. If the v101 line is aligned
  to a ZL3b line (`line_alignment.csv`), that line's inline metadata is used
  instead (this only matters for the f115r hand change).
* **Folds:** the 5 physical folio folds frozen in
  `results/frontier_2026-09-24/manifest.json`. A v101 folio missing there gets a
  fold from the project rule (sorted, shuffled with seed 20260924, rank mod 5)
  applied to the missing folios only.
* **Classes and variants.** Each v101 symbol's EVA class is its argmax EVA image
  in `mapping.json`. A *merged set* is a set of v101 symbols with the same EVA
  image. A member is **testable** if it has ≥ 20 occurrences in text lines,
  alignment purity ≥ 0.80, and ≥ 10 aligned occurrences. A set is **eligible**
  if it has ≥ 2 testable members and the second most frequent testable member
  has ≥ 30 text occurrences. This rule gives eight sets:

  | EVA class | Testable v101 members |
  |---|---|
  | d | `8`, `7`, `6` |
  | sh | `2`, `3`, `5`, `%`, `+`, `!`, `#` |
  | r | `y`, `x`, `Y`, `b` |
  | y | `9`, `(` |
  | k | `h`, `W` |
  | p | `g`, `j` |
  | f | `f`, `u` |
  | cph | `J`, `G` |

  Not eligible: s, cfh, ckh, cth, m (minor members too rare), and o, whose only
  other member `A` has purity 0.59 (EVA readers split it between o and a). `A`
  is recorded as an ambiguous symbol, not a variant.
* **Collapsed v101.** Every symbol is replaced by the most frequent v101 symbol
  of its EVA class (`collapse_table` in `mapping.json`). Word boundaries,
  readings and unit segmentation stay exactly as in v101. Only the variant
  distinctions are removed. This is what "v101 collapsed to EVA classes" means
  in every paired comparison below.

## Part A. Glyph-variant test

### A1. Question

For each eligible set: is the choice of variant explained by **position**
(capital-like), by **scribe** or **neighbouring glyphs** (handwriting variant),
by **codicological location** (drift within the manuscript or the
transcription), or does it carry **residual information** about the word it is
in (letter-like)?

### A2. Units and outcome

One observation = one occurrence of a testable member in a clean word of a text
line. Outcome = which member (multinomial). Occurrences of non-testable members
of the set are dropped.

### A3. Feature families

All context is computed with the target position masked to its class.

* **POS:** word position in line (first / last / only / middle); first line of
  paragraph; last line of paragraph; first word of paragraph; glyph position in
  word (initial / final / medial / sole); "capital slot" (glyph is the first
  glyph of the line; first glyph of the paragraph).
* **SCRIBE:** hand; Currier language; hand × language.
* **LOC:** quire; section.
* **NB:** previous and next glyph (`^`/`$` at word edges), and their pair.
* **WIDE:** glyphs two positions before and after (`^^`/`$$` beyond the edge).
  WIDE is not a control family. It is used only in the residual safeguard (A5).
* **RES (lexical):** key = the word with the target position masked, plus the
  target's index in the word. Out-of-fold target encoding: for each member v,
  log((n_kv + 2·π_v)/(n_k + 2)), where π is the training marginal, plus
  log(1 + n_k). Training rows are encoded with 5 inner folio folds inside the
  training folios. Test rows are encoded from all training folios.

### A4. Models and metric

Multinomial logistic regression (DictVectorizer, C = 1, lbfgs, max_iter 2000),
fitted on 4 folio folds and scored on the fifth. Models: M0 (marginal), POS,
SCRIBE, LOC, NB, CTRL = POS+SCRIBE+LOC+NB, CTRL−F for each family F,
CTRL+RES, CTRL+WIDE, CTRL+WIDE+RES.

Metric: mean held-out log-loss in bits per occurrence. Every comparison is a
paired per-occurrence difference, with a 95% folio-cluster bootstrap interval
(2,000 resamples, seed 20260926).

* **Unique gain of F:** L(CTRL−F) − L(CTRL).
* **Explained share:** E = (L(M0) − L(CTRL)) / L(M0).
* **Residual gain:** R = L(CTRL) − L(CTRL+RES).
* **Safeguarded residual:** R_w = L(CTRL+WIDE) − L(CTRL+WIDE+RES).

### A5. Decision rules (per set)

* A family F **contributes** if its unique gain is ≥ 0.005 bits and its interval
  lies above 0.
* **Letter-like (residual information):** R ≥ 0.01 bits with interval above 0,
  **and** R_w ≥ 0.01 bits with interval above 0. The WIDE safeguard stops an
  allograph conditioned two glyphs away from being called a letter.
* Primary label when the set is not letter-like: the contributing family with
  the largest unique gain. POS gives **capital-like/positional**; SCRIBE or NB
  gives **handwriting variant** (scribal or contextual, named separately); LOC
  gives **codicological drift**. If no family contributes, the label is
  **unexplained**: free variation, or transcription noise.
* Letter-like sets also report their contributing families.
* **Caveat, fixed now:** "letter-like" means that the variant is consistent
  within word types across folios beyond position, scribe, location and ±2
  glyph context. A transcriber who reads known words consistently, or
  word-specific writing habits, would produce the same signature. The label is
  necessary for, not proof of, distinct letters.

### A6. Paired design (full vs collapsed context)

Every model is fitted twice: once with NB, WIDE and RES built from **collapsed**
v101 (the primary arm, where context ignores other variant choices) and once
from **full** v101 symbols. Decision rules A5 are applied to the collapsed arm.
The paired contrast per set is L(CTRL+RES, collapsed) − L(CTRL+RES, full), with
an interval.

* **Variant coherence:** full context predicts better (interval above 0). Other
  variant choices in the same word or neighbourhood predict this one, so the
  choices are not independent draws. This is reported descriptively. It does
  not by itself separate letters from handwriting or transcriber habit.

### A7. Calibration with synthetic variants (gates)

Synthetic two-member variants are imposed on single-symbol classes of collapsed
v101: `o`, `a`, `c` (e), `1` (ch), `e` (l). Real positions, words, scribes and
folios are used. The minority member B is assigned by these rules:

| Control | Rule for P(B) |
|---|---|
| NULL | 0.2 everywhere |
| POS | 0.5 in the first word of a line, 0.15 elsewhere |
| SCRIBE | 0.3 in hand 1, 0.1 elsewhere |
| NB | 0.4 if the next glyph is that class's most common next glyph, 0.1 elsewhere |
| WIDE | 0.4 if the glyph two to the right is the most common such glyph, 0.1 elsewhere |
| LETTER | each masked-word key gets propensity 0.6 with prob. 0.25, else 0.05 |

Each replicate draws a subsample of occurrences of size n ∈ {300, 1000, 5000}
(or all, if fewer), with 20 replicates per control and size (5 base classes × 4
seeds, seeds 1–4). The collapsed arm only.

Gates, evaluated per size:

* **G1 residual size:** letter-like rate ≤ 10% in each of NULL, POS, SCRIBE
  and NB.
* **G2 residual power:** letter-like rate ≥ 80% in LETTER.
* **G3 attribution:** the correct primary label (POS → positional; SCRIBE →
  scribal; NB → contextual) in ≥ 80% of replicates for each of the three.
* **G4 wide safeguard:** letter-like rate ≤ 20% in WIDE.
* **G5 null:** label "unexplained" in ≥ 80% of NULL replicates.

A Voynich set is judged against the largest calibrated size not above its
occurrence count (sets with < 300 occurrences use n = 300 and are marked as
extrapolated). Residual verdicts are interpreted only if G1, G2 and G4 pass at
that size. Attribution labels are interpreted only if G3 and G5 pass. Anything
that fails is reported descriptively only.

## Part B. Ports of earlier analyses (paired design)

Three arms, with identical tokens, word boundaries and observations:

* **FULL:** v101 symbols.
* **COLLAPSED:** v101 collapsed to EVA classes.
* **SHAM:** within every merged set, member labels are permuted across all
  text occurrences of the class (global permutation, seeds 1–3). This keeps the
  alphabet size and marginal frequencies of FULL and removes any real variant
  information. It controls for the cost of a larger alphabet.

A bridge arm, **v101-EVA** (v101 transliterated to EVA strings and run through
the unchanged original pipeline), links the results to ZL3b numbers. It is
descriptive.

"Variants carry information for analysis X" requires FULL > COLLAPSED **and**
FULL > SHAM (mean over the three shams), both with intervals excluding 0. If
FULL is worse than both, with intervals below 0, the result is "variants are
noise for X". Anything else is "no evidence either way".

### B1. Ending coupling (stages 06/08)

Unit = one v101 symbol. Target = the 3-way EVA terminal class (n / l / r) of the
word's last symbol. A symbol is terminal if its EVA image ends in n, l or r:
`m` (iin), `n` (in), `N`, `M` (iiin), `e` (l), `y`/`x`/`Y`/`b` (r), `z`
(ir), `Z` (iir) and so on, by the mapping. The target is identical in all arms.
Stem = the word minus its last symbol. Initial = the first symbol of the next
word. Families (08) are computed from the EVA transliteration of the stem with
the 08 rule, so they are identical in all arms. Features, models, folds and
metrics are those of 06/08, with glyph = one v101 unit.

* **Primary:** 08 family × folio crossed design, Currier B, ordinary spaces.
  Gain = loss(base) − loss(context), in bits.
* **Secondary:** 06 stem × folio crossed design (all, A, B).
* **Replication rule (COLLAPSED arm):** gain > 0 with both folio- and
  family-clustered intervals above 0 gives "replicates on a third
  transcription". Gain > 0 with an interval including 0 gives "direction only".
  Otherwise "does not replicate".
* **Variant rule:** paired per-observation differences in gain, FULL − COLLAPSED
  and FULL − SHAM, folio-cluster intervals, read with the Part B rule. The
  base-model loss difference (does variant spelling of the stem predict the
  ending?) is reported the same way, descriptively.

### B2. §19 classifier (stage 13)

The frozen Naibbe-trained logistic and boosting models are refitted exactly as
in 13 and applied to FULL and COLLAPSED v101 (glyph = one unit; terminal set =
symbols whose EVA image ends in n, l, r or m), and to each arm globally
shuffled (seed 20260925). The message-free control rates are taken from
`results/equivalence_2026-09-25/application.json`.

* The §19 interpretation rule is applied to COLLAPSED as the third
  transcription. Stability against ZL3b is Spearman correlation and top-100
  overlap over type pairs whose EVA transliterations are both ZL types.
* **Paired, variant-only pairs (FULL):** type pairs that become identical when
  collapsed. Their probabilities are compared with *one-substitution* pairs,
  which differ in exactly one unit where the two units are of different EVA
  classes, matched on length. The test is Mann–Whitney, one-sided. If
  variant-only pairs score higher (p < 0.05), the classifier treats variants as
  more interchangeable than real substitutions, which is consistent with
  allography. Otherwise there is no support. Because §19 failed its Voynich
  gates earlier, all of B2 is **descriptive**, and no homophony claim can
  follow.

### B3. Hidden boundaries (visible → hidden terminal prediction, `boundary.py`)

The same procedure as `boundary.py`: joined frequency ≤ 2, ≥ 6 units, parts
≥ 5 occurrences and ≥ 2 units, and the best split by freq × freq. Target = the
3-way EVA terminal class of the left part's last unit, in all arms. Tables are
learned from visible spaces only.

* **Replication rule (COLLAPSED):** on examples where both predictors are
  evaluable, stem + initial accuracy exceeds stem-only, with exact McNemar
  p < 0.05.
* **Arm comparison:** candidate sets differ between arms (splitting types
  changes frequencies), so FULL vs COLLAPSED vs SHAM is compared
  **descriptively** (accuracy gain with a candidate bootstrap interval). No
  paired claim is made.

## Outputs

`results/v101_2026-09-26/`: `variant_calibration.json`, `variant_test.json`,
`port_coupling.json`, `port_equivalence.json`, `port_hidden_boundary.json`,
and prediction CSVs where they are small. Code: `code/20_v101_variant_test.py`,
`code/21_v101_ports.py`. Findings go in `V101_FINDINGS_2026-09-26.md`, with any
deviation from this protocol listed there.
