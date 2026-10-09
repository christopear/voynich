# Stage 32: frequency-ranked codeword assignment

Preregistered before execution. Ledger row 20; prospective row 21. This is a
**forward-model screen**, not blind decryption. Known-key round trips are
engineering checks, never evidence of a reading.

## Question and motivation (declared post hoc origin)

Stage 31's codebook drew 2,968 distinct strings from a word-shape model that
passes the frozen shape gate, then assigned them to plaintext words at random.
Codewords came out too long (6.1 vs 4.3–4.5 glyphs). A labelled post hoc check
found Voynich B's common types are short (type frequency/length Spearman −0.31)
and the random codebook's are not (+0.14). This stage tests the most direct
repair as a **new, stated mechanism**: the encoder gives its most common
plaintext words the most probable, typically shortest, codewords. A
nomenclator-maker who wants short codes for common words would do this.
The hypothesis was formed after seeing stage-31 results; that is why this
stage has its own protocol rather than being a repair to stage 31.

## Fixed design, identical to stage 31 Part C except assignment

* Shape model: the stage-31 broad-arm N2 Witten–Bell glyph chain, rebuilt from
  the same 20,029 tokens and checked equal to stage 31's `shape_model.json`.
* String sets: for key seeds 101–106, the same successive sampling as stage 31
  (`model_codebook`), so each key uses **exactly stage 31's 2,968 strings**.
  This makes the stage-31/32 comparison paired by key.
* Assignment: sort the 2,968 strings by model probability (descending; ties
  lexical). Sort the 1,484 plaintext types by their frequency in the full
  prepared cucina source (descending; ties lexical). That source is the one
  stage 30 already used transductively for the dictionary. Type j receives
  strings 2j and 2j+1. Which of the two is alternative 0 is a fair bit from
  `default_rng(seed + 5000)`. No other parameter.
* Plaintext passages, four rules (iid/page/word_page/refresh 1/4), encoding
  seeds, page resets, 96 cipher panels, R2 training (same broad lines), six R2
  settings and seeds (72 panels), targets and layouts are as stage 31.
* Measures: stage 31's eight (TTR, top-ten share, section excess, role
  excess, count≥5 section contribution, mean glyph length, within-word glyph
  conditional entropy, n/l/r coupling) with the same scales. Secondary,
  descriptive: hand-stratified section excess; type-level Spearman between
  frequency and glyph length.

## Predictions stated in advance

1. Token identity structure is unchanged by relabelling. So TTR, top-ten share
   and page association should have the same distribution as stage 31 for the
   same rule (up to the variant-bit labelling).
2. Mean length and glyph entropy should move toward Voynich, and the
   frequency/length correlation should turn negative.
3. Coupling stays near zero: codewords are still chosen without regard to
   neighbours. A joint fit is therefore **not expected**. The stage succeeds
   as a diagnostic if prediction 2 holds and fails if it does not.

## Selection, calibration and evaluation

As stage 31: development-median selection by maximum scaled residual against
B_ZL_split_early (ties by setting order); 16 synthetic targets (keys 701/702 ×
two development passages × four rules) with the ≥12/16 within-2 gate before
manuscript selection; leave-seed-out discrimination (≥0.80 for
"discriminating"); validation on B_ZL_split_late, B_IT_split_late,
B_ZL_join_late, A_ZL_split_late. Max residual ≤1 is a descriptive
neighbourhood. Report all signed residuals, and paired per-key differences from
stage 31 for mean length and glyph entropy.

Decision: if no draw fits, record which measures still fail and that coupling
was the predicted failure. Do not add a coupling repair here; stage 33 has its
own protocol. If a joint fit occurred despite prediction 3, report it as
unexpected and require replication before any interpretation.

## Checks and outputs

Unit tests: ranked assignment uses the same string set as the random codebook,
assigns more probable strings to more frequent words, and round-trips for every
rule. All 96 cipher panels must round-trip; a verify module replays every panel
and re-derives every reported number. Output `results/ranked_assignment_2026-10-09`;
update the ledger. No changes to historical results.
