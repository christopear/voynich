# Voynich: context-conditioned variant choice

> **Correction, 10 October 2026.** Coupling and context choice counted drawing-separated words as neighbours, and secondary targets reused ciphertext encoded on the reserved layout (111–154 of 512 tokens differ when re-encoded). Corrected: edge_max development max residual 1.16 → 1.37, reserved B best 2.33 → 2.62; no joint hits. "With two alternatives, one choice cannot do both" should read "the tested rules did not achieve both". See [the boundary correction](../boundary_correction_2026-10-10/README.md). This directory and its producing code are kept unchanged so they still replay.

Stage 33, 9 October 2026. [Frozen protocol](../../docs/protocols/CONTEXT_CHOICE_2026-10-09.md),
committed at 2d2c8e1 before execution. Evidence label: **search found no fit in
a bounded forward-model grid**. No plaintext was recovered and no key was
searched for.

**In one paragraph.** Stage 32 left one binding Currier B failure: neighbouring
words did not influence each other. Here the encoder picks, from each word's two
codewords, the one whose last glyph suits the next codeword's first glyph. The
suitability table is learned from Voynich training folios, so some coupling is
built in. Choosing the better-suited alternative every time (`edge_max`) raises
coupling to about 0.09–0.10 bits, against Voynich's 0.12–0.25. Choosing in
proportion to suitability barely moves it. The selected rule comes closest of
any cipher so far on development pages (max residual 1.16), but has no joint
hits anywhere. A tension appears: page association needs a word to keep its
variant across a page, while coupling needs the variant chosen afresh from
context. With two alternatives, one choice cannot do both.

## Paired with stage 32 IID (same codebooks, keys, passages)

| Rule | Coupling change (median, range) | Length | Glyph entropy | Section excess |
| --- | --- | --- | --- | --- |
| iid | 0 (identical tokens) | 0 | 0 | 0 |
| edge (proportional) | +0.007 (−0.070 to +0.060) | −0.005 | −0.013 | −0.000 |
| **edge_max** | **+0.086 (−0.008 to +0.160)** | +0.032 | −0.022 | −0.006 |
| edge_refresh | +0.010 (−0.096 to +0.087) | −0.004 | −0.005 | **+0.141** |

Prediction 1 holds only for edge_max. The proportional rules have context on
432 of 512 tokens and unequal suitability on about 334, but the lifts are mostly
between 1 and 2, so a proportional choice is only weakly biased. Prediction 2
holds for edge and edge_max. With refresh, page association rises
(+0.14, overshooting) while coupling is lost: once a variant is stored, it is
reused whatever follows.

Trajectory cost per 512-token panel (median): edge 473 bits, edge_max 179
bits, edge_refresh 487 bits. edge_max spends randomness only where context is
missing or uninformative.

## Development selection and reserved comparison

Development medians against B_ZL_split_early (residuals in scale units: TTR,
top-ten, section, role, count≥5, length, glyph entropy, coupling):

| Setting | Max | Residuals |
| --- | --- | --- |
| iid | 2.30 | −1.0, 0.4, −1.2, −1.3, −1.3, 0.1, −0.6, **−2.3** |
| edge | 1.99 | −1.0, 0.4, −1.2, −1.3, −1.0, 0.1, −0.6, −2.0 |
| **edge_max (selected)** | **1.16** | −1.1, 0.5, −1.2, −1.2, −1.1, 0.1, −0.6, −0.7 |
| edge_refresh | 2.07 | −1.4, 0.5, +1.5, 0.1, 0.6, 0.1, −0.6, −2.1 |
| R2 level 2, no coupling (selected) | 2.10 | glyph entropy +2.1, coupling −2.1 |

| Target | Model | Joint hits | Best max | Section | Role | Length | Glyph entropy | Coupling |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B_ZL_split_early | cipher | 0/12 | 1.25 | 0.057 | 0.028 | 4.39 | 1.823 | 0.085 |
| B_ZL_split_early | Voynich | | | 0.115 | 0.086 | 4.34 | 1.981 | 0.120 |
| B_ZL_split_late | cipher | 0/12 | 2.33 | 0.045 | 0.018 | 4.50 | 1.862 | 0.102 |
| B_ZL_split_late | R2 | 0/6 | 4.67 | 0.175 | 0.072 | 4.79 | 2.653 | −0.014 |
| B_ZL_split_late | Voynich | | | 0.114 | 0.089 | 4.52 | 2.072 | 0.248 |
| B_IT_split_late | cipher / R2 | 0/12, 0/6 | 2.55 / 4.72 | | | | | |
| B_ZL_join_late | cipher / R2 | 0/12, 0/6 | 1.64 / 3.36 | | | | | |
| A_ZL_split_late | cipher / R2 | 0/12, 0/6 | 1.05 / 2.04 | | | | | |

On reserved B the best draw still misses coupling (−2.3), page and role
association (−1.4 to −1.6), the count≥5 contribution (−1.6) and the top-ten
share (+1.8). Stage 32's marginal Currier A result does not carry over: A's
coupling target is near zero, and edge_max adds coupling (0.064).
Calibration passed 16/16; discrimination 100%.

## Interpretation

* **Coupling can be produced by an encoder's choice, but only partly here.**
  Two alternatives per word and a deterministic suitability rule give about
  40–70% of B's measured coupling. More alternatives or stronger lifts were
  not tried (protocol: no tuning here).
* **The binding B mismatch is now page association under the IID-like rules.**
  The recipe plaintext laid on these pages gives about half of Voynich's
  association. Persistence can add association but conflicts with context
  choice. A plaintext with stronger page topicality (for example a medical
  source; stage 29 found Celsus passages up to 0.148 bits) would be a different
  route that needs no persistence. Stage 34 tests that.
* Neither family hits, so the decision rule records the mismatch and stops this
  grid. No non-identifiability or compatibility claim.

No decipherment, readings, family rejection or comparative support is claimed.

## Verification

`python -m voynich.laboratory.context_verify` checks hashes. It confirms the
codebooks equal stage 32's and the lift table equals the R2 edge table. It
replays all 168 panels (49,152 cipher tokens round-trip) and confirms IID and R2
panels are token-identical to stage 32. It recomputes calibration, selection,
every comparison and the paired differences. Deviations: none.
