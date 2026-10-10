# Voynich: scribe control, dependent word shapes, then codebooks

> **Correction, 10 October 2026.** Part C's coupling measure counted drawing-separated words as neighbours, and secondary targets reused ciphertext encoded for the reserved layout. Corrected, the verdict is unchanged (no joint hits). Part A's sentence that about 29% of association "lies between hands" is withdrawn. Conditioning on hand reduces the corrected statistic by 29%; directly corrected word/hand association is 0.0995 bits (plaintext references −0.026 to 0.054). Neither allocates information to scribes. Part B is unaffected. See [the boundary correction](../boundary_correction_2026-10-10/README.md). This directory and its producing code are kept unchanged so they still replay.

Stage 31, 9 October 2026. [Frozen protocol](../../docs/protocols/WORD_SHAPES_2026-10-09.md),
committed at 5fb1ba7 before any fit. Evidence labels: Part A and Part B are
descriptive structural diagnostics; Part C is **search found no fit in a bounded
forward-model grid**. No plaintext was recovered and no key was searched for.

**In one paragraph.** Scribe accounts for part of Currier B's page association,
but not most of it. Within hands, B keeps 71% of its section excess (0.096 of
0.135 bits). That is less than any of twelve plaintext references keeps under
the same stratification (77–103%). Currier A comes from one scribe and still has
0.078 bits. A simple glyph-chain word-shape model (order 2, Witten–Bell) fixes
the main stage-30 failure. It matches Voynich's within-word predictability and its
nearly-fixed word endings, and its 2,968 most probable strings cover 83% of
reserved B tokens (stage 30's grammar: 55% with 14,336 strings). Building a
codebook on it with random assignment still fails the joint screen. Codewords
come out too long, because random assignment gives common plaintext words
arbitrary codewords, while in Voynich the common words are short. Coupling
between neighbouring words stays at zero, as predicted. R2 also fails.

## Part A: how much of the page signal is scribe?

Hand is Lisa Fagin Davis's attribution in the ZL `$H` page variable (voynich.nu
transliteration notes, item 25; `$C` is Currier's hand). Hand is a function of
page, so I(W;P|section) = I(W;hand|section) + I(W;P|section,hand). Values are
permutation-corrected bits per token, stage-29 estimator, no vocabulary cap.

| Panel | Hands (pages) | Section excess | Within hand | Retained | Count≥5, within hand |
| --- | --- | --- | --- | --- | --- |
| B ZL split, 16 folios | 2:10, 5:4, 3:2 | 0.135 | 0.096 | 0.71 | 0.080 of 0.119 |
| B ZL join, 16 folios | same | 0.148 | 0.114 | 0.77 | 0.079 of 0.111 |
| B IT split, 16 folios | same | 0.132 | 0.105 | 0.79 | 0.079 of 0.107 |
| B ZL split, early 8 | 2:7, 5:1 | 0.115 | 0.089 | 0.77 | 0.058 of 0.076 |
| B ZL split, late 8 | 2:3, 5:3, 3:2 | 0.114 | 0.044 | 0.39 | 0.024 of 0.087 |
| Stage-28 original ZL | 2:15, 5:1 | 0.116 | 0.103 | 0.89 | 0.094 of 0.104 |
| Stage-28 additional ZL | 2:3, 5:3, 3:10 | 0.105 | 0.068 | 0.65 | 0.040 of 0.074 |
| A ZL split, 16 folios | 1:16 | 0.078 | 0.078 | 1.00 | identical |

Twelve recipe/Celsus/Pliny passages laid on the 16-folio B layout keep 0.77–1.03
of their (smaller) association under the same stratification. By the declared
rule, B's retained share (0.71) is below every reference, so **hand grouping
removes more of B's association than coincident topic variation removes from
these plaintexts**. Still, B's within-hand 0.096 bits exceeds nine of the twelve
references' *unstratified* values (all but two Celsus passages and one recipe
passage, the last by 0.0002). Calibration passed: IID ≈ 0; hand-only
vocabularies 0.406 → −0.001; page vocabularies keep 81% under stratification.
Single-hand panels give exactly identical values.

