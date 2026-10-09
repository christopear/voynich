# All-survivor parser calibration — 9 October 2026

Prospective follow-up to grouped_boundary_2026-10-09, ledger row 17.
The previously observed eight calibration failures motivated this protocol.
No manuscript key searches are authorised by this protocol: this repairs a
calibration diagnostic, while the separate unit-association study returns to
actual manuscript data.

Keep the previous eight public ciphertext fixtures, training slices, grouping
constraints, spacing arms, seeds, beam width eight, evaluator and 4,096 proposals
per parsing policy. Change only parser retention: search EVERY structurally
admissible policy, without an entropy ranking cutoff. Previously observed survivor
counts total 177 (8–35 per case). Reuse the 32 already executed policy searches
only after exact execution-binding, source-hash and retained-candidate replay
checks. Run the remaining 145 policies, 593,920 new candidate evaluations;
724,992 evaluations represented including reuse. Independent case jobs may run
in four processes; no cross-case feedback or adaptive resource allocation.

Select by the existing total scoring function, tie-break by policy then candidate
ID. The truth and oracle key are used only AFTER all policies in a case finish.
Report separately: (1) true parser retained, (2) best blind output within the true
parser branch, (3) overall blind winner, (4) true-key oracle score. All nonspace
accuracy metrics remove line separators as in the previous study. A case passes
at >=90% nonspace recovery; report both seeds separately, not as independent texts.
This separates pruning, key optimisation, and final model-selection failures.
No increased budget, altered scorer, entropy inversion, new training or new keys.

Register new searches, link reused run IDs and preserve historical files. Retain
three candidates per policy and replay all selected payloads. Stop after all
177 policies are represented even if none passes. This is exhaustive over the
bounded parser grid, NOT over substitution keys or all grouped ciphers.
