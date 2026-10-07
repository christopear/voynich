# New experiments: terminal generalization and physical layout

24 September 2026. This report covers new work extending `boundary.py`, rather
than rerunning the original handoff analyses. The original code and results are
preserved. The prospective specification is `FRONTIER_PROTOCOL.md`; individual
held-out predictions and machine-readable results are in
`results/frontier_2026-09-24/`.

## Executive interpretation

We have a small, measurable advance in the evidence for a transferable boundary
regularity. Knowing the following initial improves prediction of an n/l/r
terminal even when both the entire preceding stem and its physical folio were
excluded from training. Accuracy rises from **70.19% to 73.60%**, and probability
forecasts improve by **0.02349 bits per terminal**. Both folio-clustered and
stem-clustered intervals exclude zero for this token-weighted comparison.

That finding is narrower than a general rule of Voynichese. The improvement is
concentrated in Currier B and shorter stems. Giving every distinct stem equal
weight makes the aggregate gain inconclusive. We have not identified a language,
proved phonological sandhi, or shown that inferred internal cuts are true words.

The combined layout work puts a useful limit on the finding. The rule does not
reliably transfer to drawing interruptions, and its probability forecasts often
worsen across line or paragraph breaks. However, comparisons restricted to the
same stem/context combinations are too uncertain to attribute this difference
specifically to boundary type. Adding measured horizontal starting position
does not clearly improve prediction after the textual controls.

The best working hypothesis to pursue is therefore **a local, context-sensitive
writing regularity whose strength varies with textual stratum and boundary
class**. Its generating mechanism remains unresolved. These results constrain
future models; they do not distinguish linguistic content, encoding conventions
and structured generation by themselves.

## What was actually tested

The new parser retains separator types rather than flattening them. It excludes
uncertain glyph readings without accidentally joining their neighbours, handles
inline comments without inventing token boundaries, and respects the inline
change from hand 2 to hand 3 on f115r. Paragraph titles are excluded from ordinary
body-line continuations. A stem means the complete observed token minus its last
n/l/r glyph; it is an operational definition, not a linguistic claim.

The dataset has 3,885 P0 body lines, 33,970 token slots and 32,887 clean tokens.
Eligible n/l/r observations comprise:

| Boundary | Observations |
|---|---:|
| Certain ordinary space | 12,303 |
| Uncertain space | 1,048 |
| Drawing interruption | 226 |
| Within-paragraph physical line break | 990 |
| Paragraph break | 167 |

These are conditional samples of terminals n/l/r. Other endings, including the
layout-relevant m, are outside this experiment. Results must not be generalized
to all token endings or all manuscript text.

All sides and foldout panels with the same folio number stay together. Five
folio folds test new pages. The stronger design crosses those folds with five
stem folds: each prediction comes from a model that saw neither its exact stem
nor its folio. There are 25 training/test combinations for each crossed model.
The ordinary-space crossed evaluation covers 1,754 stems and 98 physical folios.
Assertions check actual disjointness during fitting.

The baseline uses stem shape, glyph counts, hand, Currier group, section,
relative ordinal position and paragraph start. The context model adds the next
initial and fixed interactions with stem suffix and hand. The folio-only
identity model also uses exact stem and stem/initial features; the crossed
models do not. All are fixed-C multinomial logistic regressions, without tuning
against the reported outcomes. Training categories are fitted within each split.

The primary metric is reduction in negative log probability, in bits per
terminal. Positive values mean better predictions; negative values mean worse
predictions. Unlike accuracy, it penalizes confidently wrong forecasts. The
95% intervals below use 2,000 paired cluster bootstrap samples. Separate folio
and stem intervals are reported; they are not a two-way bootstrap. They condition
on the fitted models and do not capture model-refitting uncertainty or all
dependence from overlapping training folds.

## 1. Transfer to unseen stems

| Test | Accuracy, baseline → context | Gain, bits | 95% folio interval | 95% stem interval |
|---|---:|---:|---:|---:|
| Unseen folio, exact-stem features allowed | 72.87% → 74.40% | +0.00317 | −0.00768 to +0.01231 | Includes zero |
| **Unseen folio AND unseen exact stem** | **70.19% → 73.60%** | **+0.02349** | **+0.01274 to +0.03277** | **+0.00686 to +0.04319** |
| Unseen folio, shared shape features only, exploratory | 72.91% → 75.34% | +0.02209 | +0.01268 to +0.03040 | +0.00703 to +0.03843 |

The primary crossed gain is positive in all five folio folds, from +0.00368 to
+0.03974 bits. Its accuracy improvement is 3.41 percentage points, with a
folio-clustered interval of approximately +2.71 to +4.05 points. Brier score also
improves, from 0.36192 to 0.34275.

The first row matters: a sparse exact stem/initial model improves classification
without delivering a clear probability-score benefit. The exploratory shared
model supports the interpretation that some regularity transfers through common
features and that excessive exact-cell specificity can hurt forecasting. It is
not proof that one learned feature corresponds to a historical writing rule.

