# Separate table initialization, then immediate Voynich trial

Written before execution, 9 October 2026. This changes the optimizer, not the
cipher family or final score. The aim is stronger evidence on Voynich. Synthetic
accuracy will never be described as manuscript recovery.

Compare the existing cold two-table beam (8,192 evaluations) with a pipeline:
2,048 evaluations on even-indexed lines, 2,048 on odd-indexed lines, then 4,096
joint evaluations. Each initialization phase uses an independent single injective
table and resets its character-model context at every source line; it never
creates artificial adjacency between separated manuscript lines. Retain three
phase winners, rank their nine combinations by the sum of total phase costs, and
use the first eight as joint beam starts. All full-text rescoring counts within
the 4,096 joint budget. Both methods use width 8 and the same final evaluator,
training text, table-cost penalty and mutation operator. Initialization candidates
and stage run IDs are recorded, so no optimization work is hidden.

Four Latin calibration cases: the two prior two-table cases (seeds 7 and 19,
600 normalized Pliny characters at 65% of the source), plus seeds 31 and 43 on
new 600-character passages at 70% and 75%. Key seeds remain search_seed+500.
Plaintext and known keys are audited only after both methods select their final
candidates. Celsus training stays 60,000 normalized characters at 30%; Pliny's
analogous segment remains post-selection only. These four cases assess a local
engineering improvement, not broad recovery power or medieval corpus coverage.

Immediately run both methods on all ten prior manuscript/control cases: f26r
original, three whole-line shuffles and one symbol shuffle, each with seeds 7 and
19. Preserve previous inputs, line clock, phase zero reset, compound-EVA units,
uncertain-word omissions and control seeds. Apply selected mappings unchanged to
f31r and f39v; neither is newly untouched. This manuscript screen runs even if
calibration is mixed, but a method is not declared improved merely because it was
implemented. Compare against both equal-budget cold search and the prior 4,096
results, making the budget difference explicit.

Total: 14 cases × 2 methods × 8,192 = 229,376 registered evaluations in 56 runs
(14 cold, 28 phase initializers, 14 joint refinements). These are candidate
proposals, not necessarily unique keys; oracle/report re-scores are separate.

Report paired losses, independent Pliny costs, unchanged-key transfer coverage,
lexicon hits >=4 letters, and whether the same eligible words recur across seeds.
Use the same underlying mapped positions when comparing frozen models: their
unknown phase/symbol inventory should be identical. Keep full outputs, not just
attractive fragments. Report controls with identical optimization. Three shuffled
line realizations are not a significance test. Repeated words/searches are not
independent recoveries. Better Latin fit is not a translation.

If the optimizer improves synthetic recovery without a manuscript/control
advantage, prioritize reconsidering representation, segmentation and corpus
assumptions rather than expanding this search indefinitely.

```sh
uv run --env-file .env --locked python -m voynich.laboratory.phase_initialization \
  --output results/runs/phase-initialization-2026-10-09
```
