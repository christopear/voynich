# Stage 41: fixed-budget escape from incorrect keys

Prospective engineering comparison, ledger row 17. The seven searched stage 40
cases are now exposed development data. Do not call this fresh calibration or
manuscript evidence. The eighth, parser-cap case is excluded explicitly because
it has no saved starting key; do not raise its cap.

From each stage 40 beam-selected key (before continuation), compare:

1. The unchanged stage 39 random greedy continuation.
2. Simulated annealing on exactly the same distinct single reassignment and
   two-code-swap neighborhood, accepting a positive total-bit cost increase d
   with probability 2**(-d/T). Cool geometrically from T=12 to T=0.2 over the
   proposal budget. These endpoints already exist in CodebookSearch; no tuning
   sweep is allowed. Keep and return the best scored key, not the final state.

Each arm gets exactly 8192 scorer calls including its starting score. No new
initializers, restarts, parser fitting or changes to GroupedEvaluator. Proposal
RNG seed is 39001+fixture seed; annealing acceptance uses an independent RNG
seed 49001+fixture seed. Uniform sampling can use compact move descriptors but
must match the existing exhaustive neighborhood's order and distribution.

Total optimization cap: 7*2*8192 = 114688 calls. Historical parser costs are
sunk common starting costs and remain separately reported. Rerun the greedy
arm and verify its saved key and components match stage 40 exactly. Count replay
checks separately. Save exact keys, components, accepted uphill moves and best
cost trajectory. No accuracy or transfer data may influence proposal generation,
acceptance or arm selection within a case.

After all runs, report every case's full and non-space edit accuracy, changes,
and count at >=90%. Report mean paired non-space accuracy difference on these
seven cases without pretending they are independent passages. The annealing
method advances to a separately preregistered fresh calibration only if mean
accuracy improves by >=5 percentage points, the >=90% count does not decrease,
and no case regresses by more than 10 percentage points. These are engineering
selection rules on exposed data, not statistical significance tests.

If the gate fails, do not tune the schedule or increase the budget within this
stage. A negative result applies to this continuation and schedule, not all
annealing or the cipher family. No manuscript trial follows either outcome:
fresh full-pipeline recovery and justified manuscript representation remain
required. No sealed manuscript data or additional plaintext corpora are read.
