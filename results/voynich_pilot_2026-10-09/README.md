# Actual Voynich page-search pilot — 9 October 2026

**We can improve Latin-like statistics on actual Voynich text. We do not yet have
an evidence-backed partial decipherment.**

[Open the operating report](report.html) to inspect all 16 original-page candidate
outputs, their unchanged-key transfer to another page, controls and mappings.
[Full evidence](evidence.json), [comparisons](comparisons.json),
[registry reconciliation](verification.json), [execution environment](environment.json)
and [run specifications](specifications.json) preserve the results.

## What ran

48 searches, 196,608 registered candidate evaluations, zero captured evaluator
exceptions. Each run exhausted its planned 4,096-proposal budget, so PostgreSQL
correctly labels it `stopped / evaluation-limit`; the study completed. An additional
384 initial-state re-scores establish the baseline outside the search budgets.
All 48 run IDs, specification hashes, evaluation counts and selected outputs were
reconciled with PostgreSQL.

Search on **f26r** (76 retained words), unchanged-key transfer to **f31r** (81 words).
Both are Currier B herbal pages, annotated hand 2. These are not untouched research
holdouts. Seven and 13 ambiguous token spans were omitted respectively; the full
omission logs and loci are exported. Filtering closes gaps and assumes surviving
spaces are plaintext word boundaries.

Compare raw EVA characters and six conventional compound glyphs; one-to-one
substitution and mappings allowing at most two observed cipher units per Latin
letter; beam and annealing; seeds 7 and 19. Each has symbol-shuffled and whole-word-
shuffled controls. Celsus supplies the search model; Pliny evaluates selected
outputs without steering search. No Italian model or arbitrary segmentation search.

## What improved

Beam found a lower fitted objective than annealing in **6/8** original-page pairs.
All original searches improved their objective **26.1–42.8%** over the best of the
shared eight initial candidates. These are score improvements, not accuracy.

Character language costs below exclude key/choice penalties and include spaces.
Numbers are averages across the two seeds; lower is better. Only compare start and
finish within a row: representations have different input units and output lengths.

| Beam configuration | Initial Celsus bits/character | Fitted f26r | Independent Pliny on f26r | Independent Pliny on frozen f31r |
|---|---:|---:|---:|---:|
| Raw EVA, one-to-one | 6.758 | 4.730 | 4.770 | 5.307 |
| Raw EVA, capacity two | 7.175 | 4.087 | 4.014 | 4.251 |
| Compound EVA, one-to-one | 7.719 | 4.857 | 5.090 | 5.539 |
| Compound EVA, capacity two | 7.184 | 4.272 | 4.161 | 4.642 |

For context, unsearched ordinary Celsus and Pliny passages scored **2.709 and
2.524 bits/character** under the Pliny model. These are two illustrative 600-character
anchors, not calibrated acceptance thresholds. All original frozen transfers had
100% symbol coverage, so their poor readings cannot be blamed on missing codes.

## Why this is not a partial decryption

- Original text beats symbol-shuffled controls **16/16** times: the optimizer finds
  real structure in the manuscript's recurring word shapes.
- It beats whole-word-shuffled controls only **6/16** times on fitted loss, and
  **9/16** times on frozen transfer under Pliny. That supplies no consistent
  advantage for the original sequence in this small screen.
- Mappings are unstable: across the two seeds, token-weighted letter assignment
  agreement is **2.1–37.7%**, depending on configuration. Agreement is not accuracy.
- Outputs remain strings of mostly Latin-like fragments. We have not established
  a correct letter, word, or sentence through independent evidence.

A concrete trap: one run renders the frequent `qokedy` as **febris** (Latin for
fever). Other raw-EVA one-to-one runs render it `videra`, `solita`, or `fiatus`.
The surrounding text is not coherent Latin. Optimizing against medical Latin
makes a medical-looking word possible without identifying its actual meaning.

A bijective substitution cannot change symbol entropy, equality patterns or word
lengths; it can improve their alignment with Latin n-grams. Homophonic merging is
more flexible but still fixes lengths. Neither model handles omitted spaces,
nulls, changing tables, abbreviations, syllables, or unknown glyph grouping.

The four-character scorer is also limited in detecting syntax. Failure against
word-shuffle does not prove absence of meaningful word order, nor exclude these
cipher families. Two seeds and two control realizations cannot support significance
or posterior probability claims. These results are optimization diagnostics.

## Next decision

Keep this as the actual-manuscript baseline. More beam budget alone is not yet a
well-supported route to decipherment. First align encoder/scorer assumptions and
calibrate alternative glyph grouping, letter/pair units and uncertain spaces on
synthetic text with a Voynich-sized alphabet. Improve the language scorer's ability
to prefer correct medical Latin over its plausible-looking competitors. Then
repeat this controlled manuscript comparison with the calibrated richer model,
looking for stable mappings and independent-page predictions, not isolated words.

## Reproduction and verification

The [pre-execution protocol](../../docs/protocols/VOYNICH_PILOT_2026-10-09.md)
defines selection and interpretation. Search execution began with a dirty tree;
`environment.json` records the exact source hashes and starting revision. The
executed pilot implementation is preserved in commit `7482dbb`. A later parser
guard prevents words inside annotations leaking into future inputs; both selected
page inputs and omission logs were checked identical to the executed export.

```sh
uv run --env-file .env --locked python -m voynich.laboratory.voynich_pilot \
  --output results/runs/NEW-voynich-pilot
uv run --locked python -m voynich.laboratory.voynich_pilot_report \
  --input results/runs/NEW-voynich-pilot/evidence.json \
  --output results/NEW-voynich-report
```

The registry rejects identical registered specifications unless a rerun reason is
provided through its API; output directory alone does not authorize duplication.
The CLI creates a fresh study and is not a study-level resume command. Per-run
checkpoints are retained through the existing runner.

Validation: **154 tests passed**, including PostgreSQL integration and the new
transcription/control/coverage/report tests. Package build passed; report inspected
in the browser. No additional Python dependencies were needed.
