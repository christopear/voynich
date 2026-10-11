# Stage 41: annealing improves recovery, but fails the regression guardrail

**Evidence: engineering comparison on exposed synthetic development cases.**
At the same 8,192-call budget from the same starting keys, annealing increases
mean non-space edit accuracy from **62.2% to 89.0%** and the count reaching 90%
from **2/7 to 4/7**. Six cases improve. One regresses by 11.51 percentage points,
exceeding the preregistered 10-point limit. The selection gate therefore fails.
Do not reclassify the method as passing because the average is encouraging.
There is no new manuscript reading or independent calibration in this result.

## Frozen comparison

[Protocol](../../docs/protocols/KEY_ESCAPE_2026-10-11.md), committed as `b55ccc6`;
implementation committed as `a03ad53` before execution. The seven stage 40 cases
with saved beam winners are reused as development data. The eighth case remains
unsearched because its 67 parsers exceeded the fixed cap; it was not quietly
admitted here. These seven cases represent four distinct passages, not seven
independent texts.

Both arms use the same scorer, parsers and elementary key moves. Greedy only
accepts improvements. Annealing allows temporary cost increases with probability
2**(-increase/temperature), cooling geometrically from 12 to 0.2 total-bit units.
The endpoints were fixed from the existing CodebookSearch settings. It retains
the lowest-cost visited key. Compact move descriptors are tested against the
existing exhaustive neighborhood's exact order; proposals are uniform over
the same distinct moves. This is an optimization heuristic, not a posterior
sampler or proof of global optimality.

No new starts, dictionary hints, scorer tuning or additional budget were used.
Accuracy was assessed after all fourteen runs finished. The greedy arms exactly
reproduce the corresponding stage 40 keys, plaintexts and score components.

## Results

Percent non-space edit accuracy. Delta cost is annealing minus greedy: negative
means annealing's chosen key scores better. The table does not select the best
method per case after looking at accuracy.

| Case | Greedy | Annealing | Accuracy change, points | Delta cost, bits |
|---|---:|---:|---:|---:|
| Latin / preserved / 31 | 25.33 | 98.67 | +73.33 | −385.95 |
| Latin / encoded / 31 | 33.00 | 89.67 | +56.67 | −312.74 |
| Latin / preserved / 43 | 95.97 | 96.31 | +0.34 | +6.18 |
| Latin / encoded / 43 | 75.84 | 93.29 | +17.45 | −100.58 |
| Italian / preserved / 31 | 56.58 | 67.97 | +11.39 | −6.14 |
| Italian / encoded / 31 | 51.60 | 92.17 | +40.57 | −126.81 |
| Italian / preserved / 43 | 96.76 | 85.25 | **−11.51** | +65.30 |
| Mean | 62.16 | 89.05 | +26.89 | |

All runs used their full budgets. Annealing accepted 179–211 uphill moves per
case. The results demonstrate that permitting temporary cost increases can
substantially improve this solver on these examples. They do not prove that
every earlier failure was a strict local optimum, or that this schedule is
generally superior. The temperature and trajectories were not varied.

The decision rule required a mean gain of at least five points, no reduction
in the number of cases reaching 90%, and no regression greater than ten points.
The first two conditions pass; the third fails. The threshold is not relaxed.

The regression also has a worse score than the greedy result. This suggests
testing ways to retain alternative search trajectories under a fixed *combined*
budget. It does not license combining these two full-budget runs and calling
the result an 8,192-call solver. No hybrid or best-of-two result is claimed here.

## Costs and checks

* Optimization: 7 cases × 2 arms × 8,192 = **114,688 calls**.
* Saved-key verification: **14 additional evaluator calls**, all components and
  plaintexts replay exactly.
* Common historical starting cost: stage 40's **573,440 parser-search calls**,
  already spent, not repeated. Its 57,344 greedy continuation calls are also
  historical expenditures; this study reruns those controls within the new
  114,688-call budget. Earlier development costs remain in stages 39–40 reports.
* Full suite: **274 tests passed**, four database tests skipped locally.
  `voynich list` includes stage 41. No manuscript data were loaded.

No protocol deviations or post hoc optimization. Exact keys, cost components,
accepted-move counts and best-cost trajectories are in `search/`. Full and
non-space accuracy are in `evidence.json`. Reproduction uses a new output path:

```sh
uv run --locked python -m voynich.experiments.e41_key_escape --output /tmp/key-escape-check
uv run --locked python -m voynich.experiments.e41_key_escape --verify --output /tmp/key-escape-check
```

## Decision

Keep this as a promising development result, not a qualified replacement for
the frozen pipeline. It identifies a productive search mechanism on cases
where greedy continuation previously failed, while exposing an important
regression. A next prospective comparison should test protecting strong
solutions within the same total budget, without raising this stage's budget
or tuning its cooling schedule. Any selected improvement still requires fresh
full-pipeline recovery and unchanged-key transfer before manuscript use.
The original f26r representation remains infeasible under the old assumptions.
