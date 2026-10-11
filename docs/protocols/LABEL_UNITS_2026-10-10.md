# Stage 36: what labels say about the size of a Voynich "word"

Preregistered before execution. Ledger rows 12, 13 and 15 (grouped, word-level
and syllabic units) and the open question "what are the spaces?". A
**structural diagnostic**. It assigns no meaning to any label and does not
verify which label belongs to which drawing.

## Question

A label is the one place where a unit boundary is known independently of the
spacing in running text: one label sits beside one drawn object. Two readings
of the manuscript's "words" predict different things about labels.

* **Word-sized units:** a Voynich word stands for a plaintext word. A label is
  then an ordinary, usually rare, word. Labels should look like other words of
  the same frequency, and the same word may appear in the text on its page.
* **Chunk-sized units:** a Voynich word stands for a syllable or letter group,
  and a name needs several chunks. A one-"word" label is then several chunks
  written together. Labels should be longer than other words of the same
  frequency, should split into common words more often, and their pieces may
  appear as neighbouring words in the text on the same page.

Copying without a message could also make labels echo nearby text. A positive
result on recurrence therefore says something about units only if a message is
assumed. It never shows that there is one.

## Data

ZL3b, all pages except the sealed confirmation sets X and Y. **Labels:** loci
whose type begins with `L`, with exactly one clean token (multi-token and
unclean labels are counted and set aside). **Running text:** every other locus
on the page, clean tokens, with the transcription's gap kinds. Neighbours in
running text require an `ordinary` or `uncertain` gap on the same line.
Reference frequency of a type is its count in all running text used here.
Counts known before this protocol: 1,003 label loci, 778 single clean labels on
51 pages. No test statistic below was computed beforehand.

## Measures

Frequency bins by running-text count: 0, 1, 2–4, 5–19, 20+. Label types with
count 0 are compared with running-text types of count 1, the nearest available
class. This is a declared approximation.

1. **M1 length.** Mean glyph length of label types minus that of running-text
   types in the same frequency bin, averaged over bins weighted by label types.
   Interval by bootstrap over label types (2,000, seed 3601).
2. **M2 whole recurrence on the page.** Share of label tokens whose word occurs
   in the running text of the same page. Null: label words permuted across
   pages within label kind (`Lz`, `Lf`, …), 999 permutations (seed 3602).
3. **M3 split recurrence on the page.** For label tokens of at least four
   glyphs: the share for which some split into two non-empty glyph strings
   (a, b) occurs as neighbouring running-text words a b on the same page. Same
   permutation null (seed 3603).
4. **M4 decomposability.** Share of label types of at least four glyphs that
   split into two running-text types each occurring at least five times.
   Control: 999 random sets of running-text types matched to the label types on
   glyph length and frequency bin (seed 3604). Types used as controls are
   excluded from the dictionary of pieces for their own test, as label types
   are for theirs.

One-sided permutation or matched-control p-values. With four measures, treat
p < 0.0125 as the threshold for calling an effect present.

## Calibration (before reading manuscript values)

* **Null validity:** apply M2 and M3 to 20 datasets where label words are first
  permuted across pages within kind (seeds 3700–3719). At most 2/20 may reach
  p < 0.0125 for each measure.
* **Power for M3:** from each permuted dataset, for a share r of labels with at
  least four glyphs, add the label's two halves (split at the middle glyph) as
  one extra two-word line in that page's running text. r ∈ {0.02, 0.05, 0.10};
  detection in at least 16/20 at r = 0.10 is required. Report the smallest r
  detected in 16/20.

If either gate fails, report the method as uncalibrated for that measure and
make no manuscript statement from it.

## Interpretation rules

* **Word-like labels:** M2 present, M1 and M4 not.
* **Concatenation-like labels:** M1 and M4 present; M3 present strengthens it.
* **Both, or neither:** report as mixed or uninformative. Do not pick a side.
* All conclusions are about labels as transcribed. Whether a transcribed label
  is one object's name is not verified here, and label kinds differ (zodiac
  figures, containers, plant parts, stars). Report M1–M4 by label kind as a
  descriptive breakdown, without separate claims.
* No statement about meaning, language or a cipher follows from any outcome.

## Outputs

`results/label_units_2026-10-10` with evidence, calibration and a README with
an evidence label; a verify module that reruns and compares; ledger update.
No historical results changed.
