# Voynich: are n/l/r endings added markers?

Stage 37, 10 October 2026. [Frozen protocol](../../docs/protocols/ENDING_MARKERS_2026-10-10.md),
committed at b085c3c before execution. Evidence label: **not marker-like in
Currier B, by a calibrated two-part rule**. The idea and the dictionary check
are the user's. No readings; this cannot show whether the text has meaning.

**In one paragraph.** If a final n, l or r were a signal added to a complete
word (as if "now" were sometimes written "noww"), then removing it should
usually leave a word that is common in its own right. In Currier B it does
not. Only 19% of n/l/r-final words leave a common word, against 29% for other
endings, and 59% leave something that never occurs as a word. So as a group
these endings are not detachable additions. The three endings differ sharply,
though. `n` is never detachable. `l` is the most detachable of all major
endings (70% leave an attested word). Where a stem does occur both with and
without an ending, which form appears depends on the next word, as the known
neighbour coupling implies. Currier A behaves differently and passes both
parts of the rule; so does the message-free copy generator.

## The rule and its calibration

Marker-like means both: (M1) removing the ending leaves a common word (five or
more occurrences) more often than removing other endings does, with the page-
bootstrap interval excluding zero; and (M2) for stems seen both bare and marked,
the form depends on the next word's first glyph (p < 0.0125).

| Planted on shuffled Currier B text (10 runs each) | Rule fired | M1 difference | M2 p |
| --- | --- | --- | --- |
| True marker (added depending on next word) | 10/10 | about +0.5 | 0.001 |
| Random suffix (added regardless of context) | 0/10 | about +0.5 | 0.16–0.90 |
| Lexical ending (part of the word) | 0/10 | −0.05 to +0.09 | mostly > 0.4 |

Gate passed. The two negatives fail for different reasons, as intended.

## Currier B (21,853 tokens, 4,428 types)

| | n/l/r endings | Other endings | Difference |
| --- | --- | --- | --- |
| Stem occurs as a word at least five times | 19.4% | 29.0% | **−9.6 points** (95% interval −11.4 to −7.7) |
| Stem occurs as a word at all | 40.7% | 55.3% | −14.6 points |

M1 fails, in the wrong direction. M2 is present: 117 stems occur both bare and
marked (5,211 neighbour records), and form depends on the next word's first
glyph by 0.064 bits beyond chance (p = 0.001). The rule does not fire. IT2a
agrees (M1 −10.6 points; M2 0.046 bits, p = 0.001).

Per ending, all with at least 200 tokens:

| Ending | Tokens | Stem attested | Stem common | Types | Types with attested stem |
| --- | --- | --- | --- | --- | --- |
| y | 9,647 | 56% | 29% | 1,746 | 17% |
| n | 3,759 | 8% | 0.03% | 585 | 2% |
| l | 3,007 | **70%** | **39%** | 527 | 22% |
| r | 2,973 | 52% | 24% | 665 | 14% |
| m | 496 | 40% | 14% | 199 | 14% |
| o | 432 | 50% | 28% | 151 | 35% |
| s | 405 | 58% | 33% | 217 | 36% |
| d | 341 | 42% | 26% | 183 | 32% |

Of the 9,739 n/l/r-final tokens, **59.3% have a stem that never occurs as a
word** (1,562 types). The commonest: *aiin* (350), *daiin* (294), *qokain*
(268), *qokaiin* (240), *dain*, *okar*, *otaiin*, *okal*, *ain*, *otain*.
Treating a final `n` together with its preceding run of `i` as one unit lowers
that to 41.6% never attested and raises the common share to 24.9%, still below
the other endings.

## What this means for the idea

* **The simple version fails.** The user's criterion was that a stripped word
  found again and often would be interesting, and many that never show up
  would count against. Most never show up. n/l/r are not, as a group, signals
  appended to otherwise complete words.
* **`n` is not a separable glyph at all.** It lives inside units like *ain* and
  *aiin*. Any model that treats a final `n` on its own is using the wrong unit.
* **`l` is the best candidate for a detachable ending**, more than `y`. 70% of
  l-final tokens leave an attested word. This is a descriptive lead, not a
  tested claim; the protocol tested the group.
* **Context dependence is real but is the coupling already known.** M2 restates
  it for stems with both forms. It adds that the bare form itself takes part.
* **Local glyph statistics explain M1 but not M2.** Text sampled from the
  stage-31 glyph chain gives the same M1 (−12.8 points) and no M2 (p = 0.77).
  So which endings are detachable follows from how words are built; the
  dependence on the next word does not.

## Sensitivities (no separate claims)

| Data | M1 difference | M2 excess, p | Rule |
| --- | --- | --- | --- |
| IT2a, Currier B | −10.6 points | 0.046, 0.001 | no |
| ZL Currier A, non-sealed pages (6,497 tokens) | **+6.6 points** (2.8 to 10.4) | 0.109, 0.001 | **yes** |
| Glyph-chain sample | −12.8 points | −0.002, 0.77 | no |
| R2 copy generator with coupling | +3.2 points (0.6 to 5.9) | 0.046, 0.001 | **yes** |

Two cautions. First, **Currier A passes**: there n/l/r endings leave a common
word more often than other endings do (26.5% against 19.9%). The calibration
was run on B text, A is a smaller sample, and this was a declared sensitivity,
so it needs its own preregistered test before it means anything. It is,
however, a concrete difference between A and B in how endings attach. Second,
**the message-free copy generator also passes**. Its mutation step adds and
drops final glyphs and its coupling option ties endings to the next word. A
marker-like result therefore cannot by itself indicate a cipher.

## Verification

`python -m voynich.laboratory.ending_markers_verify` checks source hashes and
reruns the whole stage, requiring identical outputs. Unit tests cover the
tokeniser, a real drawing gap, the stem counts, and marker versus lexical
behaviour. Sealed confirmation pages were excluded. Deviations: none.
