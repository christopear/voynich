# Capacity screen — 9 October 2026

**Length-preserving decoders cannot turn Currier B into Latin, Italian or
German.** This covers one-to-one substitution, "capacity two" homophone
merging, and line- or page-alternating tables, all with spaces kept. A
decoder of that kind can only work if roughly 1.5 or more Voynich glyphs stand
for each plaintext letter.

Produced by `uv run --locked python -m voynich.evaluation.capacity --output
results/capacity_screen_2026-10-09/screen.json` (code in
[`src/voynich/evaluation/capacity.py`](../../src/voynich/evaluation/capacity.py),
tests in `tests/test_capacity.py`). It runs in a few seconds and involves no
search.

## The argument

If each plaintext symbol is decoded from one cipher unit plus a state that the
decoder knows from layout, then any window of n plaintext symbols carries at
most the information in the matching n cipher units plus the state:

    H(P_1..P_n) <= H(C_1..C_n) + H(S_1..S_n)

This holds for every key of the family. It is the reason the 9 October
manuscript searches (page pilot, line rotation, phase initialization) could
improve their objective but never reach Latin-like text: their families cannot
contain such text.

## Results (bits; 20,000-unit blocks; cipher's highest block vs plaintext's lowest)

Gap = plaintext H_n − (cipher H_n + state bits). A positive gap means no key
works.

| Cipher units | Reference | One table, n = 2 / 3 / 4 | Two tables (+1 bit per window, generous), n = 2 / 3 / 4 |
|---|---|---|---|
| raw EVA | Celsus (medical Latin) | +1.32 / +2.04 / +2.02 | +0.32 / +1.04 / +1.02 |
| raw EVA | Pliny (medical Latin) | +1.40 / +2.24 / +2.35 | +0.40 / +1.24 / +1.35 |
| compound EVA | Celsus | +1.26 / +1.87 / +1.76 | +0.26 / +0.87 / +0.76 |
| compound EVA | Pliny | +1.35 / +2.07 / +2.09 | +0.35 / +1.07 / +1.09 |
| compound EVA | Alfonsi (Latin) | +1.36 / +2.05 / +2.09 | +0.36 / +1.05 / +1.09 |
| compound EVA | Dante (Italian) | +1.04 / +1.72 / +1.91 | +0.04 / +0.72 / +0.91 |
| compound EVA | Middle High German | +1.00 / +1.36 / +1.36 | +0.00 / +0.36 / +0.36 |

`screen.json` holds every combination, the per-block entropy profiles, and the
expansion estimates.

**Least expansion needed** (rough): about **1.5–1.7 Voynich glyph units per
plaintext letter** for Latin and Italian, and 1.25–1.5 for German. This applies
to raw and compound EVA alike. Plug-in entropy is biased downward for long
windows, which makes this estimate err high.

## Limits

* **Plug-in estimates.** These are finite-sample estimates on equal-sized
  blocks, not exact entropies. The comparison is conservative towards
  feasibility, because it uses the cipher's highest block and the plaintext's
  lowest. The margins at n = 3–4 (1–2 bits for one table) are far larger than
  the spread between blocks.
* **Normalised plaintext.** References use the solver's own normalisation
  (`decipher_search.core.normalize`). Period spelling and abbreviation would
  change plaintext entropy somewhat, but not by 1–2 bits per 3–4 letters.
* **Two tables.** The state term credits one full bit per window, which is
  generous: most windows lie within one line. Many tables, or per-word state,
  would need their own state budget.
* **Scope.** The screen says nothing about verbose, grouped, syllable or word
  codes beyond the expansion they need. Those families are where search
  effort should go next (see `AGENTS.md`).
