# Voynich: which words carry the page signal?

Stage 29, 9 October 2026. Evidence label: descriptive structural diagnostic. No plaintext has been recovered and no cipher family is rejected here. Page-associated vocabulary also appears in Currier A. In these matched herbal samples it is weaker than in B. In B most measured association belongs to types appearing at least five times in the panel. A model concerned only with rare ingredient names would therefore miss much of the pattern it needs to explain.

## The manuscript comparison

Sixteen distinct herbal folios per Currier group, 64 clean tokens per page. Classifications come from ZL. IT2a is matched by page, not by individual glyph. Split and joined doubtful-space arms use their own first 64 clean tokens. Values are bits per apparent token above a within-section permutation baseline; the second column also conditions on line/paragraph roles. They are not percentages decrypted.

| Panel | Section excess | Role excess | Count 2–4 contribution | Count ≥5 contribution |
| --- | --- | --- | --- | --- |
| A_ZL_split_full | 0.0783 | 0.0485 | 0.0277 | 0.0506 |
| A_ZL_join_full | 0.0644 | 0.0393 | 0.0235 | 0.0409 |
| A_IT_split_full | 0.0936 | 0.0502 | 0.0498 | 0.0438 |
| A_IT_join_full | 0.0936 | 0.0502 | 0.0498 | 0.0438 |
| B_ZL_split_full | 0.1349 | 0.0977 | 0.0164 | 0.1185 |
| B_ZL_join_full | 0.1481 | 0.1102 | 0.0368 | 0.1113 |
| B_IT_split_full | 0.1321 | 0.0935 | 0.0255 | 0.1066 |
| B_IT_join_full | 0.1321 | 0.0935 | 0.0255 | 0.1066 |

Every first-eight and last-eight panel has positive excess under both conditionings in both transcriptions and spacing arms. This is directional replication under a fixed sampling rule, not a calibrated significance or family-acceptance claim. The A/B magnitude contrast may also reflect scribes, material and sampled pages. IT split/join outputs coincide on these selected spans; those arms are not independent confirmations.

| Half-panel | Section excess | Role excess |
| --- | --- | --- |
| A_ZL_split_early | 0.0673 | 0.0234 |
| A_ZL_split_late | 0.0707 | 0.0661 |
| B_ZL_split_early | 0.1147 | 0.0856 |
| B_ZL_split_late | 0.1142 | 0.0890 |

## Frequency is not meaning

Each type is assigned by its total panel count: once, 2–4 times, or at least five times. Each group contributes to the same overall score; we do not recompute MI on a filtered subset. All contributions and token masses are in evidence.json. There is no rank cutoff or tie-breaking. These frequency bins stay unchanged under the null permutations, eliminating the earlier position-dependent selection artifact.

Types with ≥5 occurrences account for 87.9% of section excess in the full B herbal panel and 89.5% in the earlier herbal/biological panel. This is a share of a corrected statistic, not a share of semantic content. The ≥5 bin is broad: repeated content words can belong to it, and we have not identified function words. A lower relative rare-bin contribution does not demonstrate a page-state mechanism.

A singleton has no repeat with which to estimate a page preference. With equal-size pages its corrected contribution is exactly zero. It could still be a perfectly meaningful plant name. The statistic cannot answer that question. After role conditioning unequal margins can alter the zero identity; inspect the stored decomposition.

## Comparison with the frozen source passages

These are the twelve existing stage-28 plaintext panels, not newly selected best fits. Recipe and medical texts also place some association in frequent types. Their variation cautions against inferring genre from the aggregate manuscript profile. No source/function-word lexicon or semantic classifier was introduced.

| Passage | Section excess | 2–4 contribution | ≥5 contribution |
| --- | --- | --- | --- |
| cucina_development_7 | 0.0624 | 0.0392 | 0.0232 |
| cucina_development_19 | 0.0638 | 0.0318 | 0.0320 |
| cucina_validation_31 | 0.0916 | 0.0387 | 0.0529 |
| cucina_validation_43 | 0.0650 | 0.0225 | 0.0425 |
| celsus_development_7 | 0.0912 | 0.0472 | 0.0440 |
| celsus_development_19 | 0.1384 | 0.0464 | 0.0919 |
| celsus_validation_31 | 0.0830 | 0.0400 | 0.0430 |
| celsus_validation_43 | 0.0969 | 0.0618 | 0.0351 |
| pliny_development_7 | 0.0599 | 0.0411 | 0.0189 |
| pliny_development_19 | 0.0375 | 0.0274 | 0.0101 |
| pliny_validation_31 | 0.0191 | 0.0042 | 0.0149 |
| pliny_validation_43 | 0.0294 | 0.0244 | 0.0050 |

## What changes next

Retain word/mixed codes as open hypotheses. Give common recurring types an explicit role in the next model, and keep A/B separate. Before fitting persistent choices, construct a bounded glyph-slot codebook, count unique outputs and collisions, and compare it with R2 on frozen pages. Round-trip recovery is a necessary engineering check; it is not manuscript evidence. Neither shuffle sensitivity nor a page-association match alone distinguishes language from a sequential message-free generator.

[Decisions for the next codebook study](../../docs/guides/CONTEXT_CODEBOOK_GUARDRAILS.md)

The suggested 1,500–4,500-entry codebook around 1420 is not established here. The historical survey and the limitation of its size categories are recorded separately; large-key simulations must remain explicitly unattested at that date.

[Historical source check](../../data/historical_cipher_sources/README.md)

## Calibration, uncertainty and reproduction

The 50 IID calibration panels averaged 0.001070 excess bits; ten planted rare-repeat panels averaged 1.819782. All gates passed before manuscript metrics. Additivity against the established scalar estimator, bijective renaming and the all-unique control passed. The ten planted cases vary null seeds, not the planted signal. No synthetic solver accuracy is being claimed.

199 permutations per measurement, seed 2901. Stored null SDs, quantiles and Monte Carlo SEs describe permutation variability only, not manuscript sampling uncertainty. The new seed produces small differences from stage 28; historical outputs were not changed. Eight-page halves also change type counts and bin membership, so they are sensitivity panels, not additive pieces of the full-panel decomposition.

Protocol committed at 3d4bdfc before execution. No protocol deviations or post hoc parameter changes. This stage fits no keys or generators. R2 comparison, glyph-slot construction and expanded manual label alignment remain upcoming work, not completed tests.

| Currier group | Selected herbal pages |
| --- | --- |
| A | f1v, f2r, f3r, f4v, f6r, f7v, f8r, f9r, f10r, f13r, f14r, f15r, f16r, f17r, f18r, f19r |
| B | f26r, f31r, f33r, f34r, f39r, f40r, f41r, f43r, f46r, f48r, f50r, f55r, f57r, f66v, f94r, f95r1 |

[Frozen protocol](../../docs/protocols/FREQUENCY_CURRIER_A_2026-10-09.md)

[Machine-readable evidence](evidence.json)

[Exact slots](slots.json)

[Source and environment manifest](manifest.json)

All 215 software tests passed, including the separate PostgreSQL test database. Source and wheel builds passed; the CLI lists stages 01–29. Verification against the independent scalar estimator checks all 82 manuscript/reference totals, frequency additivity, manifest hashes and half-panel folio disjointness.

[Verification output](verification.json)

Reproduce into a new directory: uv run --locked python -m voynich.experiments.e29_frequency_currier_a --output results/<new-dir>; then uv run --locked python -m voynich.laboratory.frequency_report --directory results/<new-dir>.

Verify: uv run --locked python -m voynich.laboratory.frequency_verify --directory results/<new-dir>.
