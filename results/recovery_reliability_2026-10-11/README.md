# Stage 42: no tested method meets the recovery reliability criteria

**Prospective synthetic comparison; no manuscript evidence.** Three frozen
methods were tested on eight new cipher cases, with three independent search
seeds per case and unchanged-key transfer. None qualifies. All 24 trials
selected the true parser; unstable key recovery is the principal observed
failure. These results replace neither the earlier failed gates nor their data.

## Primary results

All percentages are non-space edit accuracy. There were 24 paired trials per
method. A consistent case must reach at least 90% recovery **and** transfer in
all three search seeds. The criterion required at least six consistent cases,
plus at least six recovery and transfer successes in each seed, covering all
four language/spacing cells. Each method fails.

| Method | Mean recovery | Mean transfer | Recovery >=90% | Transfer >=90% | Consistent cases | Qualifies |
|---|---:|---:|---:|---:|---:|---|
| Greedy | 79.16% | 76.18% | 15/24 | 15/24 | 2/8 | No |
| Annealing | 83.47% | 81.07% | 15/24 | 14/24 | 1/8 | No |
| Equal-budget portfolio | 84.52% | 81.02% | 17/24 | 13/24 | 2/8 | No |

These are finite-panel summaries, not estimates from 24 independent passages.
There are four distinct recovery passages, each encoded under two spacing
policies, with the search repeated three times. Passage and key seed are paired.

| Method | Seed 101 recovery / transfer passes | Seed 202 | Seed 303 |
|---|---:|---:|---:|
| Greedy | 6/8 / 6/8 | 4/8 / 4/8 | 5/8 / 5/8 |
| Annealing | 6/8 / 6/8 | 5/8 / 5/8 | 4/8 / 3/8 |
| Portfolio | 7/8 / 4/8 | 5/8 / 5/8 | 5/8 / 4/8 |

For example, Latin/preserved/key-71 recovery with annealing is **96.3%, 97.3%,
19.2%** across seeds 101/202/303. Corresponding transfer is **92.7%, 93.3%,
23.0%**. Reporting only the best seed would conceal the failure.

Against greedy, annealing improves recovery in 10 paired trials, worsens eight
and ties six; its mean gain is 4.30 points, with a worst regression of 66.67
points. Portfolio improves eight, worsens ten and ties six; its mean gain is
5.36 points, with a worst regression of 40.74 points. The stage 41 exposed-case
annealing gain of 26.89 points did not reproduce at that magnitude here.

## Fixed method and data

[Protocol](../../docs/protocols/RECOVERY_RELIABILITY_2026-10-11.md), commit
`aad7a9e`; implementation `2743430`, committed before generation and execution.
Producer: `voynich.experiments.e42_recovery_reliability`.

Targets are new 350-character normalized Pliny/Dante slices at 85% and 90%
of the respective source, fixture seeds 59/71, preserved/encoded spacing.
Separate transfer slices begin 1000 characters later. All intervals are checked
against training, the original grouped-study target and stage 40 targets and
transfers. Freshness is relative to this pipeline's passage experiments, not a
claim that these books were never used elsewhere. Training and scorer are fixed.

For each search seed (101/202/303), all structural survivors are searched with
4,096 beam calls each. The lowest-loss parser winner supplies the same starting
key to all methods. Greedy and annealing get 8,192 calls each. Portfolio splits
8,192 calls into 4,096 greedy and 4,096 annealing from that same start, selecting
by total score alone. Both starts count. The temperature schedule remains
12 to 0.2. No method is chosen using accuracy, transfer or agreement.

All cases fall below the frozen 64-parser cap; none was omitted. The true parser
is retained in 8/8 cases and selected in 24/24 trials. Structural survivor counts:

| Case | Parsers |
|---|---:|
| Latin preserved 59 | 17 |
| Latin encoded 59 | 34 |
| Latin preserved 71 | 4 |
| Latin encoded 71 | 24 |
| Italian preserved 59 | 9 |
| Italian encoded 59 | 31 |
| Italian preserved 71 | 6 |
| Italian encoded 71 | 16 |

