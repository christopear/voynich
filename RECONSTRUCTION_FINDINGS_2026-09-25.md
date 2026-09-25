# Reconstruction of unverified handoff claims

25 September 2026. The original exploratory session's drivers for many numbers in
`CONTINUATION.md` and `results/results_snapshot.json` could not be retrieved.
This round rebuilds them from local data with explicit definitions. The code is
`code/reconstruction.py` (one function per claim) and `code/12_reconstruct_claims.py`
(driver). Outputs are `results/reconstruction_2026-09-25/claims.json` (snapshot value,
reconstructed value, status, definition and any alternatives tried),
`parser_sensitivity.json` and `manifest.json` (input hashes).

## How to read this

Where a claim's definition was not written down, plausible readings of the handoff
text were tried against the recorded value. That is a search for the original
definition, not a fresh test: an exact match shows the recorded number is
arithmetic that can be reproduced, not that the analysis behind it is sound. Every
definition tried is saved in `claims.json`, including the ones that did not match.
Nothing here changes the inferential standing that `REVIEW_2026-09-24.md` gave these
results. Most are full-corpus, in-sample, exploratory statistics.

Status labels:

* **exact**: matches at the recorded precision.
* **within noise**: differs only by shuffle/seed variation.
* **approximate**: same regime; the original definition is not fully recoverable.
* **qualitative**: direction and significance reproduced, magnitudes differ.
* **not reproduced**: no definition tried recovers the value.

## Summary

| Claim (CONTINUATION section) | Recorded | Reconstructed | Status |
|---|---|---|---|
| Internal m with n/l/r sibling (4.3) | 85.4% | 85.4% (234/274) | exact |
| r/l families with distinct following initials (4.4) | 16/48 | 16/48 | exact |
| Rare long forms decomposable (6.1) | 1,661/3,250 = 51.1% | 1,661/3,250 = 51.1% | exact |
| Interior-shuffle null (6.1) | 4.7% | 4.6% (single shuffles 3.9–5.2%) | exact count; null within noise |
| Cut after n/l/r/m vs other (6.2) | 51.8% vs 7.8%; RR 6.62; OR 12.66 | identical | exact |
| Exact spaced alternations (6.3) | 359; 234 forward-only, 97 reverse-only; ratio 1.66 | identical | exact |
| Naibbe boundary localization (8.2) | 646 cases, 97.83% | 632/646 = 97.83% | exact (discrepancy explained) |
| Naibbe context-only homophone recovery (14) | AUC 0.748; nearest-neighbour 32.9%; top-5 47.4% | identical, incl. 178/152 types | exact |
| Page-first token uniqueness, raw (16) | 87.4% | 87.4% (83/95) | exact |
| Currier A/B excess MI; page counts (15) | 0.0283 / 0.0778; 112/46/28/7/2 | 0.0285 / 0.0780; identical counts | within noise |
| Voynich MI trajectory; vocabulary (8.3, 9) | 0.0741 → 0.0885 → 0.1174; 2,468 → 1,991 → 1,640 types | 0.0764 → 0.0884 → 0.1172; identical types | within noise |
| Random type-collapse control (9) | 0.0865 [0.0813, 0.0925] | 0.0872 [0.0814, 0.0938] | within noise |
| Naibbe MI trajectory (8.3) | 0.0877 / 0.0962 / 0.6481 | 0.0881 / 0.0948 / 0.6476 | within noise |
| m line-final vs r/l siblings (4.2) | 68.5% vs 7.9%, 8.7× | 69.2% vs 7.6%, 9.1× (grid 67–71% vs 7–9%) | approximate |
| Split-vs-unsplit classifier (7) | sens 0.839, spec 0.916, accepted 0.993 | 0.856, 0.929, 0.994 | approximate |
| Naibbe compound-vs-single (8.2) | bal. acc. 0.827; accepted 0.996 | 0.826; 0.994 | approximate |
| Matched-window glyph entropy (10) | e.g. Voynich 2.219/1.824, Latin 3.165/2.408 | 2.231/1.828, 3.170/2.403; other rows off ≤0.15 | approximate |
| Page-first token uniqueness, latent (16) | 70.5% | 67–75% depending on gallows handling | approximate |
| Prefix lattices in 6,000-token windows (11) | Voynich 6.3, Naibbe 6.9, languages ≈0 | EVA prefixes: Voynich 9.8, Naibbe 3.8; character prefixes: 12.2, 7.0; languages 0–0.5 | qualitative |
| OK/OT residual context (13) | Voynich pooled 0.038 (p .012); OKO/OTO 0.145 (p .001) | 0.010 (p .013); 0.043 (p .014) | qualitative |
| Same-stem context cosines (4.1) | chor/chol 0.737 etc. | not recovered | not reproduced |
| Random edge-pruning control (9) | 0.0486 | definition not recorded | not attempted |

