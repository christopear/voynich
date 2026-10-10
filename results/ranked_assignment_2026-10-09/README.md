# Voynich: frequency-ranked codeword assignment

Stage 32, 9 October 2026. [Frozen protocol](../../docs/protocols/RANKED_ASSIGNMENT_2026-10-09.md),
committed at 8b728ab before execution. Evidence label: **search found no fit in
a bounded forward-model grid** for Currier B. No plaintext was recovered and no
key was searched for.

**In one paragraph.** Stage 31's codebook failed partly because random assignment
gave common plaintext words long codewords. Here the same 2,968 strings per key
are reassigned so the commonest recipe words get the most probable strings. That
fixes word length (4.41 vs Voynich 4.34–4.52; stage 31: 6.11). It also gives
Voynich's frequency/length relationship (Spearman −0.19 vs −0.17 to −0.26). Glyph
entropy now slightly undershoots (1.89 vs 2.07). Page association is exactly
unchanged, because relabelling cannot change which tokens repeat. Neighbour
coupling stays at zero, as predicted, so every Currier B target still fails.
Unexpectedly, the frozen model sits at the edge of the descriptive neighbourhood
for Currier A, where coupling is weak (4/12 draws within max residual 1). This
needs replication before it means anything.

## What changed and what did not

Everything is stage 31 Part C except the assignment. The shape model is
rebuilt and checked equal to stage 31's. The string set of each key is stage
31's exactly; strings are sorted by model probability and given in pairs to
plaintext types sorted by full-source frequency. One fair bit per type labels
the two alternatives.

Paired with stage 31 by key, rule and passage (96 pairs):

| Measure | Median change | Range |
| --- | --- | --- |
| Mean glyph length | −1.78 | −2.53 to −1.13 |
| Within-word glyph entropy | −0.385 | −0.529 to −0.229 |
| Section excess | 0.000 | 0.000 to 0.000 |

Predictions 1 and 2 hold; the unchanged page association confirms the
pipeline only relabels tokens.

## Development selection

Max scaled residual of development medians against B_ZL_split_early. Rule
residuals: TTR, top-ten, section, role, count≥5, length, glyph entropy, coupling.

| Setting | Max | Largest misses |
| --- | --- | --- |
| cipher IID (selected) | 2.30 | coupling −2.30; page association −1.2 to −1.3 |
| cipher page | 3.73 | section +3.73 |
| cipher word-page | 3.64 | section +3.64 |
| cipher refresh | 2.34 | coupling −2.34 |
| R2 level 2, no coupling (selected) | 2.10 | glyph entropy +2.07, coupling −2.10 |

Length and glyph entropy now lie within 0.6 scale units for every cipher rule.
The binding miss for the plausible rules is coupling. Calibration passed 16/16;
discrimination is 100% balanced accuracy between the simulated families.

## Reserved and sensitivity targets

| Target | Model | Joint hits | Best max | Section | Role | Length | Glyph entropy | Coupling | Within-hand |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B_ZL_split_early | cipher | 0/12 | 1.48 | 0.053 | 0.022 | 4.39 | 1.835 | 0.006 | 0.019 |
| B_ZL_split_early | Voynich | | | 0.115 | 0.086 | 4.34 | 1.981 | 0.120 | 0.089 |
| B_ZL_split_late | cipher | 0/12 | 3.76 | 0.067 | 0.027 | 4.41 | 1.890 | 0.006 | 0.045 |
| B_ZL_split_late | R2 | 0/6 | 4.67 | 0.175 | 0.072 | 4.79 | 2.653 | −0.014 | 0.097 |
| B_ZL_split_late | Voynich | | | 0.114 | 0.089 | 4.52 | 2.072 | 0.248 | 0.044 |
| B_IT_split_late | cipher / R2 | 0/12, 0/6 | 4.03 / 4.72 | | | | | | |
| B_ZL_join_late | cipher / R2 | 0/12, 0/6 | 2.42 / 3.36 | | | | | | |
| A_ZL_split_late | cipher | **4/12** | 0.95 | 0.067 | 0.016 | 4.41 | 1.890 | −0.007 | 0.067 |
| A_ZL_split_late | R2 | 0/6 | 2.04 | | | | | | |
| A_ZL_split_late | Voynich | | | 0.071 | 0.066 | 3.92 | 2.130 | 0.021 | 0.071 |

**The Currier A result is marginal, and unexpected.** The four hits have max
residuals 0.95–1.00. Each sits near the boundary on three measures at once:
length about +1, glyph entropy about −1, and role association −0.8 to −1.0.
All four come from one recipe passage (31); passage 43 gives none. The model was
trained on B shapes and selected on B pages. A's coupling target is near zero,
so the measure that defeats B does not bind there. This is a descriptive
neighbourhood result on one 512-token panel, not a fit to Currier A. Per the
protocol it requires replication (other A folios, other sources).

## What this changes

1. **Common short codewords for common words** reproduce Voynich's length and
   frequency/length structure on these pages. A historically natural design
   choice removes the stage-31 length failure.
2. **Coupling is now the single binding failure for B.** All other plausible-rule
   residuals are within about 1.3 scale units. Stage 33 tests context-conditioned
   variant choice under its own protocol.
3. Glyph entropy undershoots slightly: concentrating mass on probable strings
   makes the output a little too predictable. The tension is small (−0.6 scale).

No decipherment, reading, family rejection or comparative support is claimed.
Twelve draws are two passages × six keys. One culinary source.

## Verification

`python -m voynich.laboratory.ranked_verify` checks hashes, rebuilds the model
and codebooks, and confirms each key reuses stage 31's strings. It replays all
168 panels (49,152 cipher tokens round-trip) and recomputes calibration,
selection, every comparison and the paired differences. It also confirms R2's
panels are token-identical to stage 31's. Deviations: none.
