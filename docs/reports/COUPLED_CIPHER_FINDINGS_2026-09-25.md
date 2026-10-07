# §19 transfer to a coupled non-Naibbe cipher: findings

25 September 2026.

* **Protocol:** `COUPLED_CIPHER_PROTOCOL.md`, committed before any cipher text
  was generated or scored.
* **Background reading:** `LITERATURE_NOTES_2026-09-25.md`.
* **Code:** `code/slot_cipher.py` and `code/15_coupled_cipher_transfer.py`.
* **Results:** `results/coupled_cipher_2026-09-25/`. A rerun reproduces every
  output byte for byte.

## Main finding

**The equivalence-class method generalizes beyond Naibbe, but it has a blind
spot exactly where Voynich differs from Naibbe.**

* **Cross-family transfer.** On a labelled homophonic cipher from a different
  design family (syllable units, Voynich-Markov cores, prefix/terminal
  homophones), the frozen Naibbe-trained classifier recovers hidden equivalences
  well: mean ROC-AUC 0.947, against 0.756 for context alone.
* **The blind spot.** In the coupled version (R1), the terminal homophone is
  chosen to suit the *next* word's first glyph, as Voynich's cross-word
  dependence would require. Performance then drops:
  * mean ROC-AUC falls from 0.947 to 0.876;
  * true homophones that differ only in their terminal fall from mean p ≈ 0.57
    to ≈ 0.27.

  The pre-set rule declares the blind spot confirmed; it held in all three seed
  pairs.
* **Why.** A coupled terminal carries information about the *following* word,
  not about the unit. True terminal-only homophones in R1 differ *more* in their
  following-initial distributions (JS divergence 0.29) than unrelated pairs do
  (0.23). In the uncoupled cipher they differ less (0.11 against 0.155).

**Consequence for Voynich** (the protocol's pre-set rule):

* Voynich terminal alternations (r/l/n) with different following contexts
  cannot tell "distinct units" apart from "edge-conditioned homophones".
* The handoff's r/l result (16/48 families with distinct following-initial
  distributions, reproduced exactly on 25 September) is exactly what coupled
  homophony would also produce.
* The §19 Voynich output is likewise uninformative about homophony for terminal
  alternations.

Keeping r/l/n distinct in latent representations is still a sensible precaution,
but the stated justification no longer supports it.

## Design recap

Each Latin syllable (Alfonsi text, fixed onset-maximizing split; 874 syllable
types, 33,970 tokens filling the ZL3b layout template) maps to a unique core from
a Voynich glyph Markov model. Each syllable has `h` homophones
`prefix + core + terminal`, with prefix ∈ {"", o, qo, y} and terminal ∈
{"", y, n, l, r, m}. The code book is invertible, and every run is round-trip
checked.

Coupling reweights the terminal choice by Voynich's own end→initial affinities
(`Training.edge`), raised to β.

The protocol's grid was `h` ∈ {3, 6, 10}, `s` ∈ {0, 1}, β ∈ {0, 1, 2, 4}, with
two calibration seeds, scored on the mechanism benchmark's six-statistic
distance. Selected:

* **R0:** h = 10, s = 1, β = 0 (distance 10.3);
* **R1:** h = 10, s = 1, β = 2 (distance 9.0).

**Manipulation check** (passed): R1's n/l/r edge MI is 0.064 in both seeds,
against ≈0.001 for R0. Voynich's is 0.070.

## Results

Frozen models refitted on all Naibbe pairs, exactly as in `13`. Evaluation seeds
101–103; types with frequency ≥20.

| | R0 uncoupled | R1 coupled |
|---|---|---|
| Types / classes per seed | 375–386 / 128–132 | 378–397 / 119–124 |
| Context-cosine baseline ROC-AUC (mean) | 0.756 | 0.731 |
| **Frozen logistic ROC-AUC** (per seed) | **0.947** (0.947, 0.949, 0.945) | **0.876** (0.871, 0.859, 0.899) |
| Frozen boosting ROC-AUC (mean) | 0.898 | 0.861 |
| PR-AUC, logistic (prevalence ≈1.1%) | 0.42–0.49 | 0.24–0.33 |
| Nearest-neighbour / top-5 retrieval | 81–86% / 93–95% | 73–77% / 84–90% |
| Cluster precision / recall at p = 0.5 | 0.50–0.70 / 0.63–0.72 | 0.49–0.68 / 0.27–0.32 |
| Within-family class-held-out CV ROC-AUC (seed 101) | 1.000 | 1.000 |

Two notes on these results:

* **Logistic vs boosting.** The logistic model transfers better than boosting
  across families, as it did for the Naibbe-table encodings.
* **Within-family CV of 1.0.** The class information is fully present in both
  regimes. That is partly trivial: shared cores make this family's form
  structure transparent once a model is trained on it. The result does not show
  that a coupling-aware model is required. It shows that the *frozen* model's
  context weighting is what fails under coupling.

