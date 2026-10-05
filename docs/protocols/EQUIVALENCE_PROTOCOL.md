# Latent equivalence-class recovery (CONTINUATION §19): prospective protocol

Written 25 September 2026, before fitting any model in this stage. Known beforehand:

* the context-only Naibbe baseline (AUC 0.748, reconstructed exactly in
  `RECONSTRUCTION_FINDINGS_2026-09-25.md`);
* label purity (every frequent Naibbe type maps to one plaintext unit in at least
  95% of its tokens);
* the class count and prevalence (61 classes, 298 of 15,753 pairs positive);
* Naibbe lines average 33 tokens, Voynich lines about 8.5.

This is a local protocol, not an external preregistration.

## Question

Can ciphertext-only evidence tell whether two frequent cipher types encode the
same hidden plaintext unit, in a cipher where the answer is known? If so, what
does the unchanged model say about Voynich? Does that output differ from what
it says about text generated with no hidden units at all?

## Units and labels

Units are word types with frequency ≥20 in their own corpus. Tokens `?` are
excluded, and contexts never bridge a missing reading.

* **Naibbe:** pre-respacing ciphertext `data/naibbe_cipher_pre.txt`, with 178
  types. The label is the type's majority plaintext unit from
  `naibbe_plain_units.txt`. It is used only as the target, never as a feature.
* **Transfer targets:** new invertible encodings produced with
  `mechanism_models.Encoder` (published Naibbe tables with independent weighted
  alternatives, level 1, no coupling, seed 20260925). Labels come from exact
  decoding. Both share the Naibbe tables with the training cipher, so they test
  within-family transfer and are not an independent cipher family.
  * **Primary:** the Latin Alfonsi text (`data/latin_alfonsi.txt`), 34,764
    tokens, cut into lines copying Naibbe's line-length sequence. It differs from
    the training cipher in plaintext work and sampling procedure, but is the same
    language.
  * **Secondary, different language:** Italian Dante in one pass without
    wrapping, about 15,000 tokens, same line cutting. The cleaned text is only
    24,009 letters, too short for a full-size run. (Amended before fitting;
    the first draft specified a 34,764-token Dante run, which would have wrapped.)

## Features (pairwise, symmetric, fixed before fitting)

Each corpus is processed identically from its own token lines. Context
distributions use within-line neighbours, with `^`/`$` for line edges and a
corpus-specific top-200 neighbour vocabulary plus a catch-all dimension.

* **Context:**
  * cosine of the combined left+right vector (the 0.748 baseline construction);
  * separate left and right cosines, each with and without the catch-all
    dimension;
  * Jensen–Shannon divergence between the pair's following-initial-glyph
    distributions, and between their preceding-final-glyph distributions.
* **Frequency:** log of the smaller frequency, log of the larger, and the
  absolute log ratio.
* **Form (EVA glyph units):**
  * edit distance, raw and normalized by the longer length;
  * absolute length difference;
  * common prefix and common suffix lengths;
  * same first unit, same first two units;
  * same remainder after one unit, same remainder after two units;
  * same final unit;
  * "terminal alternation": both end in n/l/r/m with the same stem.
* **Position (sensitivity only):** absolute differences in line-initial and
  line-final rates. These are excluded from the primary model because line
  lengths differ about fourfold between Naibbe and Voynich.

## Models, validation and metrics

* **Primary:** standardized L2 logistic regression, C=1, on context, frequency
  and form features.
* **Secondary:** HistGradientBoosting with max_iter 200, learning_rate 0.05,
  max_leaf_nodes 15, l2 regularization 1.0 and random_state 20260925.
* **Baseline:** the unfitted combined-context cosine.
* No hyperparameter search.

Two grouped 5-fold designs, with seeded shuffled assignment (seed 20260925):

* **Type-held-out (primary):** types are assigned to folds. A pair is tested in
  fold k when both its types are in k, and trained when neither is. This matches
  the Voynich situation, where every type is unseen.
* **Class-held-out (stricter):** plaintext classes are assigned to folds; the
  same both-in and neither-in rule applies. The model never sees another member
  of a test type's class.

Metrics on pooled out-of-fold predictions:

* ROC-AUC and PR-AUC, with prevalence reported;
* recall at precision 0.5 and 0.8, and precision at recall 0.25 and 0.5;
* Brier score, and a 10-bin reliability table;
* per-type nearest-neighbour and top-5 retrieval, comparable to the 32.9% /
  47.4% baseline.

Intervals come from 500 type-cluster bootstraps: resample types, and weight
pairs by the product of multiplicities. They condition on the fitted fold
models. Also reported are fold ranges and ablations for each feature group
alone and all-minus-each.

**Success criterion (from §19):** "substantially higher" than context alone.
Operationally, the primary model's class-held-out ROC-AUC bootstrap interval
must lie above the baseline's point estimate, **and** PR-AUC must at least
double the baseline's. Failing this still allows a report, but the Voynich
output is then labelled uninformative.

## Clustering

Within each held-out fold, average-linkage agglomeration on 1 − p, cut at
p = 0.5. Scored by pairwise precision/recall/F1 and adjusted Rand index against
true classes, next to the same procedure applied to the baseline cosine.

## Frozen model and application

The primary and secondary models are refitted on all Naibbe pairs and then frozen.
They are scored on:

1. **Dante transfer target:** the same metrics as above, with labels.
2. **Voynich ZL3b:** all P lines, original parser.
3. **Voynich Takahashi IT2a:** same parser. Stability is measured as the Spearman
   correlation over type pairs present in both transcriptions and the overlap of
   the top-100 pairs.
4. **Message-free controls:** the saved assembly and copy/edit representative
   simulations from `results/mechanisms_2026-09-24/`. These are layout-matched
   Currier-B-calibrated streams with no hidden units.
5. **Context-destroyed Voynich:** ZL tokens globally shuffled, seed 20260925, so
   that only form and frequency evidence remains.

For each corpus, report the number of pairs with p ≥ 0.5 and p ≥ 0.8, pairs per
type, and the size distribution of clusters at p = 0.5.

## Interpretation rules (fixed now)

* Voynich candidate classes count as evidence of hidden equivalence structure
  only if both of the following hold:
  * Voynich's high-probability pair rate clearly exceeds **both** message-free
    controls and the context-destroyed Voynich;
  * the top pairs are stable across the two transcriptions.
* Otherwise the output is described as form/context similarity clusters. They
  are still useful as hypotheses, but carry no evidential weight for homophony.
* No semantic label is assigned to any class.
* Terminals are never stripped, so r/l/n/m distinctions stay in the units. OK/OT
  is not merged by rule. The OKO/OTO pair probability and the mean probability of
  same-stem r/l pairs are reported as descriptive checks.
* A good Naibbe score shows that the method can work on a Naibbe-family cipher.
  It does not show that Voynich is such a cipher.

## Outputs

`results/equivalence_2026-09-25/`, containing:

* `naibbe_cv.json`, `transfer.json`, `application.json`;
* `voynich_candidate_pairs.csv`, `voynich_candidate_clusters.json`;
* `manifest.json` (hashes, seeds, feature list, versions).

Any deviation from this protocol will be recorded in the findings.
