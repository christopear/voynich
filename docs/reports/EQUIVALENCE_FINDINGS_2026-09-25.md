# Latent equivalence-class recovery (§19): findings

25 September 2026. Specification: `EQUIVALENCE_PROTOCOL.md`, committed before any
fitting. Code: `code/equivalence.py`, `code/13_equivalence_classes.py`
(prospective) and `code/14_equivalence_posthoc.py` (post hoc). Results:
`results/equivalence_2026-09-25/`.

## Main finding

**On Naibbe-family ciphers the method works.** Ciphertext-only features predict
which cipher types encode the same plaintext unit far better than context alone.
The frozen model carries over to new plaintexts encrypted with the same tables.

**On Voynich the output does not count as evidence of hidden equivalence
classes.** Both pre-set gates fail:

* The Naibbe success criterion is only partly met.
* The Voynich output does not exceed the message-free controls in the way the
  protocol required.

The Voynich candidate groupings are therefore hypotheses about form and context
similarity. They carry no evidential weight for homophony, and no semantic
labels are assigned.

The controls' behaviour is itself informative. The model gives *many* confident
pairs to text with no hidden units (the assembly simulation, shuffled Voynich)
and *few* to Voynich. The pre-set rate comparison therefore cannot separate the
hypotheses. A different control design is needed; see below.

## 1. Naibbe calibration

* **Data:** 178 cipher types with frequency ≥20 in the pre-respacing ciphertext,
  61 plaintext classes, 298 of 15,753 pairs positive (1.9%). Label purity is at
  least 95%.
* **Features:** context, frequency and form, 21 in all (listed in the protocol).
* **Models:** a standardized logistic regression with C=1 (primary), plus
  gradient boosting.
* No tuning.

Pooled out-of-fold results. Intervals are 95% type-cluster bootstraps
conditional on the fitted fold models.

| Design | Score | ROC-AUC | PR-AUC | Recall @ precision 0.8 | Nearest-neighbour | Top-5 |
|---|---|---:|---:|---:|---:|---:|
| Type-held-out (3,080 pairs, 67 positive) | context cosine | 0.764 | 0.160 | 0.00 | 40.7% | 67.0% |
| | **logistic** | **0.944** [0.892, 0.981] | **0.542** [0.322, 0.754] | 0.21 | 68.1% | 93.4% |
| | boosting | 0.954 | 0.546 | 0.28 | 67.0% | 96.7% |
| Class-held-out (3,339 pairs, 298 positive) | context cosine | 0.745 | 0.401 | 0.16 | 56.6% | 75.0% |
| | **logistic** | **0.931** [0.894, 0.962] | **0.701** [0.600, 0.826] | 0.49 | 82.9% | 98.0% |
| | boosting | 0.939 | 0.732 | 0.57 | 84.9% | 98.7% |

In the class-held-out design the model never saw any member of a test type's
plaintext class. Fold ROC-AUCs range from 0.93 to 0.98. Calibration is good in
the type-held-out design: the top probability decile averages 0.19 predicted
against 0.17 observed. Brier scores are 0.014 and 0.046.

**Pre-set success criterion.** The criterion required two things:

* the class-held-out ROC-AUC interval above the baseline's 0.745: **met**
  (0.894–0.962);
* PR-AUC at least double the baseline's: **not met**, at 0.701 against 0.401
  (1.75×).

Under the primary type-held-out design PR-AUC more than triples (0.542 against
0.160). Post hoc: with class-held-out prevalence at 8.9%, doubling would have
meant a PR-AUC of 0.80, close to the ceiling. The criterion was fixed in advance,
though, so the protocol's consequence applies: the Voynich output is labelled
uninformative.

**Ablations** (logistic, class-held-out ROC-AUC / PR-AUC):

| Features | ROC-AUC | PR-AUC |
|---|---:|---:|
| Context only | 0.862 | 0.565 |
| Form only | 0.718 | 0.378 |
| Frequency only | 0.751 | 0.188 |
| All except context | 0.825 | 0.433 |
| All except form | 0.920 | 0.621 |
| All except frequency | 0.880 | 0.645 |
| All primary features | 0.931 | 0.701 |
| Primary + line position (sensitivity) | 0.942 | 0.734 |

