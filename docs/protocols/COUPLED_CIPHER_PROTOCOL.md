# §19 transfer to a non-Naibbe cipher with and without edge coupling: protocol

Written 25 September 2026, before generating or scoring any cipher text for this
stage. Motivation is in `LITERATURE_NOTES_2026-09-25.md`. Parisel's boundary-MI
signature, voynich-collective's held-out edge criterion and our terminal
"sandhi" test agree that cross-word edge coupling separates Voynich from Naibbe.

Already known before writing:

* the §19 results (`EQUIVALENCE_FINDINGS_2026-09-25.md`);
* the Naibbe result on Parisel's verifier;
* the Latin syllable inventory: 40,148 syllable tokens, 874 types.

## Questions

1. Does the frozen Naibbe-trained §19 classifier recover hidden equivalence
   classes in a verbose homophonic cipher from a *different* design family?
2. Does it still do so when the choice of homophone depends on the next word
   (edge coupling), as a Voynich-like cipher would require? Or do coupled
   homophones look like distinct units, as `chol/chor` did?
3. Is the class information present in such ciphertext at all? This is checked by
   retraining within the family.

## Cipher family: syllabic slot cipher (`code/slot_cipher.py`)

**Plaintext.** `data/latin_alfonsi.txt`, lower-cased and NFKD-normalized, with
j→i, k→c, w→uu. Words are split into syllables by a fixed onset-maximizing rule
(the last consonant before a vowel starts the next syllable). One plaintext
syllable becomes one cipher token. The syllabifier is only a deterministic unit
segmentation; it makes no claim to Latin phonology.

**Code book** (built per seed):

* Every syllable type gets a unique *core*. Cores are drawn from a Voynich glyph
  Markov model (`mechanism_models.Training.fresh`, trained on all clean ZL P0
  tokens), with a Voynich-like length.
  * Cores may not start with q/o/y.
  * Cores may not end with n/l/r/m/y.
  * Cores are unique.
* Each syllable gets `h` homophone variants `prefix + core + terminal`:
  * prefix ∈ {"", o, qo, y};
  * terminal ∈ {"", y, n, l, r, m};
  * variants are distinct (prefix, terminal) combinations drawn at random.
* Every variant string must be unique across the whole code book, so decoding
  is an exact dictionary lookup. Round trips are verified.

**Homophone choice.** Each token takes a prefix-plus-terminal variant with base
weights ∝ rank^(−s). Coupling then acts on the terminal only:

1. Prefixes and cores are fixed first, which determines every token's initial
   glyph.
2. Each token's terminal is then chosen among its variants that share the
   chosen prefix. The weight is base weight × affinity(variant's last glyph,
   next token's first glyph)^β. Affinity is `Training.edge`, the observed
   Voynich end→initial ratio at ordinary spaces, bounded to [0.2, 5].

β = 0 means context-free homophony. Plaintext labels never depend on β.

**Layout.** The generated stream fills the ZL3b P0 layout template (33,970 slots)
in order, keeping the template's illegible/unclean flags, exactly as in the
mechanism benchmark.

## Calibration and selection (frozen)

Fingerprint and distance: `mechanism_models.fingerprint` and
`calibration_distance`, the same six calibration statistics and scales as the
mechanism benchmark:

* token length mean and SD;
* type/token ratio;
* hapax share;
* within-token glyph entropy;
* n/l/r edge MI.

The target is the full ZL3b clean P0 corpus.

Grid: `h` ∈ {3, 6, 10} × `s` ∈ {0, 1} × β ∈ {0, 1, 2, 4}, with calibration seeds
1 and 2 (48 corpora).

* **R0 (uncoupled):** the β = 0 configuration with the lowest mean distance.
* **R1 (coupled):** the β > 0 configuration with the lowest mean distance.
* Ties go to the smaller `h`, then the smaller β.
* **Manipulation check:** R1's edge MI must exceed R0's in both calibration
  seeds. If not, report the coupling as ineffective and stop the R1 arm.

Evaluation uses fresh seeds 101, 102 and 103 for each regime. No evaluation
corpus informs selection.

## Evaluations

**E1. Frozen transfer (primary).** Refit the §19 primary logistic model and the
boosting model on all Naibbe pairs, exactly as in `13_equivalence_classes.py`;
fitting is deterministic. Score every eligible type pair (frequency ≥20) in R0
and R1:

* ROC-AUC, PR-AUC and prevalence;
* nearest-neighbour and top-5 retrieval;
* clustering precision/recall at p = 0.5;
* the unfitted context-cosine baseline.

The label is the same plaintext syllable.

**E2. Within-family information check.** Class-held-out 5-fold CV of the same
logistic specification on each regime, one seed (101). It asks whether the
ciphertext carries the class information.

**E3. Mechanism diagnostic.** For true same-unit pairs that differ **only in the
terminal** (same prefix and core), report for R0 and R1:

* mean frozen p;
* mean `js_next_initial`;
* mean `cos_right_nocatch`.

Also report the same features, descriptively, for Voynich ZL same-stem r/l pairs
and for R0/R1 different-unit pairs.

**E4. Realism check (not calibrated, reported only).** Compute our
reimplementation of Parisel's E→S% and raw boundary MI (EVA glyph units, lines as
sentences), plus the fingerprint's withheld diagnostics (lag repetition and
edit similarity). Report these for Voynich, R0, R1 and Naibbe.

## Decision rules (fixed now)

* **Cross-family transfer.** Mean frozen logistic ROC-AUC on R0:
  * ≥ 0.85: transfers;
  * 0.70–0.85: partial;
  * below 0.70: fails.
* **Coupling blind spot confirmed** if both hold:
  * mean frozen logistic ROC-AUC on R1 is at least **0.05 lower** than on R0;
  * terminal-only true pairs have a lower mean frozen p in R1 than in R0.

  The direction must be the same in all three seed pairs.
* **Information present** if within-family class-held-out ROC-AUC on R1 is at
  least 0.90. A coupling-aware classifier would then be the remedy; it is named,
  not attempted here.
* **Consequence for Voynich:**
  * *If the blind spot is confirmed:* Voynich terminal-alternation pairs (r/l/n)
    showing different following contexts do not tell "distinct units" apart from
    "edge-conditioned homophones". The earlier r/l result (16/48 families) and
    the §19 Voynich output are then both uninformative about homophony for
    terminal alternations.
  * *If not confirmed:* the conflict between §19 merges and the r/l evidence
    stands as reported.

This stage identifies no Voynich class and assigns no meaning to anything. The
slot cipher is a designed test object; it is not proposed as the Voynich
mechanism, and fitting Voynich statistics is not evidence that it is one
(voynich-collective shows such profiles can be constructed).

## Outputs

`results/coupled_cipher_2026-09-25/`, containing:

* `calibration.json`, `selection.json`;
* `transfer.json` (E1, E2, E3), `realism.json` (E4);
* `manifest.json` (seeds, grid, hashes, versions).

Representative R0/R1 texts go to `representative_R0.txt` and
`representative_R1.txt`.

Any deviations will be recorded in `COUPLED_CIPHER_FINDINGS_2026-09-25.md`.
