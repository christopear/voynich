# Voynich structural analysis

A research programme on the statistical structure of the Voynich Manuscript's
text (ZL3b EVA transcription), using Greshko's Naibbe cipher as a positive
control. It does **not** claim a decipherment, language identification or
translation.

## Current state (25 September 2026)

* **Strongest result.** In Currier B, the following word's first glyph improves
  prediction of an n/l/r word ending. This holds when the stem's spelling family
  and its physical folio are withheld, and survives a second transcription and
  three glyph segmentations. Currier A is inconclusive.
* **Key limit.** A generator with no underlying message also passes that test, so
  the effect does not distinguish meaningful text from structured pseudotext.
* **Mechanism attribution.** Telling generative mechanisms apart does not yet work
  reliably. None of the three simulated mechanisms reproduces the manuscript's
  combination of open vocabulary and modest local repetition.
* **Reconstructions.** Of 22 claims from the original handoff whose code was lost,
  9 now reproduce exactly and 4 within shuffle noise. 5 are approximate and 2
  qualitative. The same-stem cosine values could not be reproduced, and the
  edge-pruning control has no recorded definition.
* **Hidden equivalence classes (§19).** On Naibbe-family ciphers, a
  ciphertext-only pair classifier recovers same-plaintext cipher types well beyond
  context alone. This holds on held-out classes and on new plaintexts (ROC-AUC
  0.89–0.95). On Voynich the pre-set gates failed, so its candidate groupings are
  similarity hypotheses only, not homophone classes.
* **Coupled-cipher test.** On a labelled non-Naibbe cipher the same classifier
  still works (ROC-AUC 0.95), but it loses true homophones when the homophone
  choice depends on the next word (AUC 0.88; terminal-only homophones p 0.57 →
  0.27). Voynich-style edge coupling is exactly that case. So the evidence that
  r/l "carry information" does not show that they encode different plaintext.
* **Coupling-aware test.** A residual-context test that controls for boundary
  glyphs did not pass calibration: it has too little power. So its Voynich result
  (only 2 of 34 r/l/n pairs flagged) is not interpreted. The calibration did show
  that the naive r/l test flags 69% of true coupled homophones as "different". The
  question of whether r/l/n encode different plaintext is open.
* **Coupling-aware test, closed (v2/v3).** A cross-fitted, pooled version passes
  its leakage and pooled-calibration gates. On Voynich, however, ZL3b and
  Takahashi disagree (p = 0.12 vs 0.03), and the test is underpowered even
  against random distinct Voynich pairs (60–72%). As the protocol pre-declared,
  whether r/l/n alternations are one unit or several is recorded as **not
  decidable by context statistics** on this corpus. Stable result across all
  versions: the naive r/l test flags 71% of true coupled homophones as
  "different".

## Reading order

1. `CONTINUATION.md`: the original handoff from the exploratory session. Read its
   status note first: several numbers have since been corrected or qualified.
2. `REVIEW_2026-09-24.md`: independent reproduction audit and literature context.
3. `FRONTIER_PROTOCOL.md` → `FRONTIER_FINDINGS_2026-09-24.md`: terminal
   prediction on unseen folios and stems; transfer to drawing, line and paragraph
   boundaries.
4. `MECHANISM_PROTOCOL.md` → `MECHANISM_FINDINGS_2026-09-24.md`: robustness gate
   and competing-mechanism benchmark.
5. `RECONSTRUCTION_FINDINGS_2026-09-25.md`: claim-by-claim reconstruction of the
   handoff numbers whose drivers were lost.
6. `EQUIVALENCE_PROTOCOL.md` → `EQUIVALENCE_FINDINGS_2026-09-25.md`: the §19
   same-plaintext classifier, calibrated on Naibbe and applied to Voynich.
7. `LITERATURE_NOTES_2026-09-25.md`: Parisel (2026), antenore/voynich-toolkit
   and voynich-collective, as read against this project.
8. `COUPLED_CIPHER_PROTOCOL.md` → `COUPLED_CIPHER_FINDINGS_2026-09-25.md`: §19
   transfer to a non-Naibbe cipher with and without edge coupling.
9. `COUPLING_TEST_PROTOCOL.md` → `COUPLING_TEST_FINDINGS_2026-09-25.md`:
   coupling-aware test for terminal alternations, calibrated on a shared-core
   cipher.
10. `COUPLING_TEST_V2_PROTOCOL.md`: version 2 of that test (distributional
    neighbour classes, pooled test, 10-seed calibration). It is set up as an
    overnight run; see `overnight/README.md`. Findings are in
    `COUPLING_TEST_V2_FINDINGS_2026-09-26.md`: power improved (AUC 0.85), but
    the gates failed and a class-leakage flaw was identified.
11. `COUPLING_TEST_V3_PROTOCOL.md` → `COUPLING_TEST_V3_FINDINGS_2026-09-26.md`:
    version 3, with cross-fitted classes. The leak is fixed and the pooled test is
    valid, but the Voynich result is inconclusive. The question is closed.

`CODEX_KICKOFF.md` is the original task brief.

## Layout

| Path | Contents |
|---|---|
| `code/01`–`05`, `voynich_core.py` | Original handoff scripts and helpers |
| `code/boundary.py` | Recovered driver for the visible-to-hidden boundary test |
| `code/06`–`07` | Frontier experiment (prospective protocol) |
| `code/08`–`11`, `mechanism_models.py` | Robustness gate and mechanism benchmark |
| `code/12_reconstruct_claims.py`, `reconstruction.py` | Reconstructions of lost claims |
| `code/13`–`14`, `equivalence.py` | §19 equivalence-class classifier and post-hoc diagnostics |
| `code/15`, `slot_cipher.py` | Labelled slot cipher and coupled-cipher transfer test |
| `code/16`, `coupling_test.py` | Coupling-aware terminal-alternation test |
| `code/17`, `coupling_test_v2.py`, `overnight/` | Version 2 test and the overnight runner |
| `code/18`, `coupling_test_v3.py` | Version 3 test (cross-fitted classes); run via `overnight/run_v3.sh` |
| `code/test_*.py` | Unit and regression tests |
| `data/` | Corpora (fetched by `code/fetch_data.py`); provenance READMEs in subfolders |
| `results/` | Outputs by stage; `results_snapshot.json` holds the original recorded values |

## Running

Uses [uv](https://docs.astral.sh/uv/) with Python 3.14 (`pyproject.toml`, `uv.lock`).

```bash
uv sync --locked
./run_all.sh          # fetch data (network), scripts 01-05, reconstruction
uv run --locked python -m unittest discover -s code -p 'test_*.py' -v
```

The frontier and mechanism commands are listed in `code/README.md`.
