# Voynich: what labels say about the size of a "word"

Stage 36, 10 October 2026. [Frozen protocol](../../docs/protocols/LABEL_UNITS_2026-10-10.md),
committed at 03f3557 before execution. Evidence label: **descriptive structural
diagnostic; uninformative on the word-versus-chunk question by its own rules**,
with one calibrated negative on label/page recurrence. No label is given a
meaning, and no label is verified against a drawing.

**In one paragraph.** A label beside a drawn object is the one place where a
unit boundary is known without trusting the spacing. If labels were names made
of several chunks, they should be longer than other words of the same frequency
and split into common words more often. They are not, by the thresholds set in
advance. If labels were words that the page's text also uses, they should
recur on their own page more than labels from other pages do. They do not:
10.9% recur, against 11.0% for labels shuffled between pages of the same kind.
Labels look like ordinary rare Voynich words with no measurable tie to the text
on their page. That settles neither reading of the "words". It does weaken the
hope that labels are an easy bridge between pictures and running text.

## Data

1,003 label loci outside the sealed pages: 135 multi-token and 90 unclean set
aside, leaving 778 single clean labels (622 types) on 51 pages. Running text
on the same pages and elsewhere: 32,258 clean tokens, 6,408 types. 337 label
types (54%) never occur in running text.

## Results

| Measure | Observed | Reference | Difference | p or interval | Present at 0.0125? |
| --- | --- | --- | --- | --- | --- |
| M1 length vs same-frequency words (glyphs) | 5.69 | — | +0.12 | 95% interval 0.01 to 0.24 | no |
| M2 label recurs in its page's text | 10.9% | 11.0% (shuffled within kind) | −0.0 points | p = 0.56 | no |
| M3 label's two pieces are neighbours on its page | 0.6% | 0.6% | +0.0 points | p = 0.58 | no |
| M4 splits into two common words | 63.7% | 60.0% (length- and frequency-matched words) | +3.7 points | p = 0.029 | no |

M1 by frequency class (label mean vs reference mean, glyphs): never in running
text 6.39 vs 6.00 (reference: words seen once); seen once 5.78 vs 6.00; 2–4
times 5.15 vs 5.28; 5–19 times 4.44 vs 4.65; 20 or more 4.10 vs 4.29. The small
overall excess comes only from labels absent from running text, compared with
words seen once, a declared approximation. In every class with a like-for-like
reference, labels are slightly shorter.

By the protocol's rules this is **"neither"**: not word-like (M2 absent) and
not concatenation-like (M1 and M4 below threshold). M4's p of 0.029 and M1's
interval are weak leanings toward longer, more decomposable labels. They are
recorded as such and not claimed.

## Calibration

| Check | Result | Gate |
| --- | --- | --- |
| M2 false alarms on 20 shuffled datasets | 0 | ≤ 2, passed |
| M3 false alarms on 20 shuffled datasets | 0 | ≤ 2, passed |
| M3 detects planted split recurrence in 2% / 5% / 10% of labels | 20 / 20 / 20 of 20 | ≥ 16 at 10%, passed |

M3 would have detected split recurrence in as few as 2% of labels. M2's power
was not separately calibrated; its null is exact by permutation, and the
observed value sits in the middle of the null.

## By label kind (descriptive, no separate claims)

| Kind | Labels | Mean length | Recur on own page | Type occurs in running text |
| --- | --- | --- | --- | --- |
| Lz zodiac | 235 | 5.91 | 5.5% | 50% |
| L0 other | 182 | 5.09 | 21.4% | 50% |
| Lf | 164 | 5.58 | 7.9% | 50% |
| Ls | 64 | 5.64 | 1.6% | 50% |
| Ln | 58 | 4.91 | 19.0% | 82% |
| Lt | 36 | 5.86 | 22.2% | 60% |
| Lc | 35 | 6.74 | 0.0% | 9% |

Kinds differ a good deal. `Lc` labels are long and almost never appear in
running text. `Ln` labels are short and mostly ordinary words. These kind
codes are the transcription's own; what each denotes is not verified here.

## What this does and does not say

* **Unit size stays open.** Labels neither confirm word-sized units nor look
  like joined chunks. This removes one cheap argument I had leaned on, that
  single-word labels favour word-sized or syllable-sized units; the data do not
  discriminate.
* **Labels are not tied to their page's text** beyond what any label of the
  same kind would show. If the text discusses the labelled objects by name,
  it does not use the label's form to do so, either whole or as two adjacent
  pieces. Under a cipher with a choice among alternatives, a name could be
  written differently each time, so this does not contradict a cipher. It does
  mean exact label matching is a poor route to cribs.
* Copy-and-modify text would be expected to echo nearby labels; none is seen.
  That is mildly unexpected for simple self-citation, but labels and text may
  have been written at different times. No claim.
* Limits: zodiac pages have little paragraph text; the within-kind shuffle
  controls for section vocabulary, which is the intended comparison, but it
  also means section-level sharing is not measured. Whether a transcribed
  label is one object's name is unverified.

## Verification

`python -m voynich.laboratory.label_units_verify` checks source hashes and
reruns the whole stage, requiring identical `evidence.json` and
`calibration.json`. Unit tests cover compound-glyph splits, page locality, the
within-kind shuffle and exclusion of sealed pages. On 40 real drawing-gap pairs,
none was counted as a neighbour unless the same pair also occurs with a normal
space on that page. Deviations: the "controls excluded from the dictionary of
pieces" clause is vacuous (a word cannot be its own proper piece); nothing else.
