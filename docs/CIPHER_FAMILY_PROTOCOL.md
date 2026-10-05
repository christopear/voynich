# Which kinds of cipher could have produced the Voynich text? — protocol

Written 26 September 2026, before any code or computation for this stage.

**Aim.** List historically plausible ways of producing the Voynich text
(ciphers available around 1420, plus two message-free reference mechanisms).
Simulate each on real Latin, Italian and German text laid out exactly like the
manuscript. Rule each out or keep it by fixed fingerprint rules (**step A**).
For the cipher families that survive, test whether their homophone groups can
be recovered from ciphertext, and apply that to Voynich (**step B**).

Known beforehand: all earlier project results, in particular:

* the mechanism benchmark (`MECHANISM_FINDINGS_2026-09-24.md`: three
  generators, none matching vocabulary richness and local repetition
  together);
* the §19 classifier failing its Voynich gates;
* the coupling and boundary results.

No statistic defined below has been computed for Voynich or any simulation.

## A. Hypotheses, simulation and fingerprints

### A1. Targets (Voynich)

Currier B paragraph (P0) lines of ZL3b, in file order, split into two windows
of whole pages:

* **W1:** pages from the start of Currier B until the cumulative slot count
  first reaches 5,000.
* **W2:** the following pages, until another 5,000 slots are reached.

Unclean slots stay in place and are unclean in every simulation too.

* The primary target is **ZL3b W1**. **ZL3b W2** is the replication target:
  the windows cover different sections.
* Secondary, descriptive: IT2a on the same pages, and v101 (raw v101 tokens)
  on the same pages.

### A2. Plaintexts

`latin_alfonsi.txt`, `italian_dante.txt` and `mhg_fh.txt` (German), normalised
as in `slot_cipher.latin_words`. Each seed starts at a random word offset that
leaves enough text. A family and language combination that cannot fill a
window without wrapping is **not run**, and this is reported.

### A3. Families (the hypotheses)

The grid is fixed now. "k" = cipher alphabet size.

| Code | Family | What it models | Parameter grid |
|---|---|---|---|
| F1 | **Plain / simple substitution** | a real language in its own alphabet, one symbol per letter, spaces = word spaces | language |
| F2 | **Homophonic substitution** | letters get several symbols in proportion to frequency (Italian chanceries, around 1400); spaces = word spaces | k ∈ {40, 60, 90}; language |
| F3 | **Nomenclator** | F2 (k = 40) plus code tokens for the N most frequent words, v variants each | N ∈ {30, 100, 300}; v ∈ {1, 3}; language |
| F4 | **Abbreviation / shorthand** | scribal contraction: common prefixes and suffixes become single signs, interior vowels dropped with probability p, then simple substitution | p ∈ {0.3, 0.7}; language |
| F5 | **Verbose homophonic, Naibbe tables** | each letter or letter pair becomes a whole "word" (`mechanism_models` encoding); spaces separate units | level ∈ {0, 1, 2}; coupling ∈ {0, 1}; language |
| F6 | **Verbose syllabic** | each syllable becomes prefix + core + terminal (`slot_cipher`) | h ∈ {2, 4, 8}; s ∈ {0, 1}; β ∈ {0, 2}; language |
| F7 | **Verbose with nulls** | F5 at level 1 with no coupling, plus null words inserted at rate r | r ∈ {0.10, 0.25}; nulls ∈ {fresh Voynich-like words, a fixed set of 20}; language |
| R1 | Assembly (reference, no message) | `mechanism_models` assembly | level ∈ {0, 1, 2}; coupling ∈ {0, 1} |
| R2 | Copy-and-modify (reference, no message) | `mechanism_models` copy | level ∈ {0, 1, 2}; coupling ∈ {0, 1} |

Details fixed now:

* **F2 symbol allocation.** Each letter gets 1 + round((k − L) · f) symbols,
  where L is the number of letters and f the letter's frequency. The total is
  adjusted to k by giving the rounding remainder to the most frequent letters.
  Each occurrence picks one of its letter's symbols uniformly.
* **F3 code tokens.** Each code token is a distinct string over a separate
  8-symbol code alphabet (length 2–3); variants are chosen uniformly.
* **F4 contractions.** Suffixes: `orum, ibus, tur, bus, que, us, um, is, em,
  ur, er, re; one, are, ato; en, er, ent`. Prefixes: `con, per, pro, prae`.
  Each becomes its own single sign, matched longest first. Words of ≥ 4
  letters lose each interior vowel with probability p, per occurrence.
* **F7 nulls.** Insertion is independent per position, and nulls count
  against the slot budget.
* **Voynich-trained parts.** F5 coupling, F6 cores and β, F7 fresh nulls, and
  R1/R2 all use a `mechanism_models.Training` fitted on **Currier B pages
  outside W1 and W2**, so the targets are never used for training.

**Layout modifier (all families).** Every configuration is run twice:

* **L0:** no layout rule.
* **L1:** a scribal layout convention:
  * the first token of a line gets a marker sign prepended with probability
    0.5;
  * the last token of a line gets a marker sign appended with probability
    0.5;
  * each token in a paragraph's first line gets a paragraph sign prepended
    with probability 0.3.

  These three signs are not used otherwise. L1 tests whether Voynich's line
  and paragraph effects need a rule of this kind, independent of family.

**Seeds.** 6 per configuration and layout, plus 2 held-out seeds used only for
the self-consistency gate.

### A4. Fingerprints

