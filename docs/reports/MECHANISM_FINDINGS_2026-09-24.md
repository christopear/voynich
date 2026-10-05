# Robustness and mechanism experiments: findings

24 September 2026. Continuation of the boundary/layout work, with the earlier
code and results preserved. Specification: `MECHANISM_PROTOCOL.md`. Results,
per-observation predictions, simulation features, seeds and hashes are in
`results/mechanisms_2026-09-24/`.

## Main finding

This round strengthens the **narrow Currier B boundary result**, while reducing
the justification for interpreting that result as evidence of meaningful
language or a particular cipher. The predictive benefit survives a broader
spelling-family holdout, another transcription, three glyph representations,
and removal of the five most frequent families. Yet a generator with no input
message also reproduces a positive unseen-family benefit.

The mechanism benchmark distinguishes some synthetic cases but does not support
an attribution of Voynich to a mechanism. Recovery depends strongly on the
classifier, and the rejection rule accepts mixtures outside the three pure
training labels. The best-calibrated versions of the three generators also miss
important parts of the manuscript's combination of vocabulary richness and
local repetition.

These are new tests of generalization and specificity. They do not identify a
language, translate text, or establish that the manuscript is meaningless.

## 1. The robustness gate

The new holdout removes a whole operational spelling family from training, as
well as both sides of the physical test folio. Families remove an optional q
then optional o at the start, and collapse repeated e/i within the remaining
stem. This groups, for example, qokaii, okai and kai. It is one explicitly
defined family hypothesis, not a claim to know the manuscript's morphology or
a test of every possible family grouping.

The original fixed logistic models and physical folio assignments remain in
use. There are 25 crossed fold combinations per specification. Glyph changes
affect the stem features and next-initial representation; the n/l/r target is
held fixed. No model tuning was performed against these outcomes.

Positive gain means lower held-out log loss, in bits per terminal. Intervals are
95% paired percentile bootstrap intervals, clustering by folio or spelling
family separately. They condition on fitted models and are not a full two-way
or refitted-model bootstrap.

| Currier B test | N | Gain, bits | Folio interval | Spelling-family interval |
|---|---:|---:|---:|---:|
| ZL, original compound glyphs | 8,013 | +0.02805 | +0.01705 to +0.03866 | +0.00861 to +0.05251 |
| ZL, literal EVA characters | 8,013 | +0.02790 | +0.01812 to +0.03828 | +0.00887 to +0.05134 |
| ZL, additional ee/ii grouping | 8,013 | +0.02777 | +0.01610 to +0.03891 | +0.00876 to +0.05199 |
| Takahashi IT transcription | 9,198 | +0.03619 | +0.02415 to +0.04706 | +0.01391 to +0.06076 |
| ZL, remove top five families | 5,145 | +0.02436 | +0.00705 to +0.04175 | +0.00256 to +0.04714 |

In the first row, accuracy increases from 73.99% to 76.19%. After dropping the
five families, it increases from 68.53% to 71.70%. The excluded families are the
empty stripped core, ai, dai, ka and kai; they were ranked on training folios,
and happened to be the same five in every folio fold. Exclusion applies to both
training and evaluation, not merely removal of difficult test cases afterward.

Currier A is inconclusive under every specification. Whole-manuscript gains are
+0.01419, +0.01876, +0.01302 and +0.02089 bits for the first four specifications;
most whole-manuscript family-clustered intervals include zero. Removing the five
families leaves +0.00904 bits overall, also inconclusive. The appropriately
restricted conclusion is therefore about Currier B, not universal Voynichese.

The direct alternative transcription is the older Takahashi reading extracted
from the Landini–Stolfi interlinear file, in IVTFF/EVA format. The origin refused
the download client, so we used a commit-pinned public mirror with the version
2a, 2 February 2023 header. The current origin carries a later modification
note. This distinction and all hashes are recorded in `data/mechanisms/`.

