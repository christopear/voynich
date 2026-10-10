# Historical pooling verdict audit — 9 October 2026

Post hoc audit of stage 24, motivated by the demonstrated stage-27 artifact and
Claude's uncommitted scratch results. We do not treat the quoted numbers as
locally reproduced evidence. Existing output inspection identified which cells
could change verdict when pooled metrics change.

P1–P4 (vocabulary/repetition) do not use the top-200 pool. Re-evaluate the stored
six-seed means/SDs and target bootstrap SDs using ONLY those four fingerprints,
with the original max-|z|<=3 rule. Cells failing any unchanged metric cannot
be rescued by altering pooled metrics. In current records, 16 configuration/window
cells survive in W1 and six in W2; only those 22 need further simulation.

Reproduce their six original seed runs (132 total), verifying original P6 exactly.
For both ZL windows recompute page MI using (a) first-occurrence ties, (b)
frequency then lexical-identity ties, (c) all types without pooling. Use original
20 permutations and RNG seed; calculate new target bootstrap SDs from 200
page-resamples using original bootstrap seed 20260926. Compare remaining cells on
P6 using new run SDs and new target SDs, without changing the original threshold.
This is a sufficient audit of the conjunction: if every cell fails either
unchanged P1–P4 or recomputed P6, every historical ZL family/window verdict
remains negative regardless of P5/P7–P9. It does not reproduce Claude's claimed
maximum changes to those other capped metrics or all IT/v101 verdicts.
If any cell survives, leave that cell's audit unresolved rather than claim the
old verdict stands. Store code, hashes, coverage and results in a new directory.
