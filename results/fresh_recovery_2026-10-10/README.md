# Stage 40: fresh full-pipeline recovery fails its calibration gates

**Synthetic calibration only.** The frozen grouped-code pipeline reaches 90%
non-space plaintext recovery in **2/8 cases**, and unchanged-key transfer reaches
90% in **2/8**. Both gates required at least six passes. The stage 39 result of
5/8 on previously used examples did not carry over reliably to this panel.
No manuscript decoding was attempted or justified.

## What changed from stage 39

Four different 350-character passages (two Pliny, two Dante), two new key seeds
and both spacing assumptions were fixed in the
[protocol](../../docs/protocols/FRESH_RECOVERY_2026-10-10.md), commit `09a4cc5`.
Implementation commit `2689db3` preceded execution. Training sources, scorer,
encoder family, parser screen and search settings were unchanged. The passages
and separate transfer passages are disjoint from each other, training and the
earlier grouped study's passage. This is freshness relative to this recovery
comparison, not a claim that these books are untouched project data.

All structural survivors were retained, subject to the precommitted 64-parser
cap. Each parser received 4,096 beam evaluations including initialization. Only
the lowest-loss parser winner received 8,192 random greedy continuation calls.
Truth was consulted for assessment after all search selections were complete.
An additional passage was decoded with the unchanged selected key and parser;
unseen codes remained unknown and counted as errors.

This is a frozen-pipeline validation, not an equal-budget algorithm comparison.
It tests clean synthetic spans in this particular family. It does not reproduce
all manuscript conditions such as doubtful spaces, transcription damage,
page-specific vocabulary or the manuscript's full entropy profile.

## Every case

Percent non-space edit accuracy. Before = parser search winner before
continuation. The failed budget screen counts as a failure, not a missing case.

| Language / spacing / seed | Parsers | Before | After | Unchanged-key transfer |
|---|---:|---:|---:|---:|
| Latin / preserved / 31 | 17 | 19.67 | 25.33 | 28.15 |
| Latin / encoded / 31 | 34 | 22.00 | 33.00 | 32.78 |
| Latin / preserved / 43 | 11 | 62.75 | **95.97** | **93.75** |
| Latin / encoded / 43 | 39 | 49.33 | 75.84 | 67.11 |
| Italian / preserved / 31 | 13 | 55.52 | 56.58 | 55.52 |
| Italian / encoded / 31 | 20 | 35.59 | 51.60 | 53.74 |
| Italian / preserved / 43 | 6 | 69.06 | **96.76** | **95.10** |
| Italian / encoded / 43 | 67 | Not searched: cap 64 | Failure | Failure |

The true parser survived screening in all eight cases and was selected in all
seven searched cases. The five searched failures are therefore key-recovery
failures after correct parser selection. The eighth case is a budget-screen
failure; it is not evidence that its key cannot be recovered. We did not raise
the cap by three after seeing its candidate count.

Space-boundary F1 is 1.0 in all seven completed cases, including encoded-space
cases. This did not ensure correct letters. All transfer spans parse; transfer
glyph coverage is 96.3–100%. Thus low transfer accuracy cannot be attributed
solely to unknown codewords or failed segmentation. Full edit accuracy,
plaintexts, keys, coverage and separate cost components remain in the exports.

Only four distinct recovery passages underlie these eight cases, with each
passage paired to one key seed. These results do not estimate a general recovery
rate or separate passage difficulty from key difficulty.

## Post hoc diagnosis: why the failures matter

After the gates failed, a separately labelled, seven-call oracle comparison
scored the known true active keys. It did not change the search or thresholds.
Producer: `voynich.experiments.posthoc_e40_recovery_diagnosis`;
artifact: `posthoc_oracle.json`.

In all five completed cases below 90%, the true key scores better than the
returned key: by 26.7–379.3 total bits. A better-scoring correct solution exists
and the frozen search did not find it. That establishes an optimization
limitation; it does not establish that the true key is the global optimum or
that the scorer is sufficient.

Conversely, the two high-recovery keys score 29.2 and 8.7 bits better than the
exact true keys while retaining errors. This confirms that minimizing the
current objective is not the same as maximizing plaintext accuracy. Do not
train a replacement scorer on these known answers.

## Budget, deviations and verification

* 140 searched parsers × 4,096 = 573,440 evaluations.
* Seven continuations × 8,192 = 57,344 evaluations.
* Total optimization: **630,784**, below the 2,162,688 maximum.
* Independent exact replay: 147 stored keys (140 parser winners plus seven
  refined winners), including plaintext and score components.
* Post hoc oracle diagnosis: seven scorer calls, separately charged.
* Known-key fixture round trips and seven frozen transfer decodes are validation
  and evaluation operations, not optimization calls.

Stage 39's method selection is prior development work, not part of the fresh
optimization count: 724,992 historical represented evaluations, 16,923 diagnostic
neighborhood evaluations and 129,073 continuation evaluations, plus the replay
checks documented in its report. No historical search was repeated here.

No search-budget or decision-rule deviations. One startup failed because the
sandbox blocked Python's local multiprocessing socket, before any key search.
Its generated packet was archived under ignored `results/runs/`; the same
protocol and implementation were restarted with process creation permitted.
The oracle comparison is explicitly post hoc, not preregistered confirmation.

All 272 tests passed, with four database tests skipped locally. Stage 40 appears
in `voynich list`. Run and verify using new output paths:

```sh
uv run --locked python -m voynich.experiments.e40_fresh_recovery --output /tmp/fresh-recovery-check
uv run --locked python -m voynich.experiments.e40_fresh_recovery --verify --output /tmp/fresh-recovery-check
uv run --locked python -m voynich.experiments.posthoc_e40_recovery_diagnosis --output /tmp/fresh-recovery-check
```

## Decision

Do not promote this frozen solver to a manuscript attack. It sometimes recovers
a new synthetic key well enough to read another passage, but does not do so
reliably under the declared budget. The scorer has smaller errors even on its
successful cases; the much larger failures also leave better-scoring true keys
unreached.

The next engineering question is how to escape incorrect key assignments under
a fixed total budget, with a fresh prospective comparison. Merely expanding
the parser cap would address only the unsearched case; it would not resolve the
five failed searches with correct parsers. Any search or scorer changes selected
using this panel make it development data and require another independent
calibration. The original f26r boundary/expansion infeasibility also remains.
Nothing in this stage changes our understanding of the manuscript's meaning.