Limits: hands are palaeographic attributions, not ground truth. Hand overlaps
with quire and section in sixteen folios. The reserved eight-folio panel has
only two or three pages per hand, and its within-hand value (0.044) is far more
uncertain than the 16-folio value. This is why the protocol keeps the
unstratified target for selection.

## Part B: word shapes without a cipher

Two training arms: **broad**, all 20,029 clean ZL Currier B tokens on 32 folios
off the reserved pages (4,128 types), and **matched**, stage 30's 512
development tokens. Order chosen by leave-one-folio-out cross-entropy; both arms
chose N2 (two-glyph context). Sample measures are medians over 20 samples of
512 words; Voynich values are the reserved B_ZL_split_late tokens.

| Model (broad arm) | Reserved bits/glyph | Glyph entropy | Last-glyph dependence | Mean length | Top-2,968 token coverage | Unseen-type coverage |
| --- | --- | --- | --- | --- | --- | --- |
| S0 (stage-30 slots) | zero outside support | 2.653 | 0.143 | 4.19 | 0.535 | 0.067 |
| N1 | 2.285 | 1.932 | 1.486 | 4.52 | 0.773 | 0.101 |
| **N2 (selected)** | **2.104** | **1.919** | **1.444** | **4.66** | **0.826** | **0.169** |
| N3 | 2.109 | 1.917 | 1.457 | 4.66 | 0.846 | 0.191 |
| Most frequent 2,968 observed types | — | — | — | — | 0.801 | — |
| Voynich reserved B | — | 2.072 | 1.535 | 4.52 | — | — |

Last-glyph dependence is H(last) − H(last | previous). Voynich's final glyph
carries about 1.5 bits of dependence on its predecessor, and the slot grammar
reproduces 0.14. The N2 model passes all four frozen gate checks in both arms
(broad residuals: glyph entropy −0.15, dependence −0.09, length +0.14). Its 2,968
most probable strings cover more reserved tokens than the 2,968 most frequent
observed types do. In the matched arm (trained on 512 tokens), N2 covers 79% of
reserved tokens and 54% of types never seen in its training.

Transfer to Currier A is weaker: 2.67 bits/glyph versus 2.10 on reserved B, and
74% top-2,968 coverage. B-trained shapes are not A shapes.

## Part C: a codebook on the N2 model

Exactly stage 30's plaintext, dictionary, four variant rules, seeds and panel
counts (96 cipher, 72 R2). Stage 30's slot grammar is replaced by successive
sampling of 2,968 distinct strings from broad-arm N2, assigned randomly. R2 is
trained on the same 20,029 broad tokens. The vector adds the n/l/r → next-initial
coupling (scale 0.05) to stage 30's seven measures.

Calibration passed 16/16 (gate 12). Leave-seed-out discrimination is 100%
balanced accuracy between these simulated families, which is not a Voynich
classification. Development selection chose cipher IID (median max residual
3.60; the four rules lie within 3.60–3.73) and R2 level 2 without coupling (2.10).

| Target | Model | Joint hits | Best max residual | Section | Role | Mean length | Glyph entropy | Coupling | Within-hand section |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B_ZL_split_early | cipher | 0/12 | 2.62 | 0.053 | 0.022 | 6.14 | 2.246 | 0.000 | 0.019 |
| B_ZL_split_early | R2 | 0/6 | 1.91 | 0.170 | 0.097 | 4.41 | 2.499 | 0.015 | 0.151 |
| B_ZL_split_early | Voynich | | | 0.115 | 0.086 | 4.34 | 1.981 | 0.120 | 0.089 |
| B_ZL_split_late | cipher | 0/12 | 4.28 | 0.067 | 0.027 | 6.11 | 2.257 | 0.002 | 0.045 |
| B_ZL_split_late | R2 | 0/6 | 4.67 | 0.175 | 0.072 | 4.79 | 2.653 | −0.014 | 0.097 |
| B_ZL_split_late | Voynich | | | 0.114 | 0.089 | 4.52 | 2.072 | 0.248 | 0.044 |
| B_IT_split_late | cipher / R2 | 0/12, 0/6 | 4.14 / 4.72 | | | | | | |
| B_ZL_join_late | cipher / R2 | 0/12, 0/6 | 2.90 / 3.36 | | | | | | |
| A_ZL_split_late | cipher / R2 | 0/12, 0/6 | 3.70 / 2.04 | | | | | | |

