# Post hoc pooling diagnostic — 9 October 2026

The frozen study's glyph-shuffle controls had all-type within-section excess
MI -0.0003 to 0.0116, yet top-200 excess 0.1650–0.2015. This motivates the
following diagnostic; it is not an independent confirmation or replacement run.

`Counter.most_common(200)` breaks equal-frequency ties by first occurrence.
With page-contiguous input this favours early pages, particularly when the
cutoff includes singletons. A fixed pooled vocabulary is then retained during
permutations, which do not repeat that selection procedure. The statistic can
therefore carry page information introduced by its own preprocessing.

Run the eight existing manuscript/control panels with frequency ties resolved
by SHA-256 of seed plus token identity, seeds 7/19/31. Hash ranking is independent
of token positions; it is not claimed to be an optimal estimator. Retain all-type
primary results and the original pooling results unchanged. Add a 1,024-distinct-
token example under the same layout to isolate the artifact. Use 199 permutations
per condition, section and section+roles; no cipher search. No historical stage
rerun or retrospective family reclassification from this diagnostic alone.
Future pooled comparisons must avoid page-order tie selection or rerun the
complete selection procedure inside their null, with appropriate calibration.