Context carries most of the signal. The fitted model's context features already
beat the single-cosine baseline (0.862 against 0.745), mainly through the
no-catch-all cosines and the following-initial divergence. Form and frequency
each add precision. Line-position features help Naibbe slightly but stay out of
the primary model, as specified, because line lengths differ about fourfold
between the corpora.

**Clustering** (average linkage, cut at p = 0.5, inside held-out folds):

| Design | Pair precision | Pair recall | ARI |
|---|---:|---:|---:|
| Type-held-out | 0.77 | 0.42 | 0.53 |
| Class-held-out | 0.97 | 0.38 | 0.49 |

The clusters are conservative: merges are usually right, but most homophone
groups are only partly recovered. The baseline, a logistic calibration of the
context cosine alone, never reaches p = 0.5, so it produces no merges at this
cut.

## 2. Transfer to new labelled ciphers (frozen model)

Both targets are new invertible encodings made with the published Naibbe tables
(`mechanism_models.Encoder`, level 1). Labels come from exact decoding, and
round trips are verified.

| Target | Types / classes | Context cosine ROC-AUC | Logistic ROC-AUC | Logistic PR-AUC | Nearest-neighbour (baseline → model) | Cluster precision / recall |
|---|---|---:|---:|---:|---|---|
| Latin Alfonsi, 34,764 tokens | 152 / 48 | 0.740 | **0.945** [0.902, 0.972] | 0.601 (base 0.203) | 50.4% → 74.0% | 0.93 / 0.34 |
| Italian Dante, 14,005 tokens, no wrap | 87 / 19 | 0.692 | **0.894** [0.841, 0.934] | 0.457 (base 0.132) | 39.3% → 65.5% | 0.88 / 0.15 |

The model carries over to a different plaintext work, a different language and a
different sampling procedure. Both targets share the Naibbe code tables, so this
is **within-family** transfer, not evidence of transfer to other cipher designs.
The boosted model fits Naibbe itself almost perfectly in-sample (ROC-AUC 0.993)
but transfers no better than the logistic model. The logistic model is the more
honest summary.

## 3. Voynich application and controls (frozen primary model)

| Corpus | Types | Pairs p ≥ 0.5 | Rate p ≥ 0.5 | Rate p ≥ 0.8 |
|---|---:|---:|---:|---:|
| Voynich ZL3b | 256 | 284 | 0.87% | 0.28% |
| Voynich Takahashi IT2a | 264 | 355 | 1.02% | 0.34% |
| Naibbe (reference, in-sample) | 178 | 131 | 0.83% | 0.30% |
| Control: assembly, no message | 261 | 3,169 | **9.34%** | 2.08% |
| Control: copy/edit, no message | 332 | 307 | 0.56% | 0.25% |
| Control: Voynich tokens shuffled | 256 | 5,384 | **16.5%** | 3.88% |

**Transcription stability** is high: Spearman 0.94 over 31,375 shared pairs, and
72 of the top 100 pairs are shared. The gradient-boosting model gives the same
pattern.

**Pre-set interpretation rule.** Voynich classes would count as evidence only if
Voynich's high-probability rate clearly exceeded *both* message-free controls
*and* shuffled Voynich. It does not: it is 10–20 times *lower* than the assembly
and shuffled controls, and only slightly above copy/edit. The rule fails, so the
candidates are reported as similarity clusters only.

**Why the controls score high (post hoc, `posthoc_diagnostics.json`).** When
neighbouring tokens are unrelated to each other, every type's context
distribution tends towards the overall word-frequency distribution. Pairwise
context similarity then saturates. Median left/right cosines without the
catch-all dimension are 0.55 / 0.53 for assembly and 0.55 / 0.58 for shuffled
Voynich, against 0.23 / 0.27 for Voynich and 0.26 / 0.26 for Naibbe. The model,
trained where high context similarity means "same unit", merges the
undifferentiated types. The pre-set rate comparison therefore mostly measures
how informative context is, not whether hidden classes exist. Voynich's pairwise
context profile resembles Naibbe's much more than the context-free controls'.
That is consistent with real sequential structure, as earlier work already
showed, but it says nothing specific about homophony.

