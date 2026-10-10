# Stage 37: are n/l/r endings added markers?

Preregistered before execution. Ledger open question "Do r/l/n endings encode
different plaintext units?" (closed as undecidable by context statistics in
coupling test v3) and row 16. This uses a **different observable** from the
closed coupling tests: whether the word with its ending removed is itself a
word, and whether marked and bare forms divide by what follows. It is a
structural test and cannot show that the text has meaning.

## Idea (the user's)

Suppose the final n, l or r is not part of the word but a signal about the
next word, as if "now" were sometimes written "noww". Then:

1. removing the ending should usually leave a word that is common in its own
   right, more often than removing other endings does; and
2. for a stem seen both bare and marked, which form appears should depend on
   the next word's first glyph.

## Data

ZL3b Currier B paragraph lines (`P0`), all pages except the sealed
confirmation sets (which are Currier A, so none qualify). Clean tokens of at
least two compound-EVA glyphs. Neighbours require an `ordinary` or `uncertain`
gap on the same line. Type counts come from the same token set. Sensitivities,
reported without separate claims: IT2a on the same pages; non-sealed Currier A
paragraph text.

## Measures

For each final glyph g, over tokens ending in g, with stem = the word minus its
final glyph:

* **Attested:** share whose stem occurs as a word at least once.
* **Common (primary):** share whose stem occurs as a word at least five times.

**M1** = common share for the group {n, l, r} minus the common share for all
other endings pooled, token-weighted. Interval by resampling pages 2,000 times
(seed 3701), type counts held fixed. Also report every ending with at least 200
tokens separately, and type-weighted versions.

**M2** = for stems occurring both bare and with a final n, l or r, each with a
valid neighbour: mutual information between form (bare or marked) and the next
word's first glyph, given the stem, minus the mean over 999 permutations of
next-initials within stem (seed 3702). One-sided p.

Descriptive only: the share of all n/l/r-final tokens whose stem never occurs
as a word, with the twenty commonest such words; the same table for the cluster
variant (final `n` removed together with its preceding run of `i`); and M1 for
text sampled from the stage-31 glyph-chain model and from R2 trained on the
same lines. Both were trained on Voynich, so they show whether local glyph
statistics alone reproduce the pattern. They are not marker-free nulls.

## Calibration (before reading manuscript values)

On the manuscript token stream with word order shuffled within page (which
removes real coupling), using a new final glyph `z`, ten replicates each
(seeds 3800+):

* **True marker:** append `z` to a word with probability 0.6 when the next
  word's first glyph is in a fixed half of the inventory, else 0.05.
* **Random suffix:** append `z` with probability 0.3 regardless of context.
* **Lexical ending:** for a fixed random 30% of types, replace the final glyph
  by `z` in every occurrence.

Apply the decision rule with `z` as the tested group. Gate: fires in at least
8/10 true-marker replicates and at most 1/10 of each other kind.

## Decision rule

* **Marker-like:** M1 > 0 with its 95% interval excluding zero **and** M2
  present at p < 0.0125.
* **Not marker-like:** otherwise. Say which part failed.
* A high attested or common share on its own proves nothing: Voynich words are
  built from few parts, so shortened words are often words by chance. Only the
  comparison with other endings and the dependence on the next word count.
* A marker-like result would mean the ending behaves as a context-dependent
  addition. It would not show whether that is a cipher device, a scribal
  joining habit or a product of copying. R2 reproduces neighbour coupling.

## Outputs

`results/ending_markers_2026-10-10` with evidence, calibration and a README
with an evidence label; a verify module that reruns and compares; ledger
update. No historical results changed.
