# Framework pilot results — 30 September 2026

These are engineering runs made while developing the framework, without
predeclared success thresholds. No Voynich text was searched.

Accuracy is one minus normalized Levenshtein distance to normalized plaintext,
including spaces. For preserved-spacing controls some characters are therefore
known in advance. Scores are exploratory best-path costs plus a key-description
surrogate, divided by non-space input characters. Compare controls within a
fixed configuration, not raw scores between architectures or languages.

Each positive is one synthetic key on one development passage. The LM trains on
the first 70% of the source, then a 50-word gap separates it from development and
evaluation passages. This is within-source, not cross-genre, validation. Latin
and Italian narrative/poetic source suitability remains a limitation.

| Run | Control | Key evaluations | Development accuracy | Frozen-key evaluation accuracy | Score/input symbol |
|---|---|---:|---:|---|---:|
| italian_glyph_controls | positive | 8,004 | 99.0% | Unseen symbols: incomplete coverage | 3.721 |
| italian_glyph_controls | shuffled | 8,004 | — | Unseen symbols: incomplete coverage | 7.790 |
| italian_glyph_controls | assembly | 8,004 | — | Unseen symbols: incomplete coverage | 7.871 |
| italian_glyph_controls | mismatched | 8,004 | — | Unseen symbols: incomplete coverage | 7.292 |
| italian_groups_smoke | positive | 242 | 0.0% | Unseen symbols: incomplete coverage | 9.836 |
| italian_mixed_smoke | positive | 242 | 0.0% | Unseen symbols: incomplete coverage | 9.748 |
| latin_glyph_controls | positive | 8,004 | 100.0% | 100.0% | 3.019 |
| latin_glyph_controls | shuffled | 8,004 | — | — | 7.883 |
| latin_glyph_controls | assembly | 8,004 | — | — | 7.843 |
| latin_glyph_controls | mismatched | 8,004 | — | 24.5% | 7.072 |
| latin_homophonic_recovery | positive | 8,004 | 87.0% | Unseen symbols: incomplete coverage | 5.879 |

## Interpretation

- Latin simple substitution was recovered exactly on development and on a second
  passage using the frozen key. The equally optimized shuffled, iid assembly and
  block-transposed controls had substantially worse development scores. This is
  an existence demonstration on one fixture, not a calibrated rejection rule.
- Italian simple substitution reached approximately 99% development accuracy.
  Two-homophone Latin reached approximately 87%. Their evaluation passages
  introduced symbols absent from the development key, so full decoding was
  explicitly refused rather than assigning new meanings from the evaluation text.
- Group/mixed runs were small execution checks (120 proposals per restart), not
  successful recoveries. Their recorded search-space checks show that the oracle
  keys are not fully contained in the bounded candidate inventory/budget. Thus
  these are not clean estimates of in-family optimizer power. They cannot justify
  excluding either cipher family.
- Known-key round-trip tests pass for all three mechanisms. Recovering an unknown
  key is a separate, harder test; it remains weak for the more flexible models.

The JSON files retain full settings, source/code hashes, seeds, candidate keys,
plaintexts, segmentation paths, restarts and frozen evaluation results. Some
pilots predate small subsequent implementation changes; their implementation
hashes record exactly that distinction. A fresh run is needed for a confirmatory
comparison under one frozen implementation.

Next: improve and calibrate homophone/group search, handle unseen codes without
optimistic omission, and evaluate more independent texts and keys before a
million-evaluation Voynich experiment.
