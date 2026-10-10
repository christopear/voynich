# Stage 42: prospective comparison and reproducibility of recovery methods

Objective: identify a defensible, repeatable grouped recovery method, or conclude
that none of these bounded methods is sufficiently reliable. Ledger row 17.
Stage 41's annealing selection gate failed and stays failed. Here it is an
unqualified comparator in a new prospective falsification study, not a promoted
solver. Do not retroactively claim this validates the old gate.

## Frozen cases

Keep stage 40's encoder, 350-character target/transfer lengths and training
slices. New target offsets are floor(0.85*length) and floor(0.90*length), in
Pliny and Dante, with fixture key seeds 59 and 71 respectively, each in preserve
and encoded spacing: eight cases, four distinct target texts. Transfer begins
1000 characters after each target offset and uses emission seeds
240001+fixture_seed+line. Verify interval disjointness against training and all
stage 40 targets/transfers and the original floor(0.70*length) target. No fixture
replacement based on difficulty, parser count or outcomes. Corpus lengths were
checked for planning; new fixture contents/results have not been inspected.

For each case use search seeds 101, 202, 303 independently of the fixture key.
For each seed search all structural survivors as before, with a maximum of 64;
above that cap, search none and count a failure for every method. Every parser
gets 4096 beam calls including initialization. Pick its best evaluated key and
choose the parser by the existing loss/prefix/candidate-id rule. Keep that
parser fixed for all three paired refinements:

* Greedy: 8192 calls, unchanged random greedy descent.
* Annealing: 8192 calls, unchanged stage 41 temperature 12 to 0.2.
* Portfolio: 4096 greedy calls and 4096 annealing calls, both from the same beam
  winner. Select the lower total-bit-cost result, ties by candidate id. No
  truth, seed agreement or transfer information enters this selection.

Proposal seed 39001+search_seed; annealing acceptance seed 49001+search_seed.
Portfolio halves use those same seeds; they are not selected from full-budget
arms. Charge both starts. No parallel-trajectory best-of is called free.
There are 24 paired trials, up to 6881280 optimization calls total
(24*(64*4096+3*8192)). Shared parser cost is charged once in this experiment,
and per standalone method deployment; method refinement budgets are equal.
Workers can execute independent trials without changing their proposal order.

## Truth separation and reporting

Save fixture truth separately. Finish all searches before accuracy assessment.
Report every seed separately, parser counts and selection, before/after full
and non-space edit accuracy, >=90% success, unchanged-key transfer with unknowns
counted as errors, glyph coverage, and cost components. No tuning or reruns to
obtain a better seed. Distinguish structural/budget failure from key failure.

For each method/case, a public stability flag requires identical selected parser
prefixes across all three seeds and minimum pairwise positional agreement >=95%
over decoded positions where at least one of the pair is non-space. Differing
decoded lengths fail the flag. Compare this flag with actual >=90% recovery
in all three seeds; any flagged-but-wrong case invalidates an interpretation of
agreement alone as a correctness certificate. This is diagnostic, not a way
to choose a seed or repair a key.

## Fixed criteria and stopping conclusion

A method qualifies on this small clean panel only if, for EACH search seed,
at least 6/8 cases reach >=90% recovery AND >=90% transfer; at least one success
in each language/spacing cell for recovery and transfer; and true parsers survive
in all eight cases. Additionally, at least 6/8 cases must meet both accuracy
thresholds in ALL three seeds. Do not pool successful seeds to claim success.

Report the three methods independently. If multiple qualify, report all; do not
select using the new answers and label the winner independently validated.
If none qualifies, state that none is defensible as a reliable decoder under
these conditions, even if one improves mean accuracy. Report stable supported
subclaims (e.g. parser retention, optimization gains) separately from recovery.
No manuscript attack or another parameter sweep follows a failure in this stage.

The result does not establish performance on other languages, longer texts,
uncertain boundaries, damaged transcription, other cipher families or Voynich.
It does not repair original f26r infeasibility. A qualification is conditional
engineering evidence, not decipherment or universal reliability. Preserve all
historical gates/results and provide a consolidated methods assessment so the
user receives a conclusion rather than another isolated score table.
