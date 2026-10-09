# Can changing tables explain the apparent words?

**The rotating-table hypothesis remains open. This particular line-by-line test
has not produced a stable reading or consistent supporting evidence.**

[Open the report](report.html) for all original-page outputs, frozen transfers,
lexicon hits, controls and synthetic calibration.

## What we tested

One injective substitution table versus two independent tables alternating by
manuscript paragraph-text line. Both reset to phase zero at each page start. We
fit f26r and transfer unchanged keys to f31r and the additional page f39v. All are
Currier B herbal pages; none is claimed an untouched research holdout.

Compound EVA is fixed; spaces survive. Omitted uncertain words do not shift the
line clock, including when a line has no retained words. This is only one narrow
switching rule, not arbitrary rotation, per-word switching, dice choices, or
homophonic/state-dependent mixtures.

There were **24 searches / 98,304 registered evaluations**, with zero evaluator
errors: 20 manuscript/control searches and four blind synthetic calibration runs.
Each received 4,096 proposals, beam width 8. Both seeds (7 and 19) used the same
three line-shuffle realizations and one symbol-shuffle realization. Controls
receive the same extra model freedom and search budget.

Celsus supplies the search language model; Pliny scores selected outputs and
lexicon hits. A table's extra mappings incur an explicit combinatorial description
length. Scores therefore differ from the previous pilot's key-cost convention.

## What happened on Voynich

| Search seed | One-table loss | Two-table loss | Two-table advantage |
|---|---:|---:|---:|
| 7 | 6.664 | 6.550 | +0.114 |
| 19 | 6.288 | 6.522 | −0.233 |

Positive advantage is better after paying for the second table. The original-page
gain exceeds its line-shuffled counterpart in 4/6 comparisons, but that consists
of 3/3 for seed 7 and 1/3 for seed 19. These reuse two original fits and three
permutations; they are not six independent observations or a significance test.

Transfer under the independent Pliny model was inconsistent:

| Page | Seed | One-table bits/character | Two-table bits/character |
|---|---|---:|---:|
| f31r | 7 | 5.870 | 5.981 |
| f31r | 19 | 5.975 | 6.192 |
| f39v | 7 | 6.773 | 5.523 |
| f39v | 19 | 6.278 | 7.065 |

The seed-7 improvement on f39v is a lead, but it does not replicate with seed 19
or on f31r. One-table coverage was 100%; two-table coverage was approximately
99.5% on f31r and 98.6% on f39v. Unknown-containing words are excluded from score
and context resets at gaps, so the table is not a perfectly matched coverage
comparison. We do not infer a successful transfer from that one lower score.

The original one-table outputs matched the four-letter word `unum` once (seed 7)
and no eligible Pliny words in seed 19. The alternating-table outputs similarly
matched `illo` once and no eligible words in seed 19. **No eligible word recurred
across the two seeds.** Other variants of Latin spelling and inflection may be
missing from this finite lexicon; absence of a match is not absence of meaning.

## Rechecking the earlier promising words

A post-hoc audit applied a fixed rule to all 48 prior selected outputs: exact match
to the independent Pliny training lexicon, at least four letters long.

| Earlier input | Matched tokens / eligible tokens across outputs |
|---|---:|
| Original Voynich | 24 / 944 |
| Whole-word shuffle | 17 / 944 |
| Symbol shuffle | 4 / 944 |

This is a modest excess worth testing, not calibrated evidence of recovery.
Six original matches are repetitions of `febris` from the same proposed mapping.
Repeated cipher words and reruns are not independent discoveries. The audit's
source span, model-text hash, lexicon hash and prior evidence hash are exported.

## Why a negative result cannot reject rotation

The synthetic one-table tests recovered **100% and 98.6%** of nonspace text. The
synthetic alternating-table tests recovered only **68.5% and 81.4%**. Their true
keys both scored better than the found keys, and all known-key decodings were
exact. That demonstrates incomplete search at this budget. It does not establish
that the objective is adequate in every case.

The two-table synthetic text yielded 9 and 11 eligible Pliny word matches; Voynich
produced 1 and 0. These are illustrative controls, not matched-distribution
thresholds: the synthetic alphabet is not Voynich-sized, passage/word counts differ,
and only one Latin passage with two keys was tested per period.

## Next research step

Keep the lead conditional. Improve the two-table search using the line grouping
to initialize each table separately, then jointly refine under the full-text
objective; verify that this improves blind alternating-table recovery first.
Apply the identical procedure to originals and line controls before increasing
periods or choosing switching points. In parallel, a future scorer should be
validated on word-order sensitivity and corpus mismatch. Avoid optimizing toward
a hand-picked medical word or calling repeated instances of one mapping multiple
confirmations.

## Reproducibility and validation

[Pre-execution protocol](../../docs/protocols/LINE_ROTATION_2026-10-09.md).
Execution implementation: commit `7704ca1`; execution began with a clean tree.
Later input guards reject unsupported inputs; all 24 selected candidates were
replayed with identical losses and plaintexts after those guards were added.

[Full evidence](evidence.json), [paired comparisons](comparisons.json),
[post-hoc earlier word audit](previous_word_audit.json),
[execution environment](environment.json), [specifications](specifications.json),
[registry/replay checks](verification.json).

All 24 database registrations reached their planned limit and are recorded as
`stopped / evaluation-limit`; the study completed. Each specification reconstructs
by adding the shared environment to `manifest_without_environment`. Reports can
be regenerated without rerunning any search:

```sh
uv run --locked python -m voynich.laboratory.rotation_report \
  --input results/line_rotation_2026-10-09/evidence.json \
  --output results/line_rotation_2026-10-09 \
  --previous-evidence results/voynich_pilot_2026-10-09/evidence.json
```

**164 tests passed**, including PostgreSQL integration, independent known-key
round trips, phase-specific unknowns, line preservation, deterministic resume,
control invariants and paired report comparisons. Package build passed. No new
Python dependencies were required.