The hidden-boundary terminal prediction (6.4, 63.9% → 70.8%) was already
reproduced exactly by `boundary.py` in the 24 September review. It is not repeated
here.

## Notes on individual claims

**Rare-form decomposition, cut positions and alternations.** All three reproduce
from a single definition. Use the full corpus of paragraph text; take types with
frequency ≤2 and at least six EVA glyph units; call a cut valid when both pieces
have corpus frequency ≥5. This is the same threshold `boundary.py` uses. Any cut
position counts, including after the first glyph. The review's caveats still apply.
Frequencies and candidates come from the same corpus. Because frequent tokens
disproportionately end in n/l/r, a cut after those glyphs yields a frequent left
piece more often almost by construction. So the 12.7 odds ratio describes the
vocabulary and does not independently show where boundaries are. Cuts within one
word are not independent observations.

**r/l families.** A family is a stem with at least 10 within-line `stem+r` and 10
`stem+l` tokens. Its statistic is MI(terminal; next initial), tested against 200
r/l relabellings. This gives exactly 48 families and 16 above the 95th percentile,
and every family `CONTINUATION.md` names is among the 16. The tests are
uncorrected; about 2.4 false positives would be expected by chance.

**Naibbe 646 vs 634.** The recorded 646 cases are two-part compounds with at least
one candidate split. A wrong top candidate counts as an error, giving 632/646.
Script 04 also drops the 12 compounds whose true cut is not a candidate, giving
632/634. Both count the same 632 successes. The recorded figure is the fairer of
the two, because it does not exclude cases where the method cannot succeed.

**Information trajectory.** The segmented and normalized vocabularies (1,991 and
1,640 types) match only when each page is segmented with frequencies from the other
94 pages. The type-collapse control matches when the *segmented* sequence is
collapsed at random onto 1,640 classes. The recorded surface value (0.0741) sits
inside the spread across shuffle seeds (0.073–0.076). With only 20 shuffles, the
third decimal place of every excess-MI figure is noise. The edge-pruning control's
definition is not recorded. One candidate (dropping 30% of tokens at random) gives
a similar number, but choosing that fraction afterwards would be fitting, so it is
not reported as a reconstruction.

**Split-vs-unsplit.** The recorded threshold −2.1654 was reused, not re-learned.
Positives are joined held-out pairs; negatives are every held-out written token.
Changing the negative class moves specificity between 0.71 and 0.93 (see
`negative_class_variants`). The headline specificity therefore depends mostly on a
definition that was never recorded.

**Glyph entropy.** Conditional entropy is computed within words, over
non-overlapping 3,000-token windows. Voynich surface and Latin match to about 0.01
bits. Naibbe, Italian and MHG differ by up to 0.15, probably because of text
cleaning and window choice. The ordering claim holds: Voynich and Naibbe are about
2.0–2.2 bits at H1, Latin and Italian about 3.0–3.2. MHG's H2 (1.56) is lower than
Voynich surface (1.83), as it was in the recorded table.

