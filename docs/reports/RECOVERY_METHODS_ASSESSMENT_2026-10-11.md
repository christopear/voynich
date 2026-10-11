# Which recovery methods are consistent and defensible?

As of 11 October 2026, **none of the three tested key-search procedures is a
reliable decoder for the bounded grouped-code family at the frozen budget.**
This is now supported by an independent multi-seed comparison, not just a
single failed run. It is not a rejection of the cipher family, and says nothing
new about the manuscript's meaning.

## What is supported

**Parser recovery works repeatedly within the synthetic family.** On the latest
eight new cases, every true parser survives screening and is selected in all
24 full-pipeline trials. Retaining all structural survivors is defensible here.
The earlier unigram pruning is not. The original manuscript page still has no
admissible parser under this model's boundary/expansion assumptions; successful
synthetic parser selection does not remove that representational mismatch.

**Temporary cost increases can help key search.** Annealing substantially
rescued several old failures at the same budget. On independent cases its mean
gain over greedy was much smaller (4.30 points), with large regressions on some
seeds. It is a useful research comparator, not a consistently superior default.

**The equal-budget combination is also unreliable.** Splitting the budget
between greedy and annealing gives the highest recovery mean in this panel,
but fewer transfer successes than greedy. A better mean and a better decoder
are not interchangeable claims.

**Good fitted keys sometimes read a second passage unchanged.** This is genuine
recovery evidence for the synthetic encoder: no transfer fitting or unknown-key
completion was permitted. The problem is repeatability across runs, not an
absence of every successful decoding.

## Independent comparison

The latest panel used four different target passages, eight cipher cases,
three search seeds per case, and separately encoded transfer passages.
Methods had identical starting keys and equal refinement budgets, with the
full parser search charged. Four plaintexts are not 24 independent texts.

| Method | Mean recovery | Mean transfer | Trials >=90% recovery / transfer | Cases >=90% in both, across all seeds |
|---|---:|---:|---:|---:|
| Greedy | 79.2% | 76.2% | 15/24 / 15/24 | 2/8 |
| Annealing | 83.5% | 81.1% | 15/24 / 14/24 | 1/8 |
| Half-budget combination | 84.5% | 81.0% | 17/24 / 13/24 | 2/8 |

All fail the preregistered reliability criteria. For the same Latin ciphertext,
annealing recovers 96.3%, 97.3%, or 19.2% depending on search seed. Greedy and
the combined method also exhibit large variations. Choosing the best seed
after seeing truth would conceal the central limitation.

## Why they fail

There are two distinct demonstrated problems:

1. **Search misses good solutions.** Every below-90% result in the new panel
   has a known true key with a better score than the returned key. Correct
   parsers were selected, so these are not parser-selection failures.
2. **The objective does not identify exact truth.** Some near-correct outputs
   score better than the exact true plaintext. More thorough optimization alone
   cannot certify exact readings. Better language scoring might also alter the
   search landscape, but no such improvement has been established here.

These findings prevent both easy explanations: “the cipher family is wrong”
does not follow from failed search, and “just find the lowest score” does not
guarantee a correct translation.

Cross-seed agreement is worth measuring, but not yet a validated confidence
measure. Four method/case combinations exceeded the 95% agreement flag and
all recovered over 90%; they cover only three distinct cipher cases. That is
too little evidence to certify an unknown output. Disagreement is visible
instability; agreement still needs independent validation.

## Decision for the project

Keep these methods as **experimental search tools whose output is a candidate**.
Do not describe any as a qualified manuscript decoder. Do not pick the portfolio
solely for its highest mean, promote annealing solely for its old gains, or
manufacture consistency by reporting the best of several seeds without charging
the budget and independently validating the selection rule.

The defensible workflow is to freeze a method and score, evaluate complete
recovery across seeds on new data, test unchanged-key transfer, and require
independently checkable evidence for any manuscript reading. That workflow has
now exposed the uncertainty; it has not made the current decoder reliable.

This round ends with a methodological conclusion, rather than another suggested
temperature, seed count or budget increase. Further work should address a named
source of identifiability or representation: for example, an independently
specified constraint on candidate plaintext, or a justified treatment of
manuscript units and boundaries. Such a proposal must show why it can distinguish
correct readings from lower-scoring errors and must preserve independent data
for validation. These are research directions, not demonstrated fixes.

**We have improved a decoder's ability to solve some synthetic ciphers. We
have not established a consistent unknown-key decoder, identified the Voynich
encoding, or recovered a verified manuscript word.**

## Evidence trail

* [Stage 39](../../results/recovery_pipeline_2026-10-10/README.md): old-case random
  continuation improves recovery; 5/8 exceed 90%. Development evidence only.
* [Stage 40](../../results/fresh_recovery_2026-10-10/README.md): fresh pipeline
  and transfer each succeed in only 2/8; one parser-budget failure.
* [Stage 41](../../results/key_escape_2026-10-11/README.md): old-case annealing
  mean rises 62.2% to 89.0%, but a regression violates its selection guardrail.
* [Stage 42](../../results/recovery_reliability_2026-10-11/README.md): independent
  equal-budget, multi-seed comparison; no method meets its reliability criteria.

The panels, denominators and budgets differ across these stages. Their headline
percentages are not one continuous learning curve or interchangeable estimates.
