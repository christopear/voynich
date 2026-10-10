# Correction: drawing gaps, per-layout encoding and scribe wording (stages 31–34)

10 October 2026. **Post hoc correction** of implementation errors found in an
external review of PRs #13–#15. [Protocol](../../docs/protocols/BOUNDARY_CORRECTION_2026-10-10.md)
committed at f2aa309 before the rerun. Same panels as before, so this is a
correction, not fresh evidence. The stage 31–34 directories and their
producing code are unchanged and still replay; their READMEs carry dated notes
pointing here. Evidence label unchanged: **search found no fit in a bounded
forward-model grid**.

**In one paragraph.** Two shared bugs were real. The coupling measure and the
context-choice rule treated words separated by a drawing as neighbours (33
such pairs on the development pages, 10 inside the coupling statistic). The
secondary targets also reused ciphertext encoded on a different layout, which
matters for context choice (111–154 of 512 tokens differ). With both fixed and
all five grids rerun through the full frozen pipeline, every verdict stands: no
cipher grid or rule hits any Currier B target. The closest model (stage 33's
deterministic context choice on recipes) moves from development max residual
1.16 to 1.37, and on reserved B from 2.33 to 2.62. The stage-31 scribe sentence
was wrong in kind as well as wording, and is corrected below. A latent duplicate-
string bug in top-k enumeration changed nothing.

## Corrected grids versus the original reports

| Grid (original stage) | Selected cipher rule | Dev max: was → now | Reserved B best: was → now | Joint hits on B (any target, any rule) | Currier A hits (selected rule) |
| --- | --- | --- | --- | --- | --- |
| random_cucina (31 Part C) | iid | 3.60 → 3.60 | 4.28 → 4.33 | 0 | 0/12 |
| ranked_cucina (32) | iid | 2.30 → 2.27 | 3.76 → 3.70 | 0 | 4/12 → 4/12 (best 0.95) |
| context_cucina (33) | edge_max | 1.16 → 1.37 | 2.33 → 2.62 | 0 | 0/12 (best 1.13) |
| context_celsus (34) | edge_refresh | 2.83 → 2.89 | 2.90 → 3.82 | 0 | 0/12 |
| context_pliny (34) | edge_refresh | 3.85 → 3.79 | 3.44 → 3.82 | 0 | 0/12 |
| R2 (all grids) | level 2, no coupling | 2.10 → 2.11 | 4.67 → 4.66 | 0 | 0/6 |

Calibration passed 16/16 in every grid; discrimination is 100%. Corrected
manuscript coupling: development B 0.124 (was 0.120); reserved B 0.248, IT 0.253
and joined 0.183 (unchanged, since those panels' only drawing pairs were outside
the statistic); A 0.023 (was 0.021). The corrected edge_max cipher gives median
coupling 0.093 on development pages and about 0.09 on reserved B, roughly 37–75%
of the manuscript values.

Celsus's reserved best worsens (2.90 → 3.82). The reserved B layout has only two
drawing pairs, but whether a choice has context changes how many random numbers
the encoder consumes. Every later choice on that page then shifts, so 36 of the
48 context-rule records on that layout differ in tokens. The old 2.90 was the
single best of twelve draws; the others lay at 3.43–5.42. Best-of-twelve is
noisy and should not be read as a trend. Unselected
rules: Currier A neighbourhood draws now appear for ranked iid (4/12) and for
context `edge` (2/12, was 3/12). These still come from the one recipe passage,
and they are not a fit.

## Scribe statement, corrected

The stage-31 sentence "about 29% of B's association lies between hands" is
withdrawn. The chain rule I(W;P|S) = I(W;H|S) + I(W;P|S,H) holds for **raw** MI:
on B_ZL_split_full, 2.820 = 0.832 + 1.987 bits, with zero residual on every
panel. It does not survive separate permutation corrections. Subtracting the
corrected estimates gives 0.039 bits, while directly corrected I(W;hand|section)
is 0.0995 bits.

What can be said:

* Conditioning on attributed hand reduces B's corrected page-association
  statistic by 29% (0.135 → 0.096 bits) on the 16-folio panel, by 23% on the
  joined-space and development panels, and by 21% in IT.
* Directly measured, corrected word/hand association in B is 0.0995 bits. Twelve
  plaintext passages laid on the same pages, with the same hand groups, give
  −0.026 to 0.054. B's word choice is more associated with attributed hand than
  topic variation produces in these plaintexts on the same page groups.
* Neither number allocates information to scribes or establishes that scribe
  causes the vocabulary differences. Hand overlaps with quire and section here.

## Other corrections

* **Enumeration:** canonical-path top-k equals the original list exactly in all
  12 stage-31 arm/order/k cases, with zero coverage change. The latent bug did
  not affect reported numbers. Corrected code is `boundary_correction.canonical_top`.
* **Wording:** "with two alternatives, one choice cannot do both" (stage 33)
  becomes "the tested rules did not achieve both page association and coupling".
* **Fresh pages:** the reserved panels have now informed four successive
  hypotheses (stages 31–34). Future positive evidence must use folios not used
  in stages 27–34.

## Verification

`python -m voynich.laboratory.boundary_correction_verify` checks hashes. It
confirms every grid's codebooks equal the stored stage outputs and regenerates
the R2 streams. It re-encodes and re-profiles every record on its own layout,
recomputes calibration, discrimination, selection, comparisons, all-rule tables,
the scribe tables and the enumeration check. Unit tests use real transcription
lines with `<->` and `,` gaps.

Files: `evidence.json` (all grids), `generated_<grid>.json`,
`calibration_<grid>.json`, `r2_streams.json`, `scribe.json`, `enumeration.json`,
`slots.json` (targets with `gap_after`), `manifest.json`, `verification.json`.