Mean beam-only recovery before refinement was 51.51%. All three refinements
improve the panel mean, but improving that mean does not establish reliable
decoding. Transfer glyph coverage is 95.29–100%, with every transfer span
parseable. Missing codewords therefore do not explain the largest failures.

## Cross-seed agreement

The preregistered stability flag requires the same parser in every seed and
at least 95% minimum pairwise decoded-position agreement, excluding positions
where both predictions are spaces. It never enters key selection.

Greedy flags two cases, annealing one, and portfolio one. Every flagged case
has >=90% recovery in all its seeds. These four method/case flags cover only
three distinct cipher cases; one case is flagged by two methods. This small
sample with no observed false flags does **not** calibrate a correctness
certificate. Most cases do not receive a flag, and successful near-correct
decodes can fail the agreement threshold. Do not substitute agreement for an
independent reading or claim that an unflagged output is necessarily wrong.

## Post hoc objective audit

After the main assessment, eight known true active keys were scored once each.
The source and output are `voynich.experiments.posthoc_e42_objective_audit` and
`posthoc_objective.json`. This is labelled post hoc, does not alter any method
or gate, and costs eight additional scorer calls.

All below-90% results leave a better-scoring true key unreached: 9/9 greedy,
9/9 annealing and 7/7 portfolio failures. This demonstrates incomplete
optimization. It does not prove the true key is the global optimum, or that a
different objective could not also change the search landscape.

Conversely, incorrect outputs score better than exact truth in ten greedy,
eight annealing and eight portfolio results. All those outputs are above the
90% recovery threshold. Thus the current objective has a separate exactness
problem even when search reaches a good reading. Optimizing it more thoroughly
does not certify exact plaintext.

## Accounting and verification

* Shared parser work: 423 parser searches × 4,096 = **1,732,608 calls**.
* Refinement: 24 trials × 3 methods × 8,192 = **589,824 calls**.
* Total: **2,322,432 optimization calls**, below the 6,881,280 cap.
* A standalone method would incur the shared parser work plus its own 196,608
  refinement calls: **1,929,216 calls** over these 24 trials. Sharing is a
  benchmarking economy, not a free parser for deployment.
* Exact replay: **543 scorer calls** covering every parser winner, all selected
  method outputs, and both portfolio components. Scores and plaintexts match.
* Oracle diagnosis: **eight calls**, separate from optimization and replay.
* Seventy-two frozen transfer decodes and fixture round trips are evaluation
  operations, not optimization. Earlier development expenditure remains charged
  in stages 39–41; it is not reused as fresh search work here.

All 277 tests pass; four database tests skip locally. Stage 42 is discoverable.
No primary-protocol deviations, outcome-based budget changes or search reruns.
Only the labelled post hoc objective audit extends the primary analysis.
The manuscript and its sealed confirmation pages were not read.

All per-case/per-seed outcomes are in `evidence.json`; exact candidate keys,
component costs, portfolio selection and call counts are in `trials/`.
Reproduction requires a new output directory:

```sh
uv run --locked python -m voynich.experiments.e42_recovery_reliability --output /tmp/reliability-check
uv run --locked python -m voynich.experiments.e42_recovery_reliability --verify --output /tmp/reliability-check
uv run --locked python -m voynich.experiments.posthoc_e42_objective_audit --output /tmp/reliability-check
```

## Defensible conclusion

Within these clean synthetic conditions, exhaustive structural retention plus
score-based parser selection is repeatable. Exact key recovery is not. Greedy,
annealing and the half-budget portfolio all sometimes recover keys that read
another passage well; none consistently does so across search seeds. None
qualifies for promotion to a manuscript attack, and none universally dominates
the others. The larger observed errors reflect missed solutions; small errors
also reflect the scoring objective. Original f26r infeasibility is unchanged.

See the [consolidated methods assessment](../../docs/reports/RECOVERY_METHODS_ASSESSMENT_2026-10-11.md)
for the actionable interpretation across stages 39–42.
