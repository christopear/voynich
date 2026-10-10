# Correction: drawing gaps, per-layout encoding and scribe wording (stages 31–34)

Committed before the corrective rerun. This is a **post hoc correction** of
implementation errors found in an external review of PRs #13–#15. It is not a
new hypothesis and not fresh evidence: it reuses the same development and
reserved panels. Historical result directories are not overwritten. Their
producing code is left unchanged so they still replay, and each gets a dated
correction note.

## Defects (all confirmed locally before this protocol)

1. **Drawing gaps counted as neighbours.** `word_shapes.coupling_records` and
   `context_choice.successors` treat consecutive word indices on one line as
   adjacent. Words separated by a drawing (`<->`, gap kind `drawing`) also have
   consecutive indices. B_ZL_split_early has 33 such successor pairs, 10 of
   them in the coupling statistic. A_ZL_split_late has 26 (1 in the statistic);
   the reserved B panels have 2 each (none in the statistic). Unit tests skipped
   indices instead of using real gap metadata, so they missed this.
2. **Secondary layouts reused ciphertext encoded for B_ZL_split_late.** For the
   stage-33 context rules, the choice depends on line and boundary structure.
   Re-encoding one draw on IT, joined-space B and A layouts changes 111, 133 and
   154 of 512 tokens. Page-only rules (stages 31–32) are unaffected, because
   all these panels place 64 tokens per page. They are re-encoded anyway for
   uniformity.
3. **Overstated scribe allocation.** Stage 31 described the difference between
   two independently permutation-corrected estimates as the share "between
   scribes". The chain rule holds for raw MI (raw between-hand term 0.832 bits
   on B_ZL_split_full). It does not survive different corrections: the corrected
   difference is 0.039 bits, while directly corrected I(W;hand|section) is
   0.0995 bits. The defensible statement: conditioning on attributed hand
   reduces this page-association statistic by about 29%.
4. **Latent: duplicate strings in `NGramModel.top`.** Compound EVA lets
   different glyph paths spell the same string (for example `c`,`h` and `ch`),
   so top(k) can repeat strings. The external check found all six stage-31
   top-14,336 lists unique. This rerun recomputes stage-31 Part B coverage with
   canonical-path enumeration and reports any difference.

## Corrections

* **Neighbour rule:** token i+1 is i's neighbour only if both are on the same
  line, `start(i+1) = end(i) + 1`, and the transcribed gap after token i is
  `ordinary` or `uncertain`. A `drawing` gap or line end gives no neighbour.
  Gap kinds come from the panel's own transcription lines (ZL or IT2a), read
  from the gap following token i's last word. The rule applies to the coupling
  measure and to context successors.
* **Per-layout encoding:** every cipher draw is encoded separately on each
  target's own rows (same key, rule, plaintext and encoding seed). R2 output is a
  continuous stream independent of layout, so its tokens are reused and its
  profiles recomputed on each target.
* **Enumeration:** canonical paths only (a path counts only if `eva_glyphs` of
  its concatenation returns the path), and distinct strings.
* **Scribe wording:** report the reduction from conditioning on hand. Report
  the directly corrected I(W;hand|section) separately, with the raw chain-rule
  terms. Make no allocation claim from differencing corrected estimates.

## Rerun scope (frozen designs, corrected code)

Five grids, each with stage 31–34's frozen design: development selection by
maximum scaled residual over the eight measures, the 16-target calibration gate
(≥12/16 within 2), leave-seed-out discrimination, and comparisons on all five
targets:

| Grid | Original stage | Codebook | Rules |
| --- | --- | --- | --- |
| random_cucina | 31 Part C | random assignment | iid, page, word_page, refresh |
| ranked_cucina | 32 | frequency-ranked | iid, page, word_page, refresh |
| context_cucina | 33 (= 34 cucina) | frequency-ranked | iid, edge, edge_max, edge_refresh |
| context_celsus | 34 | frequency-ranked | as above |
| context_pliny | 34 | frequency-ranked | as above |

Codebooks, plaintexts, seeds, lift table, shape model and R2 are exactly as
before; verification checks codebook equality with the stored stage outputs.
Also recompute the stage-31 Part A table with the direct hand measure, and Part B
top-k coverage with canonical enumeration.

## Decision rules

* Corrected numbers supersede the affected ones in the ledger and reports.
  Verdicts change only if the corrected numbers change them.
* The reserved panels have now informed several successive hypotheses. Any
  corrected joint hit is reported, but it counts only as a reason to test on
  fresh folios under a new protocol, not as compatibility evidence.
* Wording: "two alternatives cannot do both" becomes "the tested rules did not
  achieve both".

## Checks

Unit tests use real transcription lines with `<->` drawing gaps and uncertain
`,` gaps, and confirm coupling and successors drop drawing pairs. They also
check that canonical enumeration returns distinct strings on a toy model with
compound collisions, and that per-layout encoding round-trips. A verify module
replays every stored record and re-derives every reported number. Output:
`results/boundary_correction_2026-10-10`.