**Mechanism diagnostic (E3)**, seed 101, with seeds 102–103 in parentheses:

| Pair type | Regime | n | Mean frozen p | JS next-initial | Cosine right (no catch-all) |
|---|---|---:|---:|---:|---:|
| True, terminal only | R0 | 168 | 0.545 (0.581, 0.577) | 0.110 | 0.599 |
| True, terminal only | R1 | 187 | **0.270** (0.259, 0.287) | **0.297** | 0.549 |
| True, other | R0 | 649 | 0.623 | 0.113 | 0.596 |
| True, other | R1 | 675 | 0.426 | 0.207 | 0.568 |
| Different unit | R0 | 73,488 | 0.063 | 0.155 | 0.438 |
| Different unit | R1 | 74,993 | 0.044 | 0.233 | 0.429 |

**Descriptive comparison** (not a test). Voynich ZL same-stem r/l pairs (n = 32)
have mean frozen p 0.37, JS next-initial 0.19 (against a mean of 0.30 over all
pairs) and right cosine 0.45.

Unlike R1's true terminal homophones, Voynich r/l pairs sit *below* the corpus
average divergence. If they were edge-conditioned homophones, the coupling at
those particular terminals would have to be weaker than in R1, even though
overall edge MI is similar. Cross-corpus baselines differ, so this is a hint for
a designed test, not a finding.

## Realism: how Voynich-like the test cipher is

The slot cipher was tuned to Voynich, but only one of the six targets was met
well. It is a **designed test object with Voynich-level edge coupling, not a
Voynich imitation**.

| Statistic | Voynich ZL | R0 | R1 |
|---|---:|---:|---:|
| Token length, glyph units (mean / SD) | 4.45 / 1.64 | 6.95 / 1.92 | 6.94 / 1.93 |
| Type/token ratio | 0.194 | 0.115 | 0.117 |
| Hapax share | 0.667 | 0.352 | 0.355 |
| Within-token glyph entropy | 2.17 | 2.74 | 2.74 |
| n/l/r edge MI (shuffle-corrected) | 0.070 | 0.001 | **0.064** |
| E→S%, our reimplementation | 80.3 | 40.4 | 40.4 |
| Raw boundary MI, our reimplementation | 0.201 | 0.012 | 0.137 |

On lag repetition and edit similarity, neither regime reproduces Voynich's
modest short-range recurrence; the mechanism benchmark saw the same gap. The
grid had no lever for core length or vocabulary openness, so tokens are too long
and the vocabulary too closed. The conclusions are therefore about *edge-coupled
homophony*, not about a cipher matching Voynich in every respect.

**Parisel-style metrics.** Our E→S% and boundary-MI reimplementation uses EVA
glyph units, while Parisel's code uses a greedy multi-glyph tokenizer. The values
are not comparable to his published references: for Naibbe, his tool gives
52.1% / 0.221 and ours gives 74.2% / 0.007. Directions agree (Voynich far above
Naibbe on boundary MI), but E→S% is clearly tokenizer-sensitive.

## What this changes

* **§19 method:** it works across two cipher families (Naibbe tables, slot
  cipher) when homophone choice is context-free. It degrades predictably when
  choice depends on the neighbour. Its Voynich output must not be read as
  evidence for or against homophony between terminal variants.
* **Handoff guardrail** (`CONTINUATION.md` §4.4, "r ≈ l is wrong; r/l carry real
  information"): the evidence shows that r/l carry information about the
  *following* word. It does not show that they encode different plaintext
  states. Keep r/l distinct as a precaution, but treat their plaintext status as
  open.
* **Next test worth running:** a coupling-aware equivalence test. For each
  candidate terminal-alternation pair, condition on the next token's initial and
  test whether any residual context difference remains. Under pure edge-coupled
  homophony it should vanish; for distinct units it should persist.
  * Calibrate it on R0/R1, where the answer is known, before touching Voynich.
  * This extends the handoff's OK/OT residual-context idea to terminals, with the
    missing positive and negative controls.

## Deviations and limitations

* **Protocol.** No deviations. The selected configurations lie at the grid edge
  (h = 10). The grid could not reach Voynich's token length or hapax share; this
  is a design limitation, reported rather than re-tuned.
* **Plaintext.** One plaintext, one language, and syllable units only. Other unit
  inventories (letters, words or nomenclator entries) were not tested.
* **Parisel.** The paper text was not read: this environment blocks arXiv and its
  mirrors. The signature definitions come from the author's code, read in full.

```bash
OPENBLAS_NUM_THREADS=1 uv run --locked python code/15_coupled_cipher_transfer.py
uv run --locked python -m unittest discover -s code -p 'test_slot_cipher.py' -v
```