A training-frequency-only reference achieves 37.19% accuracy and 1.58275 bits
loss on ordinary spaces. The shared structural baseline already reduces this to
72.91% and 0.74747 bits. Most predictability is in the stem and controls; the next
initial supplies a modest additional contribution. Shuffling initials within
test pages makes the identity context model worse than its baseline by 0.09008
bits. This is a diagnostic, not a conditional-randomization significance test.

### Where the transfer is concentrated

The following checks were chosen after seeing the primary results and are
exploratory, without multiplicity correction.

| Crossed evaluation subset | N | Gain, bits | 95% folio interval |
|---|---:|---:|---:|
| Currier A | 4,200 | −0.00364 | −0.02335 to +0.01432 |
| Currier B | 8,013 | +0.03851 | +0.02790 to +0.04808 |
| Stem length at least 2 glyphs | 11,322 | +0.01151 | +0.00112 to +0.02010 |
| Stem length at least 3 glyphs | 9,108 | +0.00838 | −0.00146 to +0.01705 |
| Stem length at least 4 glyphs | 6,416 | +0.00384 | −0.00580 to +0.01225 |

Equal weighting of the 1,754 distinct stems yields only +0.00286 bits, with a
stem-resampled interval of −0.01664 to +0.02274. Thus the token-weighted success
does not demonstrate broad, equally strong productivity throughout the stem
inventory. Currier group, scribal hand and section are also confounded; this is
not evidence of a causal “dialect effect.”

## 2. Transfer to proposed hidden boundaries

The old experiment scored cuts using the exact left variant's frequency. Here
the cut score instead pools all three terminal variants, and both left-family
and right-token frequencies come exclusively from training folios. Test folios
do not contribute frequencies or training observations. The terminal model is
trained only at visible certain spaces.

The resulting 882 type-by-test-fold cases contain 785 distinct joined types,
126 stems and 87 folios. The model has encountered all 126 stems at ordinary
spaces in its respective training split. This is transfer to a hypothesized
boundary inside another token, **not another unseen-stem experiment**.

| Measure | Baseline | With next initial |
|---|---:|---:|
| Accuracy | 59.41% | 67.35% |
| Log loss, bits | 1.06393 | 1.00339 |
| Brier score | 0.49516 | 0.44693 |

The accuracy gain is **7.94 percentage points**, with a folio-clustered interval
of approximately +2.75 to +12.58 points. However, the primary probability gain
of +0.06055 bits has a folio interval of **−0.06478 to +0.16069**, and one folio
fold is negative. Keeping only one occurrence per joined type produces the same
broad conclusion: 785 cases, 58.85% → 67.01% accuracy, but a probability-gain
interval that includes zero.

This extends the earlier result with more defensible selection and held-out
pages. The new and old percentages are not directly comparable because the
parser, candidate population, model and evaluation unit changed.

There is still no independent ground truth for the cuts. Selection conditions
on an observed n/l/r and a familiar right fragment, and can choose among several
cuts. Pooling removes one specific terminal-frequency preference; it does not
make selection neutral or establish segmentation correctness. No result here
licenses calling 67% of these cuts “correct.”

## 3. Joint generalization and layout

Models trained at ordinary spaces were evaluated at other boundary classes.
The following joint check additionally excludes each test stem and its folio;
it was added as an explicitly exploratory extension of the primary design.

| Boundary, unseen stem and folio | N | Context gain, bits | 95% folio interval |
|---|---:|---:|---:|
| Ordinary space, primary comparison | 12,303 | +0.02349 | +0.01274 to +0.03277 |
| Drawing interruption | 226 | −0.00408 | −0.07040 to +0.07095 |
| Within-paragraph line break | 990 | −0.04463 | −0.08445 to −0.00909 |
| Paragraph break | 167 | −0.11117 | −0.22156 to −0.00529 |
| Uncertain space | 1,048 | +0.14753 | +0.09511 to +0.20032 |

The line-break stem-clustered interval narrowly includes zero, while the
paragraph result is based on a small, selected sample. These outcomes show
where an ordinary-space predictor fails; they do not prove a different physical
mechanism. Training models on all boundary classes with boundary-specific
features did not rescue the context gain at drawings or line breaks with the
fixed model specification. Sparse data, model misspecification and distribution
changes remain explanations.

To check composition, an additional comparison matched exact stem, next initial,
hand, Currier group and section. It standardized ordinary-space predictions to
the target boundary's distribution over shared cells:

| Contrast | Matched target N | Difference in context gain, target − ordinary | 95% folio interval |
|---|---:|---:|---:|
| Drawing vs ordinary | 140 | −0.05613 bits | Includes zero |
| Line break vs ordinary | 472 | −0.09526 bits | Includes zero |
| Paragraph vs ordinary | 21 | +0.10426 bits | Includes zero |

This stronger comparison is inconclusive. The evidence supports caution about
transporting the rule between boundary classes, but not a confident claim that
drawings cause a switch in the encoding process. The large uncertain-space
effect is consistent with existing separator research and is not claimed as a
new discovery.

