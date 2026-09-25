# Prospective robustness gate and mechanism benchmark

24 September 2026. Written before fitting this stage; prior frontier results are
already known. This is a local protocol, not an external preregistration or an
untouched-manuscript confirmation. Preserve scripts 01–07 and their results.

## Robustness gate

Reuse the fixed C=1 baseline/context comparison, clean P0 parser and physical
folio folds from the frontier study. Define spelling families BEFORE outcomes:
strip optional initial q and then optional o, retaining an explicit empty core;
collapse repeated e and i within the remaining stem. This is an operational
spelling family, not a proposed morpheme. Train outside both the test folio fold
and test spelling-family fold. Assert disjointness. Five by five crossed folds.

Run ZL with original compound glyphs, literal EVA characters, and additional ee/
ii grouping within stems; run Takahashi IT2a with original compounds. Do not use
lossy v101-to-EVA conversion. Additionally remove the five most frequent families
from BOTH training and test, ranked on each training-folio corpus before removing
the test-family fold. Report coverage. Also score the subset of ZL/IT matching
page+locus IDs as a coverage sensitivity (not a word-for-word alignment).

Primary: paired log-loss gain, bits/terminal, on ordinary spaces. Report accuracy,
folio and spelling-family cluster bootstrap intervals, and A/B subgroup results.
Intervals condition on fitted models. No hyperparameter selection against these
results. Failure on family exclusion, measurement changes or dominant-family
removal downgrades the claim of broad transfer; no requirement to achieve a
positive result before proceeding with the methodological benchmark.

## Mechanisms and calibration

Build three explicit, limited candidate mechanisms; none represents all possible
ciphers, languages or pseudotexts:

* Assembly: smoothed within-token glyph Markov assembly mixed with resampling
  training tokens. No underlying message.
* Copy/edit: local self-copying, finite backward window, with edit/innovation
  probabilities. This is our simple implementation, not an exact implementation
  of Timm and Schinner.
* Encoding: published Naibbe code tables applied to normalized Latin/Italian
  letters grouped into one/two-letter units. Restrict to uniquely decodable
  outputs and verify exact round trips. Weighted independent table alternatives
  are an adaptation, not the published card-deck implementation. Keep ciphertext
  unit spaces. Never label a noninvertible construction a reversible cipher.

Use Currier B clean body text for the benchmark. Original folio folds 0–2 provide
the fitted assembly vocabulary/grammar and calibration targets; folds 3–4 provide
evaluation templates and Voynich observations. No test tokens enter generators.
Report that the manuscript was examined in the previous stage, so these are
locked computational holdouts, not historically blind data.

Each family receives a bounded parameter grid. Calibrate on token length mean/
variation, type/token ratio, singleton-type proportion, within-token conditional
glyph entropy and ordinary-space edge mutual information. Fixed numerical scales
are declared in code before running. Permit all three an optional first-glyph
reweighting based on the previous terminal, learned from ordinary spaces only.
This gives competitors access to the observed boundary dependence instead of
rejecting weak versions that omit it. Record model-specific fit failures.

Do not fit length-stratified edge dependence, repeated-word lag curves, or line/
paragraph contrasts. Generate continuous token streams, then apply observed
layout templates without resets; layout counts are conditioned on and are not
predictions. Never credit a model for a layout effect explicitly built into it.

## Recovery before interpretation

Generate multiple corpora from all candidate families with different seeds and
parameter settings. Separate calibration candidates/seeds from evaluation seeds.
Use withheld diagnostic features ONLY for the primary recovery classifier, not
the calibration features or raw glyph frequencies. Group classifier validation
by parameter configuration, not random rows. Repeat with Latin and Italian
plaintext sources held apart for the encoder, report this separately. Generated
sample length matches the evaluation template; additionally report a manuscript-
scale synthetic recovery check if that template is substantially smaller.

Use fixed standardized nearest-centroid classification, balanced class counts,
and confusion matrices. Report both closed-set accuracy and rejection of samples
far from the training simulations. A forced nearest class for Voynich is not a
mechanism identification. Rejection thresholds come from synthetic training
distances; make no posterior-probability interpretation of distances.

Primary withheld diagnostics: terminal/next-initial MI by short/long left stems;
exact-token repetition at lags 1, 2, 4, 8 and 16; normalized glyph edit similarity
at those lags; edge MI across physical line transitions versus ordinary spaces.
Use equal-sized comparisons or shuffled corrections where sample-size bias is
material, and disclose low-count boundary cells. Run the crossed-family predictor
on representative best-calibrated simulations as an additional, expensive check.

The useful outcomes include: a mechanism fails a held-out prediction; several
mechanisms remain indistinguishable; or all candidates are inadequate. Only
supported code-level mechanisms may be rejected, not their entire broad class.

## Outputs and checks

Save input hashes, versions, splits, grids, calibration scores, simulation seeds,
feature tables, confusion matrices and representative generated texts. Tests
must cover family exclusion, no invalid-neighbour bridging, deterministic
generation, encoder inversion, and separation of calibration/diagnostic fields.
Record implementation deviations and post-result analyses explicitly.
