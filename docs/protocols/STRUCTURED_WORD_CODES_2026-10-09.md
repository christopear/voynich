# Stage 30: structured word codes, persistence and R2

Preregistered before execution. Ledger rows 10, 13, 14, 18; prospective row 19.
This is a **forward-model screen**, not blind decryption. A successful known-key
round trip is an engineering check, never evidence of a Voynich reading.

## Data and frozen split

Use stage-29 stored B_ZL_split_early (eight herbal folios × 64 tokens) for
development, B_ZL_split_late for reserved evaluation. Only those 512 development
tokens train both glyph construction and R2. Secondary unchanged-setting targets:
B_IT_split_late, B_ZL_join_late and A_ZL_split_late. These pages were examined
previously; they are reserved for this fit, not untouched data. No fit on A.

Plaintext is the four frozen cucina source panels from stage 28: seeds 7/19
development and 31/43 validation. Use the first eight 64-word passages of each.
Chapter halves remain disjoint. The dictionary contains all 1,484 normalized
types in the prepared recipe source, including unused ones; this is explicitly
transductive dictionary knowledge, not recovery of unseen words. Freeze one
dictionary/key across source panels and all manuscript comparisons. Recipes
are culinary, not a demonstrated medicinal source. This study tests one source.

## One bounded slot construction

Tokenize with existing compound EVA. For each development token with 2–10
glyphs, split into first glyph, intervening tuple (possibly empty), final glyph.
Keep the 16 most frequent first slots, 64 middle slots and 16 final slots,
ties resolved lexically, independent of page position. No other empty slots.
Enumerate all combinations, concatenate, and merge identical resulting strings,
summing their product-frequency weights. Count collisions and unique support.
This is a deliberately elementary edge/interior model, not an assertion that
these slots are morphological units. No unseen-slot fallback or exceptions.

Require at least 2V distinct strings for V source types; otherwise stop cipher
generation and report this construction's capacity failure. For seeds 101–106,
sample 2V strings without replacement using those weights; randomly permute the
sample and assign two ordered alternatives to lexically sorted plaintext types.
This is a random dictionary, not a frequency-optimised key. No key selection.
Report held-out token/type support coverage, including previously unseen types.
The grammar's maximum log2(support) is not achieved entropy or proof of capacity
for any particular distribution.

## Four cipher settings, six R2 settings

All binary choices have marginal probability 1/2 by the generative law:

1. IID: independently choose at every occurrence.
2. Page: choose once per page, use that alternative for every word on it.
3. Word-page: choose on the first occurrence of each type per page; reuse.
4. Refresh: as word-page, but at later occurrences refresh with probability 1/4,
   choosing a new fair bit (which may equal the old bit).

Reset state at page boundaries. Decoder is the reverse dictionary and needs no
variant state. Record realised variant frequencies, choices and refresh events,
peak stored bits, and negative log probability of the sampled random trajectory.
Do not interpret trajectory cost as additional secret decoder key. Charge an
explicit UTF-8 dictionary/grammar serialization and the uniform ordered
assignment reference log2((2V)!) separately; the latter is not the weighted
sampler's actual entropy. Report these as budgets, not a full MDL contest.

R2 is the existing mechanism_models copy generator: levels 0/1/2, coupling
0/1, unmodified windows/mutations. Train on the same development tokens with
their actual line/gap boundaries. Run a continuous 512-token stream (no page
resets, matching its existing implementation), then lay it on the same slots.
Seeds 101–106 development, 201–206 validation. Its lexical/trigram/edge training
data and configuration are charged as an explicit serialized model. Its random
choices are marginalized by replicated simulation, not optimized hidden states;
no total likelihood/MDL ranking against the cipher is claimed.

Cipher: 4 rules × 6 keys × 2 panels × 2 splits = 96 panels. Encoding seed is
10000 + 100*passage_seed + key_seed, reused across rules for reproducibility,
not a claim of perfectly paired random draws. R2: 6 settings × 6 seeds ×
2 splits = 72 panels. Total 168. No parameter expansion if no fit.

## Measurements, selection and reserved evaluation

All-type conditional MI uses 199 within-stratum permutations, seed 2901, and
the stage-29 additive estimator. Seven primary measures/scales:
TTR/.05, top-ten share/.04, section excess/.05, role excess/.05,
count≥5 section contribution/.05, mean glyph length/.5,
within-word next-glyph conditional entropy/.25. Entropy uses transitions between
adjacent glyphs only (no start/end symbols). No vocabulary cap. Record grammar
support coverage separately; no changing coverage threshold after observation.

For each family, select a setting by the smallest maximum absolute scaled
residual of its development median from the development manuscript vector;
ties by setting order. Freeze setting and all six cipher keys. Evaluate all
validation draws, separately by passage and seed; report each signed residual,
not just wins. Max residual ≤1 is a descriptive neighbourhood, not a calibrated
family rejection threshold. No claim of comparative support from proximity alone.

Order diagnostic: page-internal equality at token lags 1, 4, 16. Report observed
rate minus mean of 19 controls, seeds 3001–3019. Whole-word controls permute
within page and layout-role stratum. Line-order controls reorder complete
retained line chunks within page and paragraph-first-line status; chunks keep
their own metadata. This intentionally tests page-stream order, including
across lines/hard gaps; it does not assert adjacency across drawings. Different
line lengths move line-end positions, but token role counts are preserved.
Apply the same controls to every generated panel and every target. Report
movable line counts, null SDs and both effects; no grammar/meaning inference.

## Calibration and gates

Before reserved manuscript comparison: unit tests must verify slot collision
handling, hard dictionary capacity, exact round trips for all rules, state resets,
trajectory accounting and control preservation of page/role marginals. All 96
cipher panels must round-trip and replay, with no exception fallback.

Calibrate the profile-selection pipeline using 16 synthetic development targets:
each of four cipher rules × independent keys 701/702 × the two development
passages. Find closest development cipher-setting median with the same seven
scales. Require ≥12/16 within max residual 2 (looser diagnostic reliability gate,
distinct from the manuscript neighbourhood). If it fails, stop before manuscript
setting selection/reserved comparison; report the calibration limitation and
grammar coverage only. Do not loosen the gate. No blind solver is being tested.

For discrimination, leave each development seed out and classify its vector by
nearest remaining cipher/R2 family median (cipher medians exclude that key from
both passages). Report balanced accuracy. Require ≥0.80 before calling these
profiles discriminating between the two simulated families; this is a diagnostic
gate, not a p-value. No new fitted order classifier; shuffle effects are descriptive.

## Reporting and decision

If a rule reduces one mismatch but fails others, report that tradeoff. A surviving
profile only motivates a separate recovery/crib protocol, not a reading. If R2
also fits or classification fails, state non-identifiability. If neither fits,
record the exact model mismatch and stop this grid. No automatic new budgets.
Keep large codebook historical status explicitly unverified around 1420.

Output new results/structured_word_codes_2026-10-09 with protocol/source hashes,
training grammar, fixed keys, costs, generated tokens/audits, calibration,
selection, comparisons, controls and report. Register producers, update ledger.
No changes to historical results; no semantic label assignments in this stage.
