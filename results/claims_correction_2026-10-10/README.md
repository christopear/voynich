# Correction: over-strong conclusions in stages 35–38

10 October 2026. **Post hoc correction** after an external review of PRs
#19–#22. [Protocol](../../docs/protocols/CLAIMS_CORRECTION_2026-10-10.md)
committed at 67357fb before the run. The reviewer replayed stages 35–37
exactly; the numbers stand. What changes is what they show, plus one token-set
deviation and one confound in stage 37. The stage 35–38 directories and their
code are unchanged and still replay; each README carries a dated note.

**In one paragraph.** Four reports claimed more than their analyses supported.
The largest error was in stage 38. Its "chain-like" result is exactly what a
Naibbe-family cipher produces when **one table draw fixes both halves of a
word**. The claim that Naibbe's construction is disfavoured whatever the key or
plaintext is withdrawn. Stage 35's sensitivity holds only for the perturbation
it planted. Stage 36 did not show labels are unconnected to their page. Stage
37 deviated from its own token rule and used a pooled test that page
differences can fool. The corrected statements are below.

## Stage 38: the product model and Naibbe-family configurations

Simulated ciphertext from Greshko's tables (a simulation, not his card
procedure), five block folds each. T_new is bits per unseen word type, product
model against glyph chain.

| Plaintext | Tables | Table draw | T_new mean (folds) |
| --- | --- | --- | --- |
| Latin | six | separate for prefix and suffix | **+1.28** (+1.20 to +1.33) |
| Latin | six | **one per word** | **−0.92** (−1.47 to −0.30) |
| Latin | alpha only | — | +3.32 (+1.72 to +4.18) |
| Italian | six | separate | +1.19 (+1.13 to +1.32) |
| Italian | six | one per word | −1.45 (−1.83 to −0.81) |
| Italian | alpha only | — | +2.41 (+1.12 to +4.35) |
| Latin, letters shuffled | six | separate | +1.42 (+1.39 to +1.45) |
| Latin, letters shuffled | six | one per word | −0.30 (−0.47 to +0.12) |
| Latin, letters shuffled | alpha only | — | +4.09 (+1.49 to +9.40) |
| *Voynich Currier B (stage 38)* | | | *−0.92 (−1.02 to −0.83)* |

* The reviewer's point holds, and more strongly than plaintext correlation
  alone. Plaintext letter correlation changes little here: shuffling the
  letters moves the separate-draw case from +1.28 to +1.42.
* What flips the sign is **correlation through the table choice**. If one draw
  picks the table for both halves, prefix and suffix are dependent and the
  product model loses to the chain, as it does on Voynich.
* **Corrected statement:** the fitted product model predicts unseen Voynich
  word types worse than the glyph chain. It does better on Naibbe-family text
  in the nine tested configurations only when prefix and suffix are drawn
  separately. Voynich's value is within the range of the one-draw-per-word
  configurations. No Naibbe-family exclusion follows.
* The "116 × 26" inventory is a summary of this model's fit to Voynich. It is
  not a recovered table, and under a one-draw system the model is misspecified.
* A decoding attempt is still not justified, but for lack of positive evidence
  about the system. It is no longer because the family is excluded.

## Stage 35: what the line-indicator test can and cannot see

A planted indicator that **permutes the final glyphs among the words of its own
line** changes 24.4% of endings and fired the rule in **0 of 20** runs. The
statistic looks at the distribution of final glyphs given the line's first
glyph; an indicator that rearranges endings without changing that distribution
is invisible to it.

**Corrected statement:** no indicator signal was detected by this statistic on
Currier B. It detects the specific planted remapping at 20% (16/20) and 40%
(20/20). Statements that a line-initial indicator "would have been seen" or is
"bounded out" are withdrawn. So is the inference that line-level table
switching is unsupported in general.

## Stage 36: power of the whole-label recurrence test

| Share of labels whose word is planted in their page's text | 2% | 5% | 10% |
| --- | --- | --- | --- |
| M2 detected at p < 0.0125, of 20 | 9 | 20 | 20 |

**Corrected statement:** no excess whole-label recurrence was detected under
the within-kind permutation comparison (10.9% observed, 11.0% expected). Under
this planting the test detects an excess from 5% of labels and often misses 2%.
That does not show the text never refers to labelled objects by those forms,
and section-level sharing is not measured. "Labels are not tied to their page's
text" is withdrawn. The M3 calibration applies to M3 only.

## Stage 37: both token sets, and a page-conditioned M2

**Token set.** The protocol said type counts come from tokens of two or more
glyphs. The code counted all clean tokens (577 one-glyph tokens included). This
was an undisclosed deviation; "deviations: none" is withdrawn.

| Currier B | n/l/r stem common | Other endings | Difference (95% interval) |
| --- | --- | --- | --- |
| As implemented (all clean tokens as reference) | 19.4% | 29.0% | −9.6 points (−11.4 to −7.7) |
| **As the protocol specified** | **7.7%** | **25.4%** | **−17.7 points (−19.3 to −16.1)** |

The direction is the same and the gap is larger. The two versions answer
slightly different questions. Under the protocol's rule, the stem of a
two-glyph word (*ol*, *ar*, *al*, *or*) is a single glyph and can never count
as attested, so those very common words always count against. IT2a: −10.6 and
−16.2 points.

**Page confound.** M2 as run permuted within stem across all pages.

| Planted on shuffled Currier B text (10 runs each) | Pooled rule fired | Page-conditioned rule fired |
| --- | --- | --- |
| True marker | 10 | 10 |
| Random suffix | 0 | 0 |
| Lexical ending | 0 | 0 |
| **Page confound, no within-page dependence** | **3** | 1 |

The pooled rule is fooled by page differences in 3 of 10 runs. The
page-conditioned rule passes its gate (at least 8/10 on true markers, at most
1/10 on each other planting).

| Data | Pooled M2 excess, p | Page-conditioned M2: cells, records, excess, p |
| --- | --- | --- |
| Currier B, ZL | 0.064, 0.001 | 157, 953, 0.080, **0.001** |
| Currier B, IT2a | 0.046, 0.001 | 127, 579, 0.031, **0.033** |
| Currier A, non-sealed | 0.109, 0.001 | 100, 438, 0.075, 0.001 |

**Corrected statement:** in Currier B, removing a final n, l or r leaves a
common word less often than removing other endings, under either token set.
For stems seen both bare and marked, form is associated with the next word's
first glyph when pooled. Within pages the association holds in ZL (p = 0.001)
but does not reach the threshold in IT2a (p = 0.033). So the within-page
dependence is not established across transcriptions, and "the next word
determines the form" is not shown. The rule still does not fire for B, because
M1 fails under either token set. Currier A passes all versions; it remains an
uncalibrated, unreplicated sensitivity.

## Programme-level points accepted

* **Novelty is unverified.** Word structure, low glyph entropy, vocabulary
  organisation and uncertain-boundary effects all have substantial precedents.
  Nothing in stages 31–38 should be called a contribution until its specific
  difference from prior work is stated and checked.
* **Reused pages are development evidence.** Currier B paragraph text has now
  been used by every stage. New folds do not restore independence.
* **Aggregate fit does not establish meaning.** Word-shape likelihoods and
  coupling scores, including stage 38's, are not evidence of a cipher, a
  language or a reading.

## Verification

`python -m voynich.laboratory.claims_correction_verify` checks source hashes
and reruns every analysis here, requiring an identical `evidence.json` (about
twenty minutes). Unit tests cover the simulation, the distribution-preserving
planting, and a synthetic page confound that fools the pooled test but not the
page-conditioned one.