## 4. Physical coordinates beyond text position

Public coordinate files were reused from the
[Rozanova–Temerev reproducibility archive](https://github.com/lrozanova/voynich-units).
The exact tree and individual file hashes are recorded. No upstream analysis
script was executed to obtain our results.

The alignment requires exact token sequences of at least three matches, then
adjacent coordinate entries, increasing horizontal position and overlapping
vertical boxes. Across 201 pages with P0 text and coordinate data, 28,370 of
33,556 text token slots lie in qualifying matching blocks. There are 23,289
eligible adjacent aligned pairs before the terminal/cleanliness restrictions.
The terminal analysis uses 10,128 ordinary-space and 186 drawing-gap pairs.
Repeated sequences can still be misaligned; there has been no independent blind
image audit. Matching also selects a potentially easier subset of the text.

The added predictor is the current token's **left edge**, normalized by the
page-wide box extent, represented continuously and in ten fixed bins. The
baseline already includes ordinal position, stem, next initial and textual
metadata. We deliberately exclude the current token's width, right edge and
following gap as predictors, because they are partly determined by writing the
terminal itself.

| Coordinate subset | Added-position gain, bits | 95% folio interval |
|---|---:|---:|
| Ordinary spaces | +0.00068 | −0.00208 to +0.00351 |
| Drawing interruptions | −0.00710 | −0.03024 to +0.02284 |

There is **no clear incremental predictive benefit** from this coordinate proxy.
This does not rule out physical layout effects. Starting position is not the
amount of space the scribe expected to have before a drawing, and page-wide
normalization is a coarse approximation on irregular pages. A direct test of
space pressure needs independently annotated writing-region boundaries.

## Relation to existing research

[Currier's observations](https://voynich.nu/extra/curr_main.html) already discuss
terminal/initial dependencies and the special role of lines. We have not
discovered either phenomenon. The advance here is testing predictive transfer
after withholding exact stems and physical folios, and quantifying its limits.

[Steckley, 2024](https://arxiv.org/abs/2404.13069) investigates scribal behaviour
around drawing interruptions. Simply finding unusual glyphs there would repeat
known work. Our extension tests transport of a learned terminal predictor and
then compares like stem/context combinations; that latter test is inconclusive.

[Rozanova and Temerev, 2026](https://arxiv.org/abs/2608.17096) examine token edges,
separator classes and coordinate evidence. We reuse their public data and do
not claim that coordinate validation or the uncertain-space distinction is new.
Our additions are the crossed prediction design, revised hidden-cut selection,
and conditional prediction using token start position. This is a methodological
and empirical extension relative to the work checked, not an established claim
of priority over all Voynich research. The 2026 source is an arXiv preprint.

## What should follow from these results

1. **Prioritize the short-stem Currier B effect.** Freeze the present models and
   test the effect under another transcription and an independent glyph
   segmentation. Also hold out entire stem families, not just exact strings.
   This is more discriminating than adding another flexible model to the same
   data or pursuing a universal sandhi account.
2. **Improve the physical exposure measurement.** Blindly annotate the next
   obstacle or writing-region edge before examining terminal outcomes. Compare
   repeated stem/context combinations with different available space. The
   current start-coordinate null identifies a limitation of the proxy, not a
   reason to abandon layout research.
3. **Keep hidden segmentation as a hypothesis test.** The accuracy gain survives
   improved selection, but probability calibration and cut validity remain open.
   Require agreement across independent transcriptions and alternatives to the
   frequency-based candidate generator before using those cuts downstream as
   linguistic units.

These are next-stage proposals, not experiments claimed completed in this run.

## Reproducibility and deviations

`code/06_boundary_frontier.py` contains the primary analysis;
`code/07_boundary_robustness.py` contains post-result subgroup, shared-model,
matched-support and crossed-layout checks. All predictions, split assignments,
source hashes, alignment counts and summaries are saved. Dependencies are added
to the existing uv project and lockfile. Seven focused tests cover uncertainty
handling, metadata changes, physical folio grouping, title/paragraph boundaries,
terminal-feature leakage, pooled cut selection and deterministic folds.

The local prospective protocol was written before the new model fits, but was
not externally preregistered. After an initial run, inspection identified the
inline hand switch on f115r; the parser was corrected and all primary results
rerun. The additional analyses are labeled exploratory rather than silently
replacing the prespecified result. No parameter search was performed.

The protocol calls the pinned upstream SHA a “commit”; GitHub's tree API in fact
returned a **Git tree object**. The frozen protocol is preserved, and this
terminology correction is recorded here and in data provenance. Input contents
remain pinned, with individual SHA-256 hashes in the supplement manifest.

Run commands are in `code/README.md`. Typical full execution:

```bash
uv sync --locked
uv run --locked python code/fetch_frontier_coordinates.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --locked python code/06_boundary_frontier.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --locked python code/07_boundary_robustness.py
uv run --locked python -m unittest discover -s code -p 'test_boundary_frontier.py' -v
```
