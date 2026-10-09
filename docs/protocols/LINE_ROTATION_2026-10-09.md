# Fixed versus alternating line tables — 9 October 2026

Written before execution. Motivated by the user's rotating-cipher hypothesis;
previous optimized Latin-like words are not established recoveries. This is a
bounded exploratory hypothesis, not a claim of historical attestation.

Use compound-EVA f26r for adaptive search; apply keys unchanged to f31r and f39v.
All are Currier B herbal pages. f31r was already used in the previous pilot;
f39v is an additional transfer page, not claimed untouched in prior research.
Use the same conservative word filtering, but retain manuscript paragraph-text
line slots, including lines with no surviving words. Phase advances at each such
line and resets to zero on every page. Omitted words do not alter the line clock.

Compare period 1 (a single injective letter table) against period 2 (independent
injective tables on alternating lines). Each observed cipher unit emits one Latin
letter. Spaces survive. This is not arbitrary switching, a dice model, homophony,
word/character rotation or unconstrained line-specific fitting. Test one narrow
extension at a time. No changing phase or period is fitted on transfer pages.

Score full joined text with the existing Celsus order-4 model, 60,000 normalized
characters at 30% of the source. The description-length cost of a table with n
observed symbols is log2(26!/(26-n)!), conditional on its observed alphabet. Sum
across tables; add one bit for the two predeclared periods. This charges additional
mappings; absolute objectives are not comparable to the previous pilot's key cost.
Pliny's analogous 60,000-character model is post-selection only.

For each period and seed (7,19), run original text, three whole-line permutations,
and one symbol-shuffled control. All period/seed combinations reuse each control
realization. Control seeds are 1001–1003 for line permutations and 1000 for symbols;
transfer uses 2001–2003 and 2000. Line shuffling keeps whole lines, word inventories,
and internal line structure but disturbs the proposed clock. Symbol shuffling
keeps every space/line slot and overall symbol counts. Each search uses beam width
8 and 4,096 evaluations: 20 manuscript runs, 81,920 proposals.

Add four blind synthetic calibration runs: one-table and two-table encryptions of
a 600-character Pliny passage at 65%, wrapped at whole words near 50 characters;
key seeds search_seed+500. Same training/scorer/budget. Known keys are evaluated
only after search for oracle consistency and search/score-gap diagnosis. The
synthetic cipher uses the full Latin alphabet; it validates this implementation,
not a matched Voynich-sized recovery distribution. Four runs are not enough to
estimate detection power. Total: 24 registered runs / 98,304 proposals.

Report (a) penalized two-table advantage, paired against one table, on originals
and each control; (b) Pliny score and coverage on both frozen pages; (c) exact
Pliny training-lexicon hits of length >=4, token fraction and distinct words;
(d) agreement of hit sets across seeds. Hits are morphology diagnostics, not
translations. Compare with controls subjected to identical search and selection;
repeated words and two optimizer seeds are not independent observations. Three
line permutations cannot establish statistical significance. Do not chase a
promising word by tuning the lexicon or transition rule after seeing outputs.

If blind recovery is weak, failed Voynich search cannot reject rotation. If two
independent tables improve controls similarly, their flexibility is a sufficient
explanation for the fitted improvement. A candidate needs coherent independent
predictions before any recovered-word claim. Review after the bounded screen.

Reproduce using a fresh registered specification:

```sh
uv run --env-file .env --locked python -m voynich.laboratory.rotation_pilot \
  --output results/runs/line-rotation-2026-10-09
```