The files differ in token readings and space judgments, so the sample sizes
differ. Restriction to common page/locus IDs leaves nearly identical aggregate
gains, but this is not a token-for-token alignment. It does not isolate glyph
reading changes from separator changes. Another transcription supplies a
measurement sensitivity check, not an independent manuscript sample. The v101
file was inspected but not converted into EVA without a validated mapping.

## 2. Three specified mechanisms

The benchmark uses Currier B P0 body text. The previously fixed physical folio
folds 0–2 supply 11,836 clean training tokens on 23 folios; folds 3–4 supply
10,017 clean evaluation tokens on 17 folios. These are locked computational
holdouts, but the manuscript had already been examined in the earlier stage.
They must not be described as historically blind new evidence.

The models are deliberately explicit and limited:

* **Assembly:** second-order within-token glyph generation with backoff, mixed
  with resampling training tokens. Lexical mixture weights are 0, 0.5 and 0.9.
  There is no plaintext to encode.
* **Copy/edit:** 20% fresh lexical innovation; otherwise copy from a recent
  backward window, with an optional insertion, deletion or substitution. The
  paired window/mutation settings are (8, 0.15), (32, 0.35), (128, 0.60). This is
  our small copying model, not a reproduction of Timm–Schinner's implementation.
* **Reversible encoding:** normalized Latin or Italian letters grouped into
  one/two-letter units, using Greshko's published Naibbe tables. Independent
  weighted alternatives replace the published card deck. Single-letter
  probabilities are 0.35, 0.50, 0.65, paired with table-weight powers 0.5, 1, 2.
  Unigram strings are reserved first, and ambiguous remaining bigram strings
  are excluded. Every generated unit is exactly invertible. Unit spaces are
  retained; this is not a test of arbitrary space deletion or lost boundaries.

All models receive either no cross-token coupling or the same bounded
first-glyph selection opportunity, learned from training ordinary spaces. Six
proposals are sampled and reweighted by the previous terminal/next initial
association. Thus a copying or assembly model is allowed to learn the observed
boundary statistic rather than being rejected for omitting it by construction.

Calibration uses six quantities: token length mean and deviation, type/token
ratio, singleton-type proportion, within-token conditional glyph entropy and
ordinary-space n/l/r edge MI. Fixed scaling constants are in the source and
manifest. There are six configurations per mechanism, two calibration seeds
each. These scores are scaled discrepancies, not likelihoods or probabilities
of the hypotheses. Best mean discrepancies are assembly 0.916, encoding 1.465,
copy/edit 5.877. The copy model already fits the calibration targets poorly.

Generated streams are continuous, then placed in observed layout templates.
They receive the numbers and positions of slots, missing readings and gaps, but
not the test words. They have no special line-reset rule. Layout counts are
conditioned on and cannot be claimed as predictions.

## 3. The boundary effect is not specific to a message-bearing mechanism

An additional family/folio holdout was run on one independent full-size
simulation from each best-calibrated configuration:

| Generator | Eligible terminals | Family-holdout gain, bits | Family interval |
|---|---:|---:|---:|
| Assembly, no input message | 10,697 | +0.02847 | +0.01393 to +0.04403 |
| Copy/edit, no input message | 10,944 | +0.06303 | +0.03439 to +0.09476 |
| Reversible encoding | 12,092 | +0.01065 | −0.00826 to +0.03252 |

The important point is the constructive counterexample: a message-free process
can pass this generalization test. It was allowed to fit ordinary boundary
dependence, but was not fitted to the family-holdout score. This demonstrates
that transfer of the association does not, by itself, establish phonology,
semantics or a cipher.

These are one-seed representatives, with uncertainty over their observations,
not over generator seeds. They use whole-manuscript layout templates, whereas
the real-data robustness conclusion above is strongest in B. Similar numerical
gains are not a formal equality test or a claim of a full statistical match.
The weaker encoding result cannot reject the broad cipher hypothesis.

## 4. Recovery of known generators

