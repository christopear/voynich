# Stage 40: frozen recovery pipeline on disjoint passages

Prospective synthetic calibration, ledger row 17. Commit before generating
fixtures or running recovery. Stage 39 chose random greedy continuation using
old examples; this study tests that fixed choice on different passages and keys.
It does not repair the original f26r parser infeasibility or authorize a
manuscript search.

## Fixed data and encoder

Keep the historical normalized training slices: Celsus for Latin, Dante for
Italian, starting at floor(0.3 * length), length min(12000, floor(0.2 * length)).
Targets are Pliny and Dante respectively. Use 350-character slices starting at
floor(0.75 * target length) and floor(0.80 * target length), stripped at the
edges. These differ from the earlier floor(0.70 * length) passage. Verify no
overlap with that passage or training, and record raw/prepared hashes and exact
offsets. These are fresh for this grouped recovery comparison, not a claim
that these source books were never used anywhere in the project.

Use the existing grouped_boundary.fixture encoder, first passage key seed 31,
second seed 43, each with preserved and encoded spaces: eight cases, four
distinct plaintext passages. Keep the same two homophones, 16 glyph alphabet,
three long-code prefixes and hard span boundaries. No replacement of difficult
or inadmissible fixtures. Known-key round trips are fixture validation only.

Also encode 350 characters beginning 1000 characters after each target offset
under its unchanged key, with independent emission seeds 140001+key_seed+line.
Decode only with the selected fitted key/policy, marking unseen codes as '?'.
No learning, completion of mappings or selection on transfer scores. Verify all
target/transfer intervals are disjoint from training, each other and the old
grouped passage. Reject an overlapping specification before searches.

## Frozen search, truth separation and budgets

Enumerate every structural survivor with screen_policies (expansion 1.35–2,
capacity two), sorted by prefixes, without unigram pruning. If there are more
than 64 survivors, record a budget-screen failure for that case without
searching a subset; zero survivors also fails. This bounds the study at
8 * (64 * 4096 + 8192) = 2,162,688 optimization calls.

For each surviving parser run the existing CodebookSearch beam (width eight,
batch eight, 4096 evaluations including initialization), fixture seed as search
seed, and unchanged GroupedEvaluator. Retain the lowest-loss evaluated candidate
per parser, ties by candidate id. Choose the lowest-loss parser winner, ties by
prefixes then candidate id. Refine only that selected key with stage 39 random
greedy descent: 8192 calls including the starting score, seed 39001+fixture seed.
No oracle parser is given to the search. No post-refinement parser switching,
additional starts, scorer changes, dictionary hints or extra budgets.

Save public inputs separately from fixture truth. Complete all loss-based
selection before evaluating accuracy or true-parser retention. Report all
parser budgets and invalid calls. Save every parser winner and selected refined
key so their component scores can be independently replayed. Workers may run
independent cases but cannot affect per-case proposal order.

## Outcomes and fixed decision

Report before/after non-space and full edit accuracy, encoded-space boundary F1,
true parser retained/selected, transfer accuracy including '?' errors, glyph
coverage, and elapsed time. Report every case, not the best seed. This is a
single-arm pipeline validation; it does not establish an equal-budget advantage
over another algorithm. The beam-only result is its cheaper intermediate state.

The local recovery gate is at least 6/8 cases with >=90% non-space edit accuracy,
including at least one pass in each language/spacing cell, and all eight true
parsers retained. Separately require at least 6/8 transfer cases with >=90%
non-space accuracy (unknowns count as errors) for a transfer gate. With only
four distinct passages these are engineering checkpoints, not population
confidence claims. A pass still requires manuscript-appropriate conditions
and a justified representation before a manuscript attack.

If either gate fails, report whether failures involve missing parsers, wrong
parser selection, or recovery with the correct parser. Do not infer universal
family exclusion or tune against these new answers. Stop this bounded study;
any remedy needs a new prospective protocol. Report development selection costs
from stage 39 separately, not as fresh-run costs. No manuscript pages or sealed
confirmation data are loaded.
