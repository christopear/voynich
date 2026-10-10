# Correction: over-strong conclusions and two implementation issues in stages 35–38

Committed before the corrective run. A **post hoc correction** following an
external review of PRs #19–#22. The reviewer replayed stages 35–37 exactly;
the numbers stand. What changes is what they are taken to show, plus one
token-set discrepancy and one confound in stage 37. Historical result
directories and their producing code are unchanged and still replay; each gets
a dated correction note.

## Defects (confirmed before this protocol)

1. **Stage 38 confused conditional with overall independence.** The product
   model assumes prefix and suffix are independent outright. Naibbe draws them
   independently **given the plaintext letters**. Correlated letters can
   correlate the parts. The report's claim that Naibbe's construction is
   disfavoured "independent of any key or plaintext" does not follow. The
   calibration covered one ciphertext (Greshko's, from one Latin text, six
   tables). The fitted "116 × 26" inventory is a summary of this model's fit,
   not a recovered table.
2. **Stage 35 generalised power from one planting procedure.** Detecting a
   planted remapping of endings at q = 0.2 does not show that any line indicator
   changing 20% of endings would be detected. An indicator that changes endings
   while preserving their distribution within the line is invisible to a
   statistic on the final glyph's distribution.
3. **Stage 36 turned non-detection into absence.** M2 (whole-label recurrence)
   had no power calibration. M3's calibration cannot stand in for it. "Labels
   are not tied to their page's text" is not supported.
4. **Stage 37 deviated from its stated token set.** The protocol said type
   counts come from tokens of at least two glyphs. The code counted all clean
   tokens, including 577 one-glyph tokens. Under the stated rule the Currier B
   n/l/r common-stem share is 7.7%, not 19.4%, and the difference from other
   endings is −17.7 points, not −9.6. The report said "deviations: none".
5. **Stage 37 M2 pooled across pages.** It permuted next-initials within stem
   over all pages. Pages that differ in both form frequency and following
   initials can produce an association with no within-page dependence. M2 as
   run is a pooled association; it does not show that the next word determines
   the form.

## Corrective analyses

**A. Stage 38, wider known-answer calibration.** Simulated Naibbe-family
ciphertext from Greshko's tables (simulation, not the published card
procedure): each plaintext letter stream is cut into one- and two-letter units
with equal probability; tables are drawn with weights 28/14/11/11/7/7.
Configurations: tables {all six, alpha only}; table draw {separate for prefix
and suffix, one draw per word}; plaintext {Latin Alfonsi, Italian Dante, Latin
with its letters shuffled}. Up to 35,000 tokens, five block folds, same T_new.
Report every configuration. The stage-38 statement is then restricted to the
configurations in which the product model is shown to win, and says so.

**B. Stage 35, distribution-preserving indicator.** On shuffled-key lines,
for lines whose first glyph is in the upper key half, permute the final glyphs
among that line's non-initial words (20 replicates, seeds 4100+). Record the
share of endings changed and how often the stage-35 rule fires. This documents
a class of indicator the statistic cannot see.

**C. Stage 36, power for M2.** From label sets permuted within kind, for a
share r ∈ {0.02, 0.05, 0.10} of labels add the label's word to its page's
running-text vocabulary; 20 replicates each (seeds 4200+). Report detection at
p < 0.0125. Any sensitivity statement is limited to this planting.

**D. Stage 37, both token sets and a page-conditioned M2.**
* M1 under the protocol's token set (counts from tokens of two or more glyphs)
  beside M1 as implemented, for Currier B and IT2a.
* M2 conditioned on stem × page: permute next-initials within stem and page;
  only stem/page cells containing both forms contribute.
* Recalibrate with the three stage-37 plantings, plus a **page-confound
  planting**: pages ranked by their share of next-initials in the fixed half;
  on the upper half of pages `z` is appended with probability 0.6, on the lower
  half 0.05, independent of the next word (10 replicates each, seeds 4300+).
  Report how often the pooled and the page-conditioned rules fire. Gate for the
  page-conditioned rule: at least 8/10 on true markers and at most 1/10 on each
  of the other three.
* Manuscript values for the page-conditioned M2, with records and cells used.

## Wording to correct

* Stage 38: "the fitted product model predicts unseen Voynich word types worse
  than the glyph chain, while it does better on Naibbe ciphertext in the tested
  configurations". No plaintext-independent exclusion. The decoding attempt
  remains unjustified for lack of positive evidence, not because the family is
  excluded.
* Stage 35: "no indicator signal detected by this statistic". Sensitivity only
  for the planted remapping. Remove "would have been seen" and "bounded out".
* Stage 36: "no excess whole-label recurrence detected under the within-kind
  permutation comparison". No claim about whether the text refers to labelled
  objects.
* Stage 37: report both token sets; "deviations: none" withdrawn; M2 described
  as pooled association unless the page-conditioned version supports more.

## Programme-level notes to record

Novelty is unverified: before calling anything a contribution, state its
specific difference from prior work. Pages reused across stages are development
evidence; new folds do not restore independence. Aggregate fit, word-shape
likelihood and coupling scores do not establish a cipher, a language or a
reading; do not restart the closed whole-word programme under another name.

Output: `results/claims_correction_2026-10-10`, with a verify module.