We generated 108 evaluation-size corpora: three mechanisms, three parameter
levels, two coupling settings, two plaintext-source assignments, three seeds.
Each has 10,277 token slots. A second set contains 36 simulations at 33,970
slots, matching the full manuscript body template, with one seed per
mechanism/level/coupling/source cell. Assembly and copying do not consume the
plaintext; source assignments for them select separate simulation seeds.

Recovery uses only withheld features, not the six calibration targets or raw
glyph frequencies: the short-minus-long stem edge-MI contrast, line-minus-
ordinary edge MI, and repetition/edit-similarity excesses at lags 1, 2, 4, 8, 16.
MI subtracts within-page shuffled values. Lag comparisons stay within pages and
do not bridge illegible tokens. Edit similarity samples up to 512 pairs per lag.
Shuffled MI correction does not eliminate every finite-sample bias; line cells
are small and empirical comparisons use the same measurement pipeline.

The primary recovery test leaves out an entire parameter level across all
mechanisms. It therefore tests extrapolation beyond exact simulated parameter
settings, not merely a new random seed. Balanced chance accuracy is 33.3%.

| Classifier | Evaluation-size accuracy | Manuscript-size accuracy | Status |
|---|---:|---:|---|
| Standardized nearest centroid | 45.4% (49/108) | 41.7% (15/36) | Prespecified |
| Three nearest neighbours | 49.1% (53/108) | 44.4% (16/36) | Exploratory |
| Fixed random forest | 76.9% (83/108) | 80.6% (29/36) | Exploratory |

The two additional classifiers were selected after the primary result, to check
whether poor recovery was a property of the diagnostic features or of the
linear centroid rule. Neither was tuned. The forest has 300 trees, minimum leaf
size 2 and a fixed seed. These results show that the diagnostics contain useful
nonlinear information; they do not establish reliable attribution to an
unknown mechanism. An information-theoretic impossibility claim would be
unwarranted.

For the evaluation-size forest, the confusion matrix is:

| Actual source | Predicted assembly | Predicted copy/edit | Predicted encoding |
|---|---:|---:|---:|
| Assembly | 34 | 0 | 2 |
| Copy/edit | 12 | 24 | 0 |
| Encoding | 10 | 1 | 25 |

The primary centroid classifier's separate Latin→Italian and Italian→Latin
source-holdout test achieves 55.6% at evaluation size and 52.8% at manuscript
size. This holds the source work apart, but not simultaneously the parameter
level. Two plaintext works and a small parameter grid cannot establish recovery
over the full space of languages, texts or mechanisms.

## 5. Rejection and omitted mechanisms

The prespecified rejection rule compares standardized diagnostic distances with
the 95th percentile of same-class training simulation distances. Under withheld
parameter validation it rejects 13.0% of known-class evaluation samples and
13.9% at manuscript scale. This is an empirical distance rule, not a calibrated
posterior or a guaranteed out-of-distribution test.

For Voynich, this rule accepts assembly and copy/edit, while the closest centroid
is assembly. **This is not reported as a mechanism identification.** The rule's
training class envelopes can be broad, and it uses the entire parameter grid,
not only the best-calibrated configuration.

We then added an explicitly exploratory challenge: 12 streams formed by mixing
assembly and encoding in blocks of 8 or 64 tokens. These have no correct pure
class among the three labels. The centroid rule rejects **0/12**. The forest
assigns a pure class with a maximum score of at least 0.8 to **5/12**; these scores
are uncalibrated classifier outputs, not true mechanism probabilities. Controls
at the two block lengths share underlying seeded streams and are not 12
independent mechanism samples.

This exposes a concrete failure of the attribution workflow. Reasonable
closed-set recovery does not imply an ability to recognize a mixed or omitted
mechanism. We therefore make no inference from the nearest Voynich label.

## 6. What the best-calibrated models miss

The following are held-out measurements; simulated ranges contain six runs
across two sources and three seeds. They are observed simulation ranges, not
confidence intervals or formal rejection thresholds.

