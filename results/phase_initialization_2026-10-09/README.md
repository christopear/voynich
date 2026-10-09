# Returning the initialization experiment to Voynich

**Actual Voynich fit improved in both seeds and all four frozen-page comparisons
against equal-budget conventional search. We still have no validated word reading,
and line-shuffled controls remain competitive.**

[Open the manuscript-first report](report.html). It leads with actual f26r/f31r/f39v
results, then controls, and separately labels the known-text calibration.

## Actual manuscript results

Each method received 8,192 candidate evaluations. Conventional search used them
jointly. Separate initialization spent 2,048 per table and then 4,096 jointly.
No initialization work is hidden; scored text lengths and wall time are not equal.

| Actual f26r search | Seed 7 | Seed 19 |
|---|---:|---:|
| Previous conventional search, 4,096 evaluations | 6.550 | 6.522 |
| Conventional search, 8,192 | 6.444 | 6.242 |
| Separate initialization then joint search, 8,192 | **5.951** | **5.914** |

Lower is better under the same penalized objective. New initialization improves
fitted loss by 7.6% and 5.3% against the equal-budget conventional search. These
are objective improvements, not plaintext accuracy.

Apply the same keys to other pages without completing missing mappings or fitting
anything on those pages. Independent Pliny character costs:

| Transfer page | Seed | Conventional 8,192 | Initialized 8,192 |
|---|---:|---:|---:|
| f31r | 7 | 6.318 | **5.363** |
| f31r | 19 | 5.727 | **5.208** |
| f39v | 7 | 5.948 | **5.600** |
| f39v | 19 | 6.527 | **5.837** |

The unknown word positions are identical across the two methods. Symbol coverage
is 99.5% on f31r and 98.6% on f39v. Unknown-containing words are excluded and model
context resets at gaps; scores therefore concern the covered text.

This comparison matters: improving the fit to f26r alone could be overfitting.
Here the new method also improves all four independent-page model scores. But
relative improvement does not by itself establish correct letters.

## What the controls say

For each seed, three line-shuffled versions and one symbol-shuffled version get
exactly the same pipeline. Line shuffling retains every word and internal line
structure but changes the proposed alternating-table assignment.

With separate initialization, original f26r beats line-shuffled controls in **4/6**
penalized-score comparisons, but only **3/6** under the independent Pliny language
score. On frozen transfer it beats the line controls 4/6 times on f31r and 5/6 on
f39v. These small, reused comparisons are not independent significance tests;
transfer masks also differ between original and shuffled inputs.

No exact proposal of the form **same table phase + same cipher word + same Latin
word of at least four letters** recurs across the two original-page seeds. In the
initialized outputs, seed 7 supplies one eligible Pliny lexicon match (`ullo`),
and seed 19 supplies none. Full outputs are available; the finite lexicon is not
an exhaustive inventory of Latin words. There is still no coherent translation
or independently established plaintext fragment.

## A manuscript-layout constraint, beyond optimizer scores

A post-hoc inspection found that f26r and f39v start paragraphs on zero-based lines
0 and 6. Under an alternating-table hypothesis, **page reset and paragraph reset
produce exactly the same state schedule on those two pages**. They cannot tell us
which reset rule is intended. f31r has starts at 0, 5 and 9, so it can distinguish
the schedules.

Using all four selected keys unchanged on f31r, paragraph reset scores worse than
page reset in all four cases under Pliny. The comparison uses only the 78 word
slots known under both schedules, so it does not reward either rule for dropping
hard words. Costs are in [the clock audit](clock_audit.json) and the report.

This is a conditional, post-hoc observation, not proof that either clock is real.
It identifies a genuinely discriminating page/layout and a limitation of the
current line-shuffle controls: they mix paragraph starts, ends and interior lines.
Future controls should preserve those roles while disrupting the proposed state.

## Synthetic calibration — separate from Voynich

| Known-text case | Conventional 8,192 | Initialized 8,192 |
|---|---:|---:|
| Previous passage/key, seed 7 | 89.9% | **99.4%** |
| Previous passage/key, seed 19 | **98.3%** | 53.8% |
| New passage/key, seed 31 | **98.1%** | 94.7% |
| New passage/key, seed 43 | **100%** | 98.1% |

These percentages measure nonspace plaintext recovery on ciphers we generated.
They are not manuscript accuracy. Mean recovery falls from **96.6% to 86.5%** with
separate initialization: it is not a reliable general improvement and should
remain experimental. The two previously difficult cases do improve with the
longer conventional search versus its old 4,096 budget (68.5%/81.4% → 89.9%/98.3%).

The practical lesson is to maintain competing search strategies. A method can
improve manuscript language fit without improving known-text recovery overall;
that is a reason for stronger controls, not to declare it closer to the solution.

## Next decision

Keep Voynich as the decision point. The immediate substantive follow-up is a
paragraph-role-preserving null test and additional pages where page/paragraph
reset predictions differ. This directly tests whether the new gain reflects
manuscript layout rather than encryption state. If it does not survive, redirect
the effort to glyph grouping, word boundaries and language/corpus assumptions;
do not keep expanding table counts or search budgets to chase Latin-looking text.

The [research constitution](../../docs/RESEARCH_CONSTITUTION.md) now explicitly
requires bounded actual-manuscript trials after credible calibration improvements.
Synthetic success is a capability check, not the project deliverable.

## Reproducibility and checks

[Pre-execution protocol](../../docs/protocols/PHASE_INITIALIZATION_2026-10-09.md).
Execution revision `e272666` was clean. The clock diagnostic was added after the
planned search and is labeled post-hoc; it did not change or select any fitted key.

**56 registered runs, 229,376 evaluations, zero evaluator exceptions.** All runs
reached their planned limit. All database records, selected-candidate replays and
execution bindings were verified; all 14 initialization recipes reconstructed
from retained phase winners. Per-run `stopped / evaluation-limit` is the planned
termination, not an unfinished study.

- [Complete experiment export](evidence.json)
- [Comparisons and stable-word checks](comparisons.json)
- [All retained stage winners](stage_retention.json)
- [Run specifications](specifications.json) and [shared environment](environment.json)
- [Database, replay and initialization verification](verification.json)
- [Post-hoc clock diagnostic](clock_audit.json)

Regenerate the report without new searches:

```sh
uv run --locked python -m voynich.laboratory.phase_report \
  --input results/phase_initialization_2026-10-09/evidence.json \
  --previous results/line_rotation_2026-10-09/evidence.json \
  --output results/phase_initialization_2026-10-09 \
  --clock-audit results/phase_initialization_2026-10-09/clock_audit.json
```

Validation includes PostgreSQL integration, initialization accounting, deterministic
resume, line-context resets, phase-aware word agreement and common-coverage clock
comparisons. No new dependencies were needed.
