# Recovery pipeline: scorer and search diagnosis

Prospective engineering protocol, 10 October 2026. The user explicitly resumed
unknown-key recovery after the descriptive studies. This follows ledger row 17
(bounded grouped codes) and informs row 12; it does not reopen the whole-word
generator programme. This is not a manuscript hypothesis test.

## Phase A: the existing eight failures

Use the eight synthetic cases and blind-selected winners in
`results/parser_retention_2026-10-09/evidence.json`, with the original public
ciphertext, training slices and selected parsing policies. Reconstruct inputs
from the original specifications and verify source/prepared hashes. No new
manuscript data or sealed pages are read. Historical outputs are immutable.

For each winner, enumerate every distinct valid single-code reassignment and
two-code assignment swap under capacity two. Score each exactly with the
unchanged GroupedEvaluator. Retain the best neighbour, counts, costs and the
separate language/choice/key/policy components. Report whether a lower-cost
neighbour exists (tolerance 1e-9 total bits). This is an exhaustive certificate
only for this one-move neighbourhood, never for all keys.

As a separately labelled oracle diagnostic, score the known true active key
and its same neighbourhood. Truth must not affect neighbour enumeration or
loss selection. Only afterwards measure plaintext accuracy of the winners and
best neighbours. A wrong neighbour that out-scores the true key demonstrates a
local scoring preference problem; an improving neighbour of the returned key
demonstrates incomplete local optimisation. Both can occur simultaneously.

At most two complete neighbourhoods per case, at most 3,000 evaluations per
neighbourhood (including the centre); total cap 48,000. Count duplicate-free
scored candidates and report elapsed time. If a neighbourhood exceeds the cap,
stop and report incomplete rather than silently truncating a certificate.

## Phase B: decision before further recovery

If Phase A finds ordinary improving moves missed by search, specify and commit
a bounded systematic-neighbourhood continuation and an equal-budget random-move
comparison, preserving the scorer and starting candidates. This tests a search
procedure, not a new cipher hypothesis. No outcome-based budget expansion.
If it finds scoring defects, retain them as explicit limitations; do not tune
the scorer against the known test answers. A scorer change needs independent
training and a separately committed fresh-passage evaluation.

Historical examples are development cases. Any improved accuracy must be
reported as continuation with all historical and new evaluation costs stated,
not as independent blind recovery. A fresh synthetic calibration is required
before a manuscript attack; passing the old cases alone cannot authorize it.

The old f26r original has no admissible parser under this family's frozen
boundaries/expansion range. Even successful key optimisation would not change
that. A future manuscript trial needs an explicitly justified representation
and boundary protocol, full-pipeline recovery calibration, matched controls,
and unchanged-key transfer. Do not lower the old expansion threshold merely
to admit f26r, or claim a new decryption from language-model scores.

## Deliverables and stop

An import-safe numbered stage 39, reusable public-input search helpers, tests
of neighbourhood completeness and score replay, new dated results, and a ledger
update. Preserve truth in post-selection diagnostics. Save exact selected keys,
source/specification hashes, budgets and outcomes. This diagnostic reads existing
exports and does not create or modify historical PostgreSQL runs.

Conclude the bounded phase with a concrete decision: search remedy warranted,
scorer remedy required, or neither established. Do not replace this decision
with further aggregate-profile fitting. No cipher-family exclusion, novelty,
semantic interpretation or manuscript recovery follows from this stage.