Medians over the selected setting's validation draws. Both families fail every
target. Glyph entropy improves from stage 30's 2.78 to 2.26 but remains above
Voynich. Page association behaves as in stage 30, since the rules are unchanged.

**Coupling:** as the protocol predicted, random assignment chooses each codeword
without regard to its neighbours, so cipher coupling is zero (−0.007 to 0.006).
Voynich B gives 0.12–0.25 on the same rows. Coupling is weak in A (0.021).

**Word length (post hoc diagnosis, not a protocol measure):** the shape model's
own samples average 4.66 glyphs. Codewords as types average 6.07, because
collecting 2,968 *distinct* strings reaches far into the model's long tail.
Random assignment then gives frequent plaintext words such long codewords. In
the broad B pool, frequency and length are negatively rank-correlated across
types (Spearman −0.31; token mean 4.62 versus type mean 5.64). The cipher
output's correlation is +0.14. Voynich's common words are short; this codebook's
are not.

Budgets: N2 count table 132,584 serialized bits; codebook serialization 368,976
bits and uniform ordered-assignment reference 29,962 bits per key; 11,169 model
draws to collect 2,968 distinct strings. Implementation-dependent accounting,
not an MDL ranking.

## What this changes

1. **The page target is partly scribal.** About 29% of B's 16-folio association
   lies between hands, more than topic coincidence explains in these
   references. A cipher model should be scored against both the unstratified
   and within-hand values, especially on panels mixing hands 2, 3 and 5. A,
   from one hand, still shows association.
2. **Word shapes are solved enough for now.** A two-glyph-context chain
   reproduces predictability, word endings and capacity. Further slot-grammar
   variants are unnecessary for these measures. Stolfi/Zattera grammars remain
   deferred: their source pages were unreachable (HTTP 404).
3. **Assignment, not shape, is now the binding constraint.** Two specific
   mechanisms remain untested: (a) frequency-ranked assignment, in which common
   plaintext words get the most probable codewords; (b) context-conditioned variant choice,
   in which the alternative suited to the next word is chosen. (b) is the only route in this
   family to the coupling. Each needs its own protocol; neither is a Part C repair.

No decipherment, readings, family rejection or comparative support is claimed.
Twelve validation draws are two passages × six keys, not twelve sources.
One culinary source; 512 tokens per target.

## Verification and files

`python -m voynich.laboratory.word_shapes_verify` checks source hashes. It
recomputes all 29 Part A panels and the full Part B arms, CV, coverage and gate.
It rebuilds the N2 model and all six codebooks and replays all 168 panels
(49,152 cipher tokens round-trip). It also re-derives calibration, discrimination,
selection and every residual. A full rerun reproduced `shapes.json` and
`evidence.json` byte for byte. 227 tests pass; the four PostgreSQL integration
tests skipped locally (no `POSTGRES_TEST_URL`) and run in CI.

`scribe.json` Part A · `shapes.json` Part B · `shape_model.json` N2 counts ·
`codebooks.json`, `generated.json`, `calibration.json`, `evidence.json`,
`costs.json` Part C · `hands.json`, `training.json`, `slots.json`,
`source_panels.json`, `manifest.json`, `verification.json`.

Deviations: none in design or thresholds. After the first run, the arm
construction was moved into a function so the verifier could reuse it. The
stage was then rerun from scratch, and `shapes.json`/`evidence.json` were
byte-identical; the committed outputs and hashes come from that rerun.

Post hoc: the frequency/length diagnosis above, and the observation that the
reserved panel's within-hand value happens to equal the cipher's (0.044 vs
0.045). The latter is coincidental given its development mismatch (0.089 vs
0.019) and is not evidence.
