# Medical cipher recovery — review point

Open [the executive report](report.html). [evidence.json](evidence.json) contains
metrics, original diagnoses and gates, post-search audits, source provenance,
run IDs, environments and one selected candidate per search.

## Executive findings

We tested unknown-key recovery on Celsus and Pliny medical/herbal passages,
training each language model on the other author. This is closer to the working
medicinal-cipher hypothesis than the previous same-work literary controls,
although the sources are ancient texts in modern editions, not medieval recipes.

At the same 8,000-candidate budget, the key-search beam recovered more plaintext
than annealing in **14 of 16 paired cipher instances**, tied once and lost once.
There are only four source passages and two authors; these comparisons are
correlated engineering evidence, not a general success probability.

| Cipher family | Annealing mean development accuracy | Beam mean development accuracy |
|---|---:|---:|
| Simple substitution | 98.15% | 99.75% |
| Homophonic substitution | 59.28% | 76.61% |
| Fixed two-symbol groups | 59.73% | 91.84% |
| Variable one/two-symbol groups | 58.89% | 95.32% |

Each mean covers four passage/key instances. The beam's homophonic results
range from 25.4% to 98.2%; it is useful but not dependable by itself. Fixed groups
reach exact development recovery on one Pliny passage. Variable fixtures are
mostly single-character codes (31 of 34 key entries), so their strong averages
do not establish recovery of arbitrary variable-length codes.

Across 32 selected outputs (16 instances × two algorithms), **15 reach at least
95% development accuracy**, four are exact, and four pass the full screening
gate. Eleven of those fifteen high-accuracy outputs still have incomplete
reserved-code coverage. The four full passes concern two Celsus simple-substitution
instances under both algorithms. They are not four independent source successes.

The new representation removes forced single-character fallback mappings from
grouped codebooks. Every new true active key is valid and decodes exactly under
the declared evaluator. The prior 32-case audit found 16 demonstrated search
gaps in glyph/homophonic recovery and 16 representation mismatches in grouped/
mixed cases; it did not rerun or overwrite those experiments.

## What still prevents reliable recovery

1. **Search instability:** 17 selected outputs remain below 95% even though the
   valid true key scores better. A beam can improve recovery and still get stuck.
2. **Language-model error:** both methods prefer the same near-correct `b`/`f`
   substitution on one Celsus instance. The wrong reading scores slightly better
   than truth. A search algorithm cannot repair a preference in its objective.
3. **Encoder/scorer mismatch:** a post-search audit finds 11 selected grouped
   paths that violate the fixture encoder's longest-match unit rule. The scorer
   accepts optional letter/pair spellings; the fixture encoder does not. One of
   these results exceeds 95% accuracy. Original gates remain unchanged, but a
   readable path is not automatically a recovered generating mechanism.
4. **Incomplete transfer:** unseen codes and incorrect boundary policies remain
   explicit failures. `?` counts as an error. Conditional completion counts are
   reported without choosing any missing mapping or using reserved language
   evidence to fit the key.

## Recommended next experiment

First make the generator and scorer agree: enforce the declared longest-match
rule in one arm, and give optional letter/pair spelling an explicit probability
law in another. Keep both search methods, with equal total budgets for any
portfolio comparison. Test lexical/orthographic scoring on fresh passages rather
than tuning it to repair the observed `b`/`f` example.

Predeclare a bounded key-completion stage for newly encountered codes, then assess
it on a further reserved passage. Do not retroactively turn current frozen-key
failures into passes. For example, several strong partial readings have only
5–7 remaining assignments for their missing codes, whereas some variable-code
cases have much greater uncertainty under their selected segmentation policy.

Then move the calibration toward manuscript conditions: restricted symbol
inventories, less favorable mixtures of code lengths, uncertain spaces, and
medieval Latin/Italian medical sources. The encoder now supports 12/20-symbol
fixtures with engineering tests, but **no blind search in this report uses
those restricted alphabets**. No Voynich ciphertext has been searched or decoded.

## Execution and reproduction

- Frozen research implementation: commit `18660e5`; one clean execution environment.
- Plan: `configs/benchmarks/medical-recovery-2026-10-08.json`.
- Protocol: [MEDICAL_RECOVERY_2026-10-08.md](../../docs/protocols/MEDICAL_RECOVERY_2026-10-08.md).
- 64 registered searches, 512,000 candidate evaluations, zero captured evaluator
  exceptions. Invalid candidates are counted separately in each run.
- A 16-search, 256-evaluation engineering smoke run is excluded from these totals.
- PostgreSQL registrations were reconciled against all exported run IDs, specs,
  states and evaluation counts. Each search reaches its budget; a per-run
  `stopped/evaluation-limit` status is expected and the planned study is complete.
- 147 tests, including PostgreSQL integration, and package builds pass.
- Tests verify score parity, resume behavior, matched-control preservation,
  plan boundaries, default-key replay, restricted-alphabet reversibility,
  completion counts against exhaustive enumeration and encoder consistency.

Use a new output path and the configured database to run the plan:

```bash
uv run --env-file .env --locked python -m voynich.laboratory.medical_recovery \
  --plan configs/benchmarks/medical-recovery-2026-10-08.json \
  --output results/runs/medical-new
```

Registrations reject exact duplicates unless an explicit rerun reason is supplied
through the lower-level runner. A fresh research database can reproduce a whole
study without changing existing registrations. Source/code hashes and recorded
environments distinguish scientifically equivalent reruns from bitwise replay.

Re-export the completed local evidence (no searches):

```bash
uv run --locked python -m voynich.laboratory.medical_report \
  --input results/runs/medical-recovery-2026-10-08 \
  --audit results/runs/initial-oracle-audit-2026-10-08.json \
  --output results/medical-report-new
```

The ignored local run folders retain private fixture truth and bounded archives;
PostgreSQL retains registrations/checkpoints. The committed export is reviewable
without them. Source acquisition, immutable URLs, hashes, edition attribution,
extraction policy and CC BY-SA licenses are under `data/laboratory_sources/`.

Post-search additions (not predeclared selection rules): the near-correct
objective-preference audit above the 95% threshold, cost-component gaps, actual
code-length composition, unseen-mapping completion counts and greedy-unitization
checks. These diagnose existing outcomes and do not alter proposals, scores,
selected keys, original diagnoses or gates.