| Quantity | Voynich B holdout | Assembly range | Copy/edit range | Encoding range |
|---|---:|---:|---:|---:|
| Singleton fraction among types | 0.6785 | 0.5359–0.5583 | 0.3671–0.3938 | 0.5757–0.6139 |
| Lag-2 repetition excess | 0.00513 | −0.00047–0.00053 | 0.19687–0.22692 | −0.00042–0.00096 |
| Adjacent edit-similarity excess | 0.03971 | −0.03067–0.01390 | 0.17457–0.25123 | −0.01203–0.00319 |

Here repetition excess is the probability of an identical token pair minus its
within-page frequency baseline, not the raw repetition rate. The manuscript
combines a relatively open vocabulary with modest local recurrence. The best
assembly/encoding versions produce too little local recurrence, and the best
copy version produces far too much while having too few singleton types.

This is a more useful target for subsequent modeling than matching the boundary
statistic alone. A next model should try to reproduce **vocabulary novelty,
modest short-range recurrence and transferable edge dependence jointly**.
The present restricted copy grid fixes innovation at 20%, so its failure cannot
rule out more selective or higher-innovation copying. Likewise, the constrained
encoder is only one table-based construction, not all reversible encodings.

## Scope, provenance and limitations

The boundary/line observations themselves predate this project. This stage adds
the spelling-family and transcription gate, a constructive message-free
counterexample under the same predictive test, grouped synthetic recovery and
the mixed-mechanism rejection challenge. It does not establish priority over
all Voynich work or amount to a publishable decipherment claim.

The copying model is inspired by the general mechanism explored by
[Timm and Schinner](https://github.com/TorstenTimm/SelfCitationTextgenerator), but
their code was not used. The encoding tables and attribution are from
[Greshko's Naibbe project](https://github.com/greshko/naibbe-cipher), associated
with [Greshko (2025)](https://doi.org/10.1080/01611194.2025.2566408). The local
modified MIT license is preserved. Broader statistical model comparison is
already present in [Rozanova and Temerev (2026)](https://arxiv.org/abs/2608.17096);
we are extending a diagnostic workflow, not introducing the idea of generator
controls.

Reversibility is verified against the exact consumed normalized letter stream
for every encoding run. It does not recover original spaces, punctuation or
capitalization. The normalization follows j→i, k→c, w→uu. The existing Italian
file is short, so some evaluation and larger runs cycle their source fragment;
all wraps are recorded. Eighteen of 108 evaluation simulations and 12 of 36
large simulations contain wraps, all in the encoding family. Source cycling and
limited plaintext diversity restrict generalization claims.

The first encoder check correctly failed when reserving unigram outputs was
omitted: some letters lost all unambiguous alternatives. The implementation was
corrected to reserve unigram strings first, its full inversion checks passed,
and the benchmark was rerun. No incomplete run supplies the reported results.

No additional Python libraries were needed. Eight new tests cover spelling
families, glyph preservation, separation of calibration/diagnostic fields,
exhaustive retained-code inversion, deterministic generation, invalid-token
barriers, template length and basic statistic sanity. Actual fitting also
asserts family/folio disjointness. The prior seven tests remain in place.

## Reproduce and inspect

The primary/calibration/representative runs comprise 183 generated corpora,
followed by 12 exploratory mixture controls. Large intermediate texts are saved
for the three representatives; other runs retain seeds, corpus hashes and
feature/audit tables so they can be regenerated.

```bash
uv sync --locked
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --locked python code/08_robustness_gate.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --locked python code/09_mechanism_benchmark.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --locked python code/10_recovery_sensitivity.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --locked python code/11_mixture_controls.py
uv run --locked python -m unittest discover -s code -p 'test_*.py' -v
```

Key files: `gate_summary.json`, `benchmark_summary.json`, `calibration.json`,
`simulation_features.json`, `large_simulation_features.json`,
`recovery_sensitivity.json`, `mixture_controls.json`, and the corresponding
prediction CSVs/manifests in `results/mechanisms_2026-09-24/`.
