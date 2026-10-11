# Stage 39: return to unknown-key recovery

**Evidence: synthetic engineering improvement on previously used development
cases. No manuscript reading or cipher-family exclusion.**

The original retained-parser search recovered 28.5–75.0% of non-space plaintext
characters, with no case reaching 90%. Continuing its saved keys with a fixed
random greedy search reaches 90% in five of eight cases. Mean non-space edit
accuracy rises from 56.3% to 78.7%. This measures added recovery capability on
these examples; it is not independent blind calibration, a new family fit, or
evidence that Voynich uses this cipher. It also costs additional evaluations.

## What was run

[Protocol](../../docs/protocols/RECOVERY_PIPELINE_2026-10-10.md), Phase A committed
as `98a34dc`; Phase B amendment committed as `1f80399` after the diagnosis and
before continuation. Producer: `voynich.experiments.e39_recovery_pipeline`;
reusable search: `voynich.search.neighborhood`. Original artifacts are unchanged.

The same eight public ciphertexts, training slices, selected parsers, capacity
two and GroupedEvaluator were used. Source and prepared training hashes and
historical winner scores replay exactly. Truth never enters search selection.
Accuracy is measured only after loss-based selection. The original language
model, homophone-choice cost and key/policy costs are unchanged.

Phase A enumerated every distinct one-code reassignment and two-code swap from
both the returned and true active keys. All 16 neighborhoods fit the prescribed
cap. Every returned key had improving moves (8–50); every true key also had
incorrect improving moves (3–13). The best incorrect neighbors reduce total
cost by 7.49–14.06 bits while retaining 97.86–98.68% non-space accuracy. Language
cost accounts for the reduction in seven cases; one also saves two choice bits.
Thus the scorer's preference errors are real but these local examples do not
explain the much larger recovery failures by themselves.

Phase B compared systematic best-improvement descent and uniformly sampled
random greedy descent, each starting from the same historical winner with an
8,192-call cap. It compares two continuations, not either method against an
equal-budget rerun of the historical beam. There was no change of scorer or
outcome-dependent extension.

## Recovery results

Percent non-space edit accuracy; spaces excluded from this metric. Both-spacing
edit accuracy, plaintexts, exact keys and cost components remain in the JSON.

| Case | Original | Systematic | Random |
|---|---:|---:|---:|
| Italian, encoded spaces, seed 19 | 75.00 | 92.50 | 98.21 |
| Italian, encoded spaces, seed 7 | 29.64 | 36.07 | 35.71 |
| Italian, preserved spaces, seed 19 | 73.57 | 88.93 | 95.36 |
| Italian, preserved spaces, seed 7 | 66.07 | 77.14 | 94.64 |
| Latin, encoded spaces, seed 19 | 68.54 | 93.38 | 95.70 |
| Latin, encoded spaces, seed 7 | 39.07 | 48.68 | 95.70 |
| Latin, preserved spaces, seed 19 | 69.87 | 87.42 | 87.42 |
| Latin, preserved spaces, seed 7 | 28.48 | 27.15 | 27.15 |
| Mean | 56.28 | 68.91 | 78.74 |
| Cases at least 90% | 0/8 | 2/8 | 5/8 |

All eight final keys have better scores, but one has worse accuracy. Systematic
search certifies a local optimum in that failed case after 6,193 calls. Its
other seven sweeps end incomplete at the budget limit; none is a local-optimum
certificate. Random search uses the full budget in every case. Eight cases,
two languages and two fixture seeds are too few to establish general solver
superiority. No best-of-two-arm selection based on accuracy is presented.

## Costs and verification

* Historical all-parser searches: 724,992 represented evaluations, including
  reused runs; these are the common sunk starting cost, not repeated here.
* Phase A: 16,923 neighborhood evaluations plus 16 replay/round-trip checks.
  The original Phase A JSON reports neighborhood evaluations only; its extra
  validation calls are stated here explicitly (and in subsequent producer runs).
* Phase B: 63,537 systematic and 65,536 random evaluations, 129,073 total,
  below the combined 131,072 cap; eight additional historical-start replays.
* Export verification: 48 saved records and eight historical starts replay
  exactly, including components, plaintexts and both accuracy metrics.

Source manifests capture the files used at execution, including the then
uncommitted implementation; the protocol commits precede the relevant runs.
Elapsed seconds are recorded per case/arm. No database runs or manuscript
statistics were created. The full suite passed: 268 tests, four database tests
skipped locally. `voynich list` discovers stage 39.

Reproduction in a fresh output directory:

```sh
uv run --locked python -m voynich.experiments.e39_recovery_pipeline --output /tmp/recovery-check
uv run --locked python -m voynich.experiments.e39_recovery_pipeline --continuation --output /tmp/recovery-check/continuation
uv run --locked python -m voynich.experiments.e39_recovery_pipeline --verify --output /tmp/recovery-check
```

No decision-rule deviations. Verification-call accounting is additional to
the search budgets. Timing/environment metadata and the amended protocol hash
will differ on replay; candidate and score comparisons are the scientific checks.

## Decision and next checkpoint

Search improvement was warranted and produced substantial recovery gains on
five cases. Systematic enumeration is useful for diagnosing local failures but
did not outperform the random continuation overall. Keep random continuation
available in the recovery pipeline; do not claim it solves the family.

The remaining failures require separating poor basins from objective preference
errors. A next study should freeze a complete solver (including parser search
and continuation), use new disjoint synthetic passages, charge all initialization
and parser costs, and evaluate it without answer-based method selection. Any
new scoring model must be trained and chosen independently of these answers.
The present run stops at its registered budget rather than adding starts until
the table improves.

No manuscript attack is justified by this result yet. The original f26r page
still admits no parser under the old boundary/expansion assumptions; better key
search cannot repair that. A manuscript trial additionally needs a justified
representation, successful fresh full-pipeline recovery, matched controls and
unchanged-key transfer. Our understanding of the manuscript's meaning has not
changed in this stage.
