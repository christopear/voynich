# Stage 35: does the start of a line act as an indicator?

Preregistered before execution. Ledger rows 14 and 16 (changing tables; state or
context used in decoding) and the open question "do line effects come from the
cipher?". This is a **structural test of one stated cipher mechanism**. It is
not a generator fit and cannot by itself show that the text has meaning.

## Question

A common way to run a cipher with several tables is to mark, at the start of
a line or paragraph, which table follows. If Voynich lines begin with such an
indicator, the first glyph of a line should predict the forms of the words later
in that line **more than any other word in the same line does**. Lines sharing
vocabulary for other reasons (topic, copying from the line above, habit) make
every word in a line predict the others about equally. The test is therefore a
contrast between positions, not an association on its own.

## Data

ZL3b paragraph lines (`P0` loci) on Currier B pages. Lines must have at least
nine words with the first nine clean. Pages in confirmation sets X and Y of the
image-pilot split are excluded by rule; they are Currier A, so none qualify.
Development herbal A pages (hand 1) are a declared low-power sensitivity (89
qualifying lines). B folios are divided into two halves by alternating folios
in manuscript order, for a replication check. All these pages have prior
exposure (inventory tiers 2–4). This statistic has not been computed on them
before.

## Statistic

For key position j ∈ {1, 2, 3, 4} (1 = first word of the line):

* Key K_j: the first glyph (compound EVA) of word j.
* Targets: the words at positions j+2 … j+5. The adjacent word is skipped so
  the known ending/next-initial coupling cannot contribute.
* Feature F of each target word. **Primary: its final glyph.** Secondary: its
  first glyph, and the whole word.
* E_j: conditional mutual information I(F; K_j | stratum) in bits per target
  token, minus the mean over 199 permutations (seed 3501) that shuffle line
  keys among lines within the stratum. Stratum = page × paragraph-first-line
  flag. Keys are permuted per line, so a line's targets keep sharing one key.

**Contrast D = E_1 − mean(E_2, E_3, E_4).** Also report E_j / H(K_j | stratum),
since the first glyph of a line has a different distribution from other words.

Uncertainty: stratum-level contributions to each E_j are computed once; pages
are resampled with replacement 2,000 times (seed 3502) to give a percentile
interval for D. Also report D in each folio half.

## Controls and calibration (before interpreting the manuscript value)

1. **Shuffled keys:** the manuscript with line keys permuted within stratum
   once (seed 3503): D should be near zero.
2. **Message-free text:** the stage-31 R2 generator trained on the same B
   lines (level 2, coupling off and on; seeds 101–106), laid on the same line
   layout. It has no indicator. Its D shows what copy-and-modify produces.
3. **Planted indicator (power):** start from the shuffled-key manuscript. Give
   each line a bit b from its first glyph (key alphabet split into two halves of
   near-equal mass, fixed lexically). For every non-initial word on lines with
   b = 1, with probability q replace its final glyph by a fixed permutation of
   the final-glyph inventory (seed 3504). q ∈ {0, 0.05, 0.1, 0.2, 0.4}, 20
   replicates each. Record how often the decision rule below fires.

Calibration gate: the rule must fire in at most 2/20 replicates at q = 0 and in
at least 16/20 at q = 0.4. If not, report the method as uncalibrated and make
no manuscript statement.

## Decision rule

* **Indicator signal:** primary D > 0 with the page-bootstrap 95% interval
  excluding zero on all B lines, D > 0 in both folio halves, and the normalised
  contrast also positive. Then report the size against the planted scale, and
  compare with R2. If R2 shows a similar D, say that copying also produces it.
* **No indicator signal:** otherwise. Report the smallest planted q detected in
  at least 16/20 replicates as the bound: a line-initial indicator affecting
  that share of word endings or more would have been seen.
* Either way the claim is limited to a first-glyph indicator acting on word
  endings within the same line, on Currier B paragraph text. Indicators at
  paragraph or page level, or acting on other parts of words, are not tested.
  Secondary features are descriptive and cannot rescue a null primary result.

## Outputs

`results/line_indicator_2026-10-10` with evidence, calibration, controls and a
README carrying an evidence label; a verify module that reruns and compares;
ledger update. No historical results changed.