**Candidate groupings.** These are in `voynich_candidate_clusters.json` (p = 0.5)
and the top 1,000 pairs in `voynich_candidate_pairs.csv`. They are mostly
prefix, gallows or terminal neighbours:

* `okaiin/otaiin`, `okal/otal`, `okar/otar`, `okain/otain`;
* `okeey/oteey/qokeey`;
* `qokedy/qokeedy`, `qokaiin/qokain`;
* `chol/chor`, `sho/shol/shor`;
* `dain/dair/dar/dol`, `sain/sair/sal/sar/sol/sor/tar`;
* `chodaiin/odaiin/oraiin/shodaiin/taiin/ytaiin`.

**Conflicts with earlier evidence.** The earlier test (16 r/l families) found
distinct following-initial distributions for 15 r/l pairs that are also frequent
here. The frozen model merges 6 of them at p ≥ 0.5: `chol/chor`, `shol/shor`,
`dol/dor`, `lol/lor`, `sol/sor`, `sal/sar`. OK/OT same-remainder pairs get a
mean p of 0.51, with `okaiin/otaiin` at 0.95. For OKO/OTO, the one contrast where
residual context was significant, `okol/otol` scores 0.69 and `okor/otor` 0.32.

The model partly imports a Naibbe form prior. In Naibbe, OK/OT same-remainder
pairs are mostly true homophones, and the frozen coefficients reward a shared
suffix and penalize a shared final glyph. Voynich pairs that match that template
get high scores whatever their contexts show. These groupings should not be
treated as homophone classes, and terminals must not be merged on this basis.

## What this establishes, and what next

* **Established:** for a Naibbe-family verbose homophonic cipher, ciphertext-only
  pair features recover hidden equivalences well beyond context alone. The
  evidence covers held-out plaintext classes and new plaintexts in other
  languages: ROC-AUC 0.89–0.95, nearest-neighbour retrieval 66–83% against
  39–57%. This is the §19 positive control, done.
* **Not established:** that Voynich has homophone classes of this kind, or which
  forms belong together. The pre-set gates failed, and the model's Voynich
  output conflicts with established r/l evidence in 6 of 15 checked cases.

Next steps, which would each need a new protocol:

1. **Replace the rate control.** Test on a hidden-class cipher *outside* the
   Naibbe family, with known labels, whose surface statistics are calibrated to
   Voynich. Separately, inject known synthetic homophone splits into Voynich and
   measure whether the frozen model recovers them against Voynich's own context
   background.
2. **Remove the Naibbe form prior for Voynich use.** Compare the context-only
   model's Voynich candidates with the full model's. Any grouping supported only
   by form similarity should be discounted.
3. **Respect the terminal constraint by design.** Score r/l/n/m alternations
   separately, or exclude pairs that differ only in the terminal glyph, because
   independent evidence already shows those terminals are informative.

## Deviations and provenance

* **Transfer targets.** The protocol was amended *before fitting*. The Dante text
  (24,009 letters) was too short for a 34,764-token run without wrapping, so the
  Latin Alfonsi text became the primary transfer target and Dante became a
  one-pass secondary target (14,005 tokens). The protocol records this.
* **Clustering baseline.** The "same procedure applied to the baseline cosine"
  was implemented as a logistic calibration of that single feature, so the
  p = 0.5 cut is comparable across scores.
* **Voynich parsing.** Voynich corpora use the stricter `06` parser (P0 text,
  uncertain tokens as gaps). That gives 256 ZL types rather than 270 under the
  original parser.
* **Post-hoc work.** `14_equivalence_posthoc.py` was written after the results.
  It is exploratory and does not change any prospective verdict.
* **Reproducibility.** Seeds, feature lists, frozen coefficients, library
  versions and input hashes are in `manifest.json`.

```bash
OPENBLAS_NUM_THREADS=1 uv run --locked python code/13_equivalence_classes.py
OPENBLAS_NUM_THREADS=1 uv run --locked python code/14_equivalence_posthoc.py
uv run --locked python -m unittest discover -s code -p 'test_equivalence.py' -v
```
