# Voynich: are words prefix-plus-suffix codes?

> **Correction, 10 October 2026 (claims).** The conclusion that Naibbe's construction is disfavoured "independent of any key or plaintext" is withdrawn. The product model assumes outright independence; Naibbe's is conditional on the letters and on how tables are drawn. A Naibbe-family simulation in which one draw fixes both halves of a word gives T_new of −0.30 to −1.45, the same range as Voynich's −0.92. Supported: the product model predicts unseen Voynich types worse than the chain, and better on Naibbe-family text only when the halves are drawn separately. The 116 × 26 inventory is a model summary, not a recovered table. See [the claims correction](../claims_correction_2026-10-10/README.md). This directory and its producing code are unchanged so they still replay.

Stage 38, 10 October 2026. [Frozen protocol](../../docs/protocols/WORD_PARTS_2026-10-10.md),
committed at c77156c before any manuscript text was read. Evidence label:
**chain-like by a calibrated structural test; Naibbe's independent
prefix-and-suffix construction is disfavoured as a description of Currier B
word structure**. No key search and no readings.

**In one paragraph.** A Naibbe-shaped cipher builds most words from a prefix
for one letter and a suffix for the next, chosen independently. Words it has
never seen should then be predictable as new combinations of known parts. On
real Naibbe ciphertext that works: predicting through independent parts beats a
glyph chain by +1.3 to +1.7 bits per new word, and the fitted model recovers
Naibbe's actual tables. On Currier B it fails in every fold: −0.83 to −1.02
bits. Voynich words do divide into familiar parts (95% of new words are made of
parts seen before), but the two halves are not independent. Which ending a
word takes depends on what comes before it, more than two separately drawn
table entries would allow.

## Calibration (passed)

| Text | T_new by fold (bits per new-type token) | Gate |
| --- | --- | --- |
| Naibbe ciphertext (known prefix × suffix) | +1.26, +1.51, +1.32, +1.55, +1.68 | positive in ≥ 4/5: yes |
| Glyph chain trained on Naibbe ciphertext | −1.19, −1.13, −1.24, −1.00, −1.12 | negative in ≥ 4/5: yes |
| Glyph chain trained on Voynich B | −1.51, −1.81, −1.59, −1.69, −1.65 | negative in ≥ 4/5: yes |

T_new compares a product model (one prefix times one suffix, split point
latent, no whole-word memory) with the stage-31 glyph chain, on held-out
tokens whose type was not in training. It cannot go below −3.32. In method
development on Naibbe text alone, the product model put 92% of prefix mass and
97% of suffix mass on true table entries.

## Manuscript

| Text | T_new by fold | Mean | New words made of known parts | Effective prefixes × suffixes |
| --- | --- | --- | --- | --- |
| **Currier B, ZL** | −1.02, −0.88, −0.83, −0.98, −0.86 | **−0.92** | 95.1% | 116 × 26 |
| Currier B, IT2a | −1.15, −1.00, −0.96, −1.01, −0.82 | −0.99 | 94.8% | — |
| Currier A, non-sealed (small) | −1.11, −0.96, −1.34, −1.33, −1.27 | −1.20 | 91.3% | — |
| R2 copy generator | −1.93 to −1.72 | −1.85 | 83.1% | — |
| Latin (Alfonsi) | −2.51 to −2.04 | −2.31 | 54.4% | about 1,200 × 10 |
| Italian (Dante) | −1.91 to −0.66 | −1.29 | 63.0% | about 340 × 9 |
| Naibbe ciphertext | +1.26 to +1.68 | +1.46 | 100% | 57 × 50 |

Verdict by the frozen rule: **chain-like** (negative in 5/5 folds). Each fold
holds out about 4,350 tokens, 590–720 of them new types.

Three descriptive points:

* **Voynich sits between the chain controls and Naibbe, nearer the chain.**
  Its −0.92 is above the −1.65 of chain text with its own local statistics. So
  there is some part-like regularity a pure glyph chain misses, but far too
  little independence for a two-part product.
* **The inventory is lopsided.** About 116 effective prefixes against 26
  suffixes, where Naibbe has 57 and 50. Voynich has many beginnings and few
  endings. That is closer to "a varied body plus one of a short list of
  endings" than to two balanced tables.
* **The parts themselves look like Naibbe's**, unsurprisingly, since Naibbe's
  tables were written from Voynich words: top prefixes *qok, d, a, ok, ot, ch,
  o, che, qot, sh*; top suffixes *y, aiin, edy, ar, ain, al, ol, l, eey, r*.

## What this means

* **Naibbe as published is not how Voynich words are structured.** Its
  procedure draws the prefix and the suffix with separate cards, which makes
  the halves independent given the letters. Voynich's halves are dependent.
  This is a structural failure that does not depend on any key or plaintext.
* **What is not excluded:** a system where a single choice fixes both halves
  (one table per word, not per half); a system with three or more parts per
  word; or parts whose form adjusts to their neighbour inside the word. The
  dependence found here is the same kind of local adjustment as the coupling
  between words (stage 37, and the earlier boundary work): endings accommodate
  what precedes them.
* **It weakens the case for the decoding attempt as planned.** That attempt
  assumed each word reduces to an independent (prefix, suffix) pair, one symbol
  per letter. That reduction does not hold. A solver would need a different
  model of what a word encodes.
* **The spacing caveat stands.** If transcribed spaces are not unit boundaries,
  both models were scored on the wrong units.
* R2 and natural language are also chain-like or worse, so this result does
  not separate a cipher from message-free text or from language.

## Verification

`python -m voynich.laboratory.word_parts_verify` checks source hashes and
reruns the whole stage, requiring identical outputs. Unit tests cover
compound-glyph splits, normalisation, and a synthetic product text whose
held-out combinations are predicted through parts. Sealed confirmation pages
were excluded. Deviations: none.
