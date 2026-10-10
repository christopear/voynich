# Voynich: does the start of a line act as an indicator?

Stage 35, 10 October 2026. [Frozen protocol](../../docs/protocols/LINE_INDICATOR_2026-10-10.md),
committed at 96d820e before execution. Evidence label: **statistically bounded
negative for one stated mechanism** (calibrated test, stated domain). No
readings; this test cannot show whether the text has meaning.

**In one paragraph.** A cipher with several tables often marks at the start of
a line which table follows. If Voynich did this with the line's first glyph,
that glyph should predict the endings of later words in the line more than any
other word in the line does. It does not. On 1,374 Currier B lines from 81
pages, the first glyph predicts later endings by −0.002 bits per word (zero),
and the contrast against positions 2–4 is −0.005 (95% interval −0.019 to
+0.011). The test detected a planted indicator in 16 of 20 trials when it
altered 20% of endings, and in 20 of 20 at 40%, with no false alarms in 20 null
trials. So a first-glyph line indicator that changes a fifth or more of the word
endings in its line would have been seen.

## Result

Excess bits per target word, given page and paragraph-first-line status. The
key at position j predicts the words at positions j+2 to j+5, so the adjacent
word is skipped and the known neighbour coupling cannot contribute.

| Key position | 1 (line start) | 2 | 3 | 4 |
| --- | --- | --- | --- | --- |
| Manuscript B, target's final glyph (primary) | −0.0023 | 0.0085 | −0.0053 | 0.0038 |
| Manuscript B, target's first glyph | −0.0000 | −0.0033 | −0.0047 | 0.0111 |
| Manuscript B, whole word | 0.0001 | −0.0071 | 0.0060 | 0.0037 |

| Data | Contrast D | 95% interval (page bootstrap) | Folio halves | Rule fires |
| --- | --- | --- | --- | --- |
| Manuscript B, primary | −0.0046 | −0.0187 to 0.0110 | −0.0002, −0.0085 | no |
| Manuscript B, first glyph | −0.0011 | −0.0182 to 0.0138 | −0.0036, 0.0011 | no |
| Manuscript B, whole word | −0.0008 | −0.0128 to 0.0108 | −0.0142, 0.0109 | no |
| Shuffled keys (control) | −0.0089 | −0.0212 to 0.0048 | 0.0012, −0.0177 | no |
| Herbal A development (89 lines; low power) | −0.0155 | −0.0434 to 0.0124 | −0.0021, −0.0305 | no |
| R2, coupling off (6 seeds) | −0.0035 to 0.0075 | | | 0/6 |
| R2, coupling on (6 seeds) | −0.0172 to 0.0100 | | | 0/6 |

The manuscript is indistinguishable from its own shuffled-key control.

## Calibration

| Share of endings altered by the planted indicator (q) | 0 | 0.05 | 0.10 | 0.20 | 0.40 |
| --- | --- | --- | --- | --- | --- |
| Rule fired, of 20 | 0 | 0 | 0 | 16 | 20 |
| Median D | −0.003 | −0.001 | 0.004 | 0.022 | 0.073 |

Gate passed (at most 2/20 at q = 0, at least 16/20 at q = 0.4). The smallest
effect reliably detected is q = 0.2. Effects at 5–10% are **not** excluded.

## A second observation (descriptive)

No key position predicts endings two or more words away: all twelve excess
values lie within ±0.012 bits. Once the page is known, a word's first glyph
tells you nothing about the endings of non-adjacent words in its line. Lines
are not internally homogeneous in this respect, so "each line uses its own
table" is not supported for word endings whatever marks the table. Line-edge
effects reported earlier concern which glyphs appear *at* line starts and ends,
not a dependence running through the line.

## What this does and does not say

* It bounds one mechanism: a first-glyph indicator at line start acting on word
  endings within the line, in Currier B paragraph text.
* It does not test indicators at paragraph or page level, an indicator carried
  by a whole first word or by line-final glyphs, or effects on parts of words
  other than the tested features. The first-glyph and whole-word secondaries are
  null but were not separately calibrated.
* Herbal A has too few qualifying lines to say anything.
* R2 also shows nothing, so this result does not separate a cipher from
  message-free text. It removes one cipher design from consideration.

For the ledger: rows 14 and 16 stay open, with line-level table switching by a
first-glyph indicator now bounded. The open question "do line effects come from
the cipher?" gains this constraint: whatever makes line edges special does not
propagate through the line.

## Verification

`python -m voynich.laboratory.line_indicator_verify` checks source hashes, then
reruns the whole stage, including the 100 calibration runs, and requires
identical `evidence.json` and `calibration.json`. Unit tests cover the skipped
adjacent word, null and planted behaviour, and the shuffle control. Pages in the
sealed confirmation sets were excluded by rule. Deviations: none.
