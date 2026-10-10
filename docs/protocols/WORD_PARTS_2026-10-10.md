# Stage 38: are Voynich words prefix-plus-suffix codes?

Preregistered before execution on manuscript text. Ledger rows 12 and 15
(grouped and syllabic units) and row 8 (verbose codes with fixed Naibbe tables).
A **structural test of one shape prediction**. It is not a generator fit, it
searches for no key, and it cannot show that the text has meaning.

## Question

A Naibbe-shaped cipher writes most words as a prefix for one letter joined to a
suffix for the next, the two parts drawn independently given the letters. If
Voynich words are built that way, a model that predicts a word only as "one
prefix times one suffix" should predict **words it has never seen** better
than a model that chains glyphs. If Voynich words are instead chain-like, or
are stems with a few endings as in ordinary language, it should do worse.

## Models (`voynich.laboratory.word_parts`)

* **Product model:** every word of two or more compound-EVA glyphs is one
  prefix and one suffix, both non-empty, drawn independently. The split point
  is latent. Fitted by 30 EM iterations from uniform responsibilities. No
  whole-word memory and no smoothing.
* **Chain:** the stage-31 order-2 Witten–Bell glyph chain.
* **T_new (primary):** over held-out tokens whose type does not occur in
  training, the mean of log2[(0.9·P_product + 0.1·P_chain) / P_chain]. It is
  bounded below by −3.32 and is positive when independent parts predict new
  words better than the chain. **T** is the same over all held-out tokens.
  **Coverage** is the share of new-type tokens to which the product model
  gives non-zero probability.

## Method development already done (declared; no manuscript text used)

On Greshko's shipped Naibbe ciphertext (34,764 tokens), three folds: T_new
+1.26, +1.52, +1.32; coverage 1.00; effective inventory about 57 prefixes and
50 suffixes. On chain text sampled from a glyph chain trained on that
ciphertext: T_new −1.24, −1.19, −1.27. The fitted product model puts 92% of
prefix mass and 97% of suffix mass on true table entries (90 and 95 of the top
100). Natural language: Latin (Alfonsi) T_new −2.04 with about 1,197 effective
prefixes and 10 suffixes; Italian (Dante) −1.24 with 341 and 9. The statistic,
the 0.9/0.1 mixture and the 30 iterations were fixed on these. **No Voynich
value of any quantity here was computed before this protocol was committed.**

## Data

ZL3b Currier B paragraph lines, clean tokens, off the sealed confirmation
pages. Five folds by alternating folios in manuscript order; each fold is held
out once. Sensitivities without separate claims: IT2a Currier B on the same
folds; non-sealed ZL Currier A (five folio folds).

## Calibration gate (computed in the run, before the manuscript is read)

* Naibbe ciphertext, five contiguous-block folds: T_new > 0 in at least 4/5.
* Chain text trained on Naibbe ciphertext, five folds: T_new < 0 in at least 4/5.
* Chain text trained on the Voynich B training folds (same token counts),
  five folds: T_new < 0 in at least 4/5. This is text with Voynich's local
  glyph statistics and no part structure.

If the gate fails, report the method as uncalibrated and make no statement.
Also reported, not gated: R2 (level 2, coupling on, seed 101) laid on the same
folds; Latin and Italian as above.

## Decision rule

* **Product-like:** T_new > 0 in at least 4/5 Voynich folds, mean coverage of
  new types at least 0.95, and mean T_new above every chain-control fold.
* **Chain-like:** T_new < 0 in at least 4/5 folds.
* **Mixed:** anything else.

Descriptive, for whichever outcome: effective numbers of prefixes and
suffixes, their top 25 members, and T, set beside Naibbe (about 57 × 50) and
natural language (hundreds × about 10).

## What each outcome would mean

* Product-like: words behave as two independently chosen parts, the shape a
  Naibbe-style table system produces. It would justify specifying a decoding
  attempt for that family under a new protocol. It would not show a cipher: a
  generator could be built the same way.
* Chain-like: the two halves of a word are not independent given the split.
  Naibbe's published procedure (separate card draws for prefix and suffix) is
  then disfavoured as a description of word structure. A variant in which one
  draw fixes both halves is not tested.
* The test takes the transcribed spaces as word boundaries. If spaces are not
  unit boundaries, both models are scored on the wrong units; this limit
  applies to every outcome.

## Outputs

`results/word_parts_2026-10-10` with evidence, calibration and a README with an
evidence label; a verify module that reruns and compares; ledger update. No
historical results changed.