**Lattices.** The result depends on the definition. With EVA-glyph prefixes, OK/OT
is the top pair in 5 of 6 Voynich windows, but Naibbe then has only 3.8 qualifying
pairs per window. With character prefixes, Naibbe reproduces (7.0 pairs, max 11.4),
but ch/sh overtakes OK/OT in Voynich. No single definition gives the recorded
combination. Both definitions agree that the natural-language texts have almost no
such lattices. The Italian and MHG files hold only one 6,000-word window each.

**OK/OT residual context.** The pattern reproduces:

* Naibbe true homophones show no residual context (p 0.79).
* Naibbe different-plaintext pairs are significant (p 0.003).
* Voynich OK/OT pooled over 18 remainders is significant (p 0.013).
* OKO/OTO is the strongest single Voynich contrast.
* OKCHO, OKCHY, OKEO and OKSHO show nothing.

The effect sizes are several times smaller than recorded, and OKO/OTO reaches
p = 0.014 rather than 0.001. Excess MI depends on sample size, so its magnitude
should not be compared between Naibbe (683 tokens) and Voynich (6,734). A
non-significant remainder is not evidence of homophony; the review makes this
point about equivalence tests.

**Context cosines.** None of 12 context representations gives 0.737 / 0.716 /
0.658 / 0.653. `voynich_core.context_vectors` pushes all cosines towards 1 through
its shared catch-all dimension: chor/chol comes out at 0.987. The underlying
claim, that same-stem terminal variants share contexts more than unrelated words
do, was tested with a documented substitute. It covers 87 same-stem pairs with
frequency ≥10, each matched to an unrelated word of similar frequency:

* With the catch-all dimension, same-stem pairs barely differ from controls
  (medians 0.906 vs 0.900; same-stem higher in 57% of pairs).
* Without it, the difference is clearer (0.222 vs 0.157; same-stem higher in 76%
  of pairs).

The recorded values should not be cited. The direction of the claim survives only
under the second representation.

## Parser sensitivity

The original tokeniser keeps the first reading only for plain `[abc:def]`
alternatives. For others it either concatenates both readings or splits the word:

* `daiiir[{ih}:ch]y` → `daiiirihchy`
* `dai[{cto}:@194;]y` → `daicto y`

This affects 76 of 4,130 paragraph lines. `parse_zl3b(..., fix_alternatives=True)`
keeps the first reading instead; the default is unchanged. Rerunning the
parser-dependent claims with the fix (`parser_sensitivity.json`) changes the corpus
from 35,130 to 35,124 tokens. Every claim moves by at most about 0.3 percentage
points: decomposable 51.1% → 51.0%, alternations 359 → 359, r/l families 16 → 17
of 48, Currier excess MI in the fourth decimal place. The bug is real, but it does
not drive any of these results. The stricter parser in `06_boundary_frontier.py`
remains the better choice for new work.

## What this changes

* Most hidden-segmentation numbers in `CONTINUATION.md` sections 6.1–6.3 now have
  runnable code and regression tests. Their evidential weight is unchanged: they
  are in-sample descriptive statistics.
* The Naibbe localization discrepancy was a difference in denominator, not a
  change in method or data.
* The same-stem cosine values in section 4.1 should be withdrawn. The lattice and
  OK/OT magnitudes in sections 11 and 13 should be cited only as definition-dependent.
* The information-trajectory figures (sections 8.3 and 9) reproduce but carry
  noise in the third decimal place from 20-shuffle nulls.
* Three kickoff items remain open: the §19 latent equivalence classifier, the
  edge-pruning control, and any claim that depends on unrecorded thresholds.

## Reproduce

```bash
uv sync --locked
uv run --locked python code/12_reconstruct_claims.py
uv run --locked python -m unittest discover -s code -p 'test_*.py' -v
```

`code/test_reconstruction.py` locks the exact reconstructions and the original
script 01/02 headline values (excess MI 0.059405; 233/257 boundary localizations).
It also tests the parser fix in both modes.
