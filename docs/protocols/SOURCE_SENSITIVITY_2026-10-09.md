# Stage 34: plaintext source sensitivity under the frozen stage-33 mechanism

Preregistered before execution. Ledger rows 13 and 22; prospective row 23.
This is a **forward-model screen**, not blind decryption. Known-key round trips
are engineering checks, never evidence of a reading.

## Question

Stages 30–33 used one Italian culinary source. Under stage 33's closest rule
(deterministic context choice, no persistence), page association comes almost
entirely from the plaintext laid on the pages, and recipes supply about half of
Voynich's. The programme's working content hypothesis is medicinal/herbal.
Stage 29 found Celsus passages with page association up to 0.148 bits on these
layouts and Pliny passages much lower. This stage asks whether the plaintext
source, with the mechanism frozen, changes the joint picture. No mechanism
parameter changes.

## Frozen mechanism (exactly stages 31–33)

* Shape model: stage-31 broad N2, rebuilt and checked equal.
* Codebook per source and key: successive sampling of 2V distinct strings from
  the shape model (`model_codebook`, key seeds 101–106, calibration 701/702),
  then stage-32 frequency-ranked assignment. V is the number of normalised types
  in that source's prepared text, with the source's full-text frequencies,
  transductive as in stage 30.
* Choice rules: stage 33's four (iid, edge, edge_max, edge_refresh), the same
  R2 edge lift table, encoding last-to-first by page.
* Measures, scales, targets, layouts, encoding seeds (10000 + 100·passage +
  key), selection, calibration gate (≥12/16 within 2) and discrimination as
  stage 33. R2 panels are identical to stage 33's (R2 ignores plaintext).

## Sources

The stage-28 frozen passages for **celsus** (Latin medical), **pliny** (Latin
natural history/medicine) and **cucina** (Italian recipes, reference;
reproduces stage 33 exactly): seeds 7/19 development, 31/43 validation, first
512 words. Chapter halves stay disjoint. Prepared texts and provenance are
stage 27's (`data/unit_association_sources/`).

Per source: 4 rules × 6 keys × 2 passages × 2 splits = 96 cipher panels; 288 in
total plus 72 shared R2 panels. Selection is separate per source, on
development pages only.

## Secondary measure (declared)

The plaintext words themselves laid on the same rows: section and role excess
(stage-29 estimator). For a disjoint code with page-independent IID choice,
the population data-processing bound gives I(C;P) ≤ I(U;P) + I(C;P|U), with the
second term zero. This shows how much page association each source brings
before encoding. It is descriptive and not used in selection.

Also descriptive: for every source, rule and target, hits within max residual
1 over the validation draws, regardless of selection. This addresses the
replication request from stage 32's marginal Currier A result. Unselected
rules are not eligible for a positive claim.

## Predictions stated in advance

1. Celsus passages raise cipher page association relative to cucina under
   iid/edge/edge_max, and Pliny lowers it, tracking the plaintext's own
   association on the same rows.
2. Latin inflection raises the type/token ratio relative to cucina.
3. Coupling under edge_max is similar across sources, since it is a property of
   the codebook endings and the lift table, not of the plaintext.

## Decision rules

* If a source's selected cipher rule has joint hits on reserved
  B_ZL_split_late and R2 has none: label "compatible on these measures" for
  that source and construction only. State that coupling is partly built in and
  sources were compared after stage 33 was seen. Any stronger label needs new
  folios and sources under a later protocol. No decipherment claim.
* If both hit: non-identifiable on these measures.
* If neither hits for any source: report the remaining mismatch by source and
  stop this mechanism line. The next step is then a different representation
  or semantic constraints (labels), not more parameters here.
* Choosing the best of three sources after seeing results is itself a
  selection. Report all three, and do not treat the best one as confirmed.

## Checks and outputs

Unit test: source-generic codebook construction reproduces stage 33's cucina
codebooks. Verify module replays every panel, re-derives every reported number,
and confirms cucina panels equal stage 33's. Output
`results/source_sensitivity_2026-10-09`; update the ledger. No changes to
historical results.
