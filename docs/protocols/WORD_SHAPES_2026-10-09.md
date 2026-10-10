# Stage 31: scribe control, dependent word shapes, then codebooks

Preregistered before execution. Ledger rows 13, 14 and 19; prospective row 20.
Three parts, run in order. Part C runs only if Part B's frozen gate passes.
This is a **forward-model screen**, not blind decryption. Known-key round trips
are engineering checks, never evidence of a Voynich reading.

## Why this stage

Stage 30's slot grammar treats first glyph, middle and final glyph as
independent. Its own samples give about 2.83 bits per within-word glyph
transition against Voynich's 1.98 on development pages, so the entropy gap
comes from the grammar, not from how codewords were assigned. Stage 29 found
that 88% of B's page association comes from types seen at least five times, but
did not ask whether scribe accounts for part of it. Stage 30 never scored
the n/l/r ending → next-initial coupling, which is the most robust structural
finding about Voynich word order.

## Exploratory scoping already done (declared, development data only)

Before writing this protocol, on B_ZL_split_early and on the broad B training
pool defined below (reserved folios excluded):

* H(last glyph) = 2.27 bits, H(last | previous glyph) = 0.88 (pool: 2.29/0.91);
  H(second | first) = 1.73. The final glyph is strongly predicted by its
  predecessor, not merely drawn from a small ending inventory.
* The coupling statistic below on B_ZL_split_early: excess 0.127 bits,
  null SD 0.031, n = 145 records. On stage-30 development cipher panels its
  medians were 0.009–0.035; R2 settings ranged −0.005 to 0.171.
* The ZL `$H` variable carries Lisa Fagin Davis's hand assignments (voynich.nu
  transliteration notes, item 25; `$C` is Currier's hand). Stage-29 B
  development folios: seven hand 2, one hand 5. B reserved: three hand 2,
  three hand 5, two hand 3. All sixteen A herbal folios are hand 1.

No reserved-page model comparison, shape model fit or Part A stratified value
was computed before this protocol was committed.

## Part A: scribe-stratified page association