Tokens are treated as atomic types, so the primary fingerprints do not depend
on the cipher alphabet, on how glyphs are segmented, or on EVA vs v101. All are
computed on clean tokens with the same code for Voynich and simulations.
Adjacency never crosses an unclean slot or a page.

| # | Fingerprint | Measures |
|---|---|---|
| P1 | types / tokens | vocabulary richness |
| P2 | hapax share of types | open vs closed vocabulary |
| P3 | share of tokens from the 10 most frequent types | function-word-like dominance |
| P4 | adjacent exact repeats minus within-page collision baseline | `qokedy qokedy` repetition |
| P5 | corrected MI(word_i; word_i+1), within line | local word-to-word dependence |
| P6 | corrected MI(word type; page) | topic / page specificity |
| P7 | corrected MI(word type; line-initial position) | line-start effects |
| P8 | corrected MI(word type; line-final position) | line-end effects |
| P9 | corrected MI(word type; first line of paragraph) | paragraph-start effects |

* Word types are capped at the 200 most frequent, with the rest pooled.
* "Corrected" means the observed MI minus the mean over 20 permutations:
  * P5 permutes right-hand members within page;
  * P6 permutes tokens across the window;
  * P7–P9 permute tokens within page, which keeps page composition.
* **Secondary (descriptive, no vote):** mean word length in units, within-word
  conditional unit entropy, corrected MI(last unit; next first unit), and
  corrected MI of first/last unit with line-initial/line-final position. Units
  are EVA glyphs for Voynich and symbols for simulations.

### A5. Decision rules

For configuration c and fingerprint j, z = (V_j − mean_c,j) / sqrt(sd_c,j² +
sd_V,j²), where:

* mean_c,j and sd_c,j come from c's 6 seeds;
* sd_V,j is Voynich's sampling SD from a 200-replicate page bootstrap of the
  target window.

A configuration is **compatible** if |z| ≤ 3 on all of P1–P9.

* **Family verdict per target:**
  * **compatible** if at least one configuration (any language, parameters,
    layout) is compatible;
  * otherwise **excluded**. The binding fingerprints are those with |z| > 3 in
    the family's least-bad configuration (minimum over c of max |z|).
  * **"Compatible only with L1"** is reported when no L0 configuration is
    compatible.
* **Robust verdict:** the same verdict on ZL3b W1 and W2. Otherwise
  **window-dependent (undecided)**.
* **Transcriptions:** IT2a and v101 verdicts are reported. A disagreement with
  ZL3b is marked **transcription-sensitive**.

**Gate G1, self-consistency.** Each held-out seed of each configuration is used
as a pseudo-target, with its own family's configurations as candidates and the
same sd_V. At least **90%** of a family's pseudo-targets must come out
compatible with their own family. If a family fails, its Voynich verdict is
**not interpretable**.

**Report, not a gate: G2, discrimination.** For each pair of families, the
share of family X's pseudo-targets that are compatible with family Y. Families
with mutual compatibility ≥ 50% are **confusable**, and verdicts that separate
them are flagged.

**Interpretation, fixed now.**

* "Compatible" means **not ruled out by these fingerprints**. It never means
  the manuscript was made this way.
* If message-free R1 or R2 is also compatible, the fingerprints do not separate
  cipher from non-cipher, and this is stated.
* An exclusion holds only for the grid tested; a family variant outside the
  grid is not excluded.
* Plain language (F1) stands in for a lost language only through three
  European languages, and this limit is stated.

## B. Homophone-group recovery for surviving cipher families

**Scope.** Homophonic families F2, F3, F5, F6 and F7 that are robustly
compatible in A.

* If none is, step B runs only the calibration for F5 and F6, as reference,
  with no Voynich application.
* A family confusable with a surviving one is included.

**Corpus.** W1 + W2 layout (about 10,000 slots). The synthetic plaintexts are
Latin, and German where it fills the layout. Word-level F2 and F3 use Latin
only, because Italian and German are too short.

**Labels.** Plaintext unit per token:

* F2/F3: the plaintext word;
* F5/F7: the letter or letter pair (nulls get a unique label per null type, so
  they are never positives);
* F6: the syllable.

**Classifier.** The §19 pair features (`equivalence.Corpus`, primary groups,
logistic), with MIN_FREQ = 10 for this corpus size. It is trained on the
family's own synthetic texts: its compatible configurations from A, or all its
configurations if fewer than two are compatible. Evaluation is on held-out
seeds, and held-out language where two languages exist.

* **Gate H1:** held-out ROC-AUC ≥ 0.85 **and** precision ≥ 0.50 among pairs
  with p ≥ 0.8.

**Voynich application** (only if H1 passes). Score ZL3b W1 + W2 with the
frozen family-trained model, and compare Voynich's rate of pairs with p ≥ 0.8
against:

1. the family's own synthetic runs (5th–95th percentile);
2. Voynich with tokens globally shuffled (seed 20260925);
3. R1 and R2 texts at their best-matching configuration from A (the least-bad
   by max |z|).

**Reading, fixed now:** Voynich "shows the family's homophone signature" only
if its rate is inside the family's range **and** above both (2) and (3).
Candidate groups are listed as hypotheses, with no plaintext assigned.

## Outputs

`results/cipher_families_2026-09-26/`: `step_a_runs.json` (every run's
fingerprints), `step_a_verdicts.json`, `step_a_gates.json`,
`step_b_calibration.json`, `step_b_application.json`. Code:
`code/cipher_families.py`, `code/24_cipher_family_benchmark.py`,
`code/25_homophone_recovery.py`. Findings go in
`CIPHER_FAMILY_FINDINGS_2026-09-26.md`, with deviations listed.
