# Stage 33: context-conditioned variant choice

Preregistered before execution. Ledger row 21; prospective row 22. This is a
**forward-model screen**, not blind decryption. Known-key round trips are
engineering checks, never evidence of a reading.

## Question

Stages 31–32 leave one binding failure for Currier B: a word's n/l/r ending does
not predict the next word's first glyph, because each codeword is chosen
without regard to its neighbours. The constitution lists context-conditioned
alternatives as a candidate operation. Here the encoder chooses, between a
word's two disjoint codewords, the one whose final glyph suits the next
codeword's first glyph. Decoding still needs only the reverse dictionary.

**This builds the coupling in by design.** The suitability table comes from
Voynich training folios. So reproducing coupling on its own is expected and
proves nothing. The question is whether the coupling reaches the right size
while length, entropy, frequency/length and page association all hold together
on reserved pages, and whether R2, which has its own coupling option, does
equally well. A joint fit by both would mean the measures cannot tell the two
apart (non-identifiable).

## Fixed design

* Codebooks: exactly stage 32's frequency-ranked codebooks (keys 101–106,
  calibration keys 701/702), rebuilt and checked equal. Shape model, plaintext
  passages, encoding seeds, targets, layouts, eight measures and scales are
  stage 32's.
* Suitability table: `mechanism_models.Training(broad lines).edge`, the existing
  R2 edge lift. P(initial | final)/P(initial) over ordinary gaps in the 20,029
  broad-arm tokens, smoothed and clipped to [0.2, 5] by its existing code. No
  new fitted parameter. Missing pairs have lift 1. Charged as serialized bits.
* Context: token i's successor is i+1 when it is on the same line with no hard
  gap (same rule as the coupling measure). Otherwise there is no context.
* Order: each page is encoded from its last token to its first, so the
  successor's codeword is fixed first. State resets at page boundaries.

Four rules (setting order):

1. **iid**: stage 32's rule, byte-identical tokens (pairing baseline).
2. **edge**: choose alternative a with probability proportional to
   lift(final(a), initial(next codeword)); a fair bit without context.
3. **edge_max**: choose the alternative with the larger lift; a fair bit on a
   tie or without context.
4. **edge_refresh**: stage 30's refresh logic (reuse a word's stored variant on
   a page, refresh with probability 1/4), applied in encoding order. Every
   fresh choice is made as in **edge**.

The audit records choices, the fraction of choices with context and unequal
lifts, and the trajectory cost −log2 P(choice) under the declared law.

R2: unchanged from stage 32 (same broad training, six settings, seeds), so
R2 panels must be token-identical to stage 32's.

## Predictions stated in advance

1. Coupling rises above stage 32 for the three edge rules, most for edge_max.
2. Page association is unchanged for edge and edge_max relative to iid in
   distribution, since codeword identity per plaintext word is preserved up
   to the variant. Length and glyph entropy move only slightly.
3. Whether coupling reaches 0.12–0.25 bits is not predicted. Each word has only
   two alternatives, and only some pairs differ usefully in final glyph.

## Selection, calibration and evaluation

As stage 32: development-median selection by maximum scaled residual against
B_ZL_split_early; the 16-target synthetic calibration gate (≥12/16 within 2);
leave-seed-out discrimination (≥0.80); validation on B_ZL_split_late,
B_IT_split_late, B_ZL_join_late, A_ZL_split_late; descriptive neighbourhood
max residual ≤1; all signed residuals; within-hand section excess and
frequency/length as secondary measures. Report paired per-key differences from
stage 32 IID for coupling, length, glyph entropy and section excess.

Decision rules:

* If the selected cipher rule has validation hits on reserved B and R2 does
  not, report "compatible on these measures" for this construction, with the
  built-in-coupling caveat. Require stage 34 replication on new folios and
  sources before any stronger label. No decipherment claim.
* If both families hit, report non-identifiability on these measures.
* If neither hits, record the remaining mismatch. Do not add more alternatives,
  stronger lifts or tuned exponents in this stage.

## Checks and outputs

Unit tests: right-to-left context uses the encoded successor and respects line
and hard-gap boundaries; edge_max picks the higher-lift alternative; iid
reproduces stage 32 tokens; all rules round-trip; trajectory cost equals the sum
of −log2 choice probabilities. A verify module replays every panel and re-derives
every reported number. Output `results/context_choice_2026-10-09`; update the
ledger. No changes to historical results.