Data: all 24 stage-29 A/B panels (ZL/IT × split/join × full/early/late) and
the five `previous_*` panels, reading `slots.json` unchanged. Hand is attached
from the ZL page header `$H` by page identifier (also for IT panels, as with
stage 29's Currier metadata). No page is dropped.

Statistic: the stage-29 additive decomposition (199 within-stratum
permutations, seed 2901, all types, count bins). Compute four versions:
section strata; section × hand strata; section × roles; section × roles × hand.
Since hand is a function of page, I(W;P|section) = I(W;H|section) +
I(W;P|section,hand). Report the hand-stratified excess, the difference
(between-hand component), retained share = stratified/unstratified, and the
count≥5 bin under both.

Reference: lay each of the twelve stage-28 plaintext passages (cucina, celsus,
pliny × four 1,024-word passages) on the B_ZL_split_full layout (same rows,
pages and hands) and compute the same four versions. This measures how much a
text with no scribe effect loses from the same stratification, including topic
variation that coincides with hand groups.

Calibration (must pass before Part A interpretation): a synthetic 1,024-token
layout of 16 pages × 64 tokens, hands assigned as in B_ZL_split_full
(ten/four/two pages, in that page order). Twenty seeds each:
(i) IID tokens from 128 types: mean |excess| < 0.01 under both strata;
(ii) hand-level vocabularies (tokens drawn from a hand-specific 64-type set, no
page effect): unstratified mean excess > 0.1 and stratified mean |excess| < 0.02;
(iii) page-level vocabularies within hand (page-specific 16-type sets):
stratified mean ≥ 0.8 × unstratified mean. A panel whose hands are all equal
must give identical stratified and unstratified values exactly (checked on A).

Interpretation (descriptive): B's hand-stratified section excess is reported as
an alternative target alongside the stage-29 value; it does not replace the
primary target in Part C selection. If B's retained share is below the minimum
retained share of the twelve references, state that hand grouping removes more
of B's association than coincident topic variation removes from these
plaintexts. Otherwise state that the stratification does not distinguish scribe
from content. Hands are a palaeographic attribution, not ground truth; scribe and
section/quire are partly confounded in sixteen folios.

## Part B: word-shape models without a cipher

Tokenizer: compound EVA (`eva_glyphs`), as stage 30.

Training arms:

* **matched**: the 512 B_ZL_split_early tokens (stage 30's training data);
* **broad**: every clean ZL token on a Currier B page (`$L=B`, any section),
  excluding all folios of B_ZL_split_late. It includes development folios.

Evaluation targets: B_ZL_split_late (primary), B_IT_split_late,
B_ZL_join_late, A_ZL_split_late (sensitivities; A is a transfer test).

Models:

* **S0**: stage-30 `SlotGrammar.fit` on the arm (16/64/16 slots, 2–10 glyphs).
* **N1, N2, N3**: glyph n-gram models with context length k = 1, 2, 3, padded
  with k start symbols and one end symbol. Interpolated Witten–Bell smoothing:
  P(g|h) = (c(h,g) + T(h)·P(g|h')) / (c(h) + T(h)), with T(h) the number of
  distinct continuations of h and h' the context without its oldest symbol.
  The empty context interpolates with a uniform distribution over the training
  inventory plus the end symbol and one UNK symbol. Unseen glyphs score as UNK.
  No other hyperparameters.

Order selection per arm: leave-one-folio-out cross-entropy over the arm's
training folios (bits per glyph including the end symbol, pooled over folds).
Choose the lowest; ties go to the lower order. S0 is not eligible because it
assigns zero probability outside its support; it is reported as a baseline.

Primary measure: reserved token-weighted cross-entropy, bits per glyph including
end symbol. Type-weighted cross-entropy is secondary. For S0, report support
coverage and the cross-entropy restricted to covered tokens only, labelled as
not comparable.

Sampling diagnostics: 20 samples × 512 words per model, seeds 3201–3220. UNK
is never sampled (renormalized); samples longer than 15 glyphs or empty are
rejected and redrawn. Measure: within-word adjacent-glyph conditional entropy
(stage-30 `glyph_h`, no boundary symbols), mean glyph length, last-glyph
dependence D_last = H(last) − H(last | previous) and D_second = H(second) −
H(second | first) over words of at least two glyphs. Report medians and ranges,
against the same quantities on each target's 512 observed tokens.

Coverage/capacity: enumerate each model's most probable distinct strings
exactly by best-first search (no UNK, at most 15 glyphs; S0 by weight). At
K = 2,968 (stage-30 codewords required) and K = 14,336 (stage-30 support), report
token, type and previously-unseen-type coverage of each target, where unseen is
relative to the arm's training types. Reference: the arm's own K most frequent
observed types (memorisation comparator, fewer if the arm has fewer types).

**Shape gate** (frozen; each arm's selected model, on B_ZL_split_late):

1. |median sample glyph_h − observed| ≤ 0.25;
2. |median sample D_last − observed| ≤ 0.25;
3. |median sample mean length − observed| ≤ 0.5;
4. top-2,968 token coverage ≥ 0.549 (stage-30 grammar's coverage at 14,336).

Cross-entropy has no threshold; it selects order and is reported. If no arm's
selected model passes, Part C is not run; report the shape result only.

## Part C: codebooks on the selected shape model (conditional)

Arm: broad if its selected model passes the gate, else matched. R2 is trained on
the same arm's lines (matched: stage-30 `training_lines`; broad: the arm's ZL
lines with their own clean flags and gaps). Same R2 six settings and seeds.

Plaintext, dictionary, rules, seeds and panel counts are exactly stage 30's:
four cucina passages (first 512 words), the 1,484-type dictionary, two disjoint
alternatives per type, rules iid/page/word_page/refresh (refresh 1/4), key seeds
101–106, encoding seed 10000 + 100·passage + key, page resets. 96 cipher panels
and 72 R2 panels.

Codebook construction: for key seed s, draw words from the selected model with
`numpy.random.default_rng(s)` (same rejection rules as sampling diagnostics),
keeping first occurrences until 2,968 distinct strings are collected; this is
successive sampling without replacement proportional to model probability.
Shuffle with the same generator, then assign consecutive pairs to lexically
sorted plaintext types, as in stage 30. Random assignment only; no
frequency-matched or context-conditioned assignment in this stage.

Measures: stage 30's seven (same scales) plus **coupling** (scale 0.05): over
adjacent token pairs in the same line with no hard gap (row i+1 has the same
locus and start = end + 1), left token of at least two glyphs ending in n, l or
r; MI(terminal; next token's first glyph) minus the mean of 199 permutations of
next-initials within page (seed 3101). Generated tokens are laid on the
target's rows exactly as in stage 30.

Prediction stated in advance: random assignment chooses each codeword without
regard to its neighbours, so cipher coupling should stay near zero and fail
the coupling residual. A cipher pass on coupling would be a surprise to examine.

Selection, calibration and reserved evaluation follow stage 30 with the eight
measures: development median closest to B_ZL_split_early by maximum scaled
residual, ties by setting order; the 16-target synthetic calibration gate
(≥12/16 within 2) before manuscript selection; leave-seed-out discrimination
(≥0.80 balanced accuracy for "discriminating"); validation on B_ZL_split_late,
B_IT_split_late, B_ZL_join_late, A_ZL_split_late. Neighbourhood max residual
≤ 1 is descriptive, not a calibrated rejection threshold. Report all signed
residuals. Secondary: hand-stratified section excess for targets and selected
draws (descriptive, not used in selection). The stage-30 lag/order diagnostic
is dropped; stage 30 found it did not separate manuscript from either model.

Costs: report the shape-model serialization (counts) as an explicit budget
alongside stage 30's dictionary/assignment references. No MDL ranking.

## Not in this stage (declared)

Stolfi's and Zattera's published word grammars were intended as fixed outside
baselines. Their source pages were unreachable from this session (HTTP 404), and
implementing them from memory would not be a faithful baseline. They are deferred.
Context-conditioned variant choice (choosing the alternative that suits the
next word) is a separate hypothesis for a later protocol, not a Part C repair.

## Gates, checks and reporting

Unit tests before running: Witten–Bell distributions sum to one over the
alphabet for every context; best-first enumeration equals brute force on a
small model; hand-stratified decomposition equals the unstratified version when
all hands are equal; coupling records respect line and hard-gap boundaries;
codebook strings are distinct and round-trip for all rules.

Every generated cipher panel must round-trip. Every generated record is stored
and replayable by a verify module. Output: new `results/word_shapes_2026-10-09`
with protocol/source hashes, Part A tables and calibration, Part B models,
selection, diagnostics, coverage, gate, Part C (if run) panels, calibration,
selection and comparisons, plus a README with an evidence label. No historical
results changed. Register producers and update ledger rows 13, 19 and the new row.
