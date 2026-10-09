# Scope for a falsifiable label/crib test — 9 October 2026

**Design scope only. No semantic assignment or decryption has been tested.**
A final protocol must freeze verified image/label alignments, lexical alternatives,
model complexity, budget and predictions before a crib search. Ledger row 13.

## What is actually available

The ZL3b `Lz` records provide **299 zodiac-section labels on 12 panels**, of which
271 have clean readings under our existing parser. Twenty-two clean whole-label
spellings occur on more than one panel. This is a transcription inventory, not
299 known words. Some labels have multiple tokens, doubtful spaces or uncertain
glyphs; store the entire label and its boundary annotations. The producer is
`voynich.laboratory.crib_inventory`; raw inventory and repeats are in
`results/crib_scope_2026-10-09/inventory.json`.

I visually inspected Yale viewer image 127 (the fish diagram, corresponding to
f70v2) and image 129 (f71r), using the [primary facsimile](https://collections.library.yale.edu/catalog/2002046).
Both show a central animal image and numerous surrounding human/star figures with
short inscriptions, as well as circular text. The central image, marginal Latin-
alphabet annotation and surrounding labels are different possible referents.
This does **not** justify assigning the central sign's name to every surrounding
label. This inspection verified overall layout, not every glyph/figure alignment.
The inventory explicitly leaves detailed facsimile alignment unverified.

Do not treat Roman-letter month annotations as established plaintext/ciphertext
pairs, as necessarily Latin rather than vernacular, or as contemporaneous with
the cipher hand. Their writing layer, reading and intended referent need separate
assessment. Date of parchment alone cannot establish annotation date.

Zodiac records do not carry the same Currier B classification as the paragraph
sample in experiment 27. This is a new domain, not unchanged-key transfer from
that sample. Conclusions cannot be silently pooled across them.

## First bounded test: recurrence before translation

Use folios 70–71 for development and folios 72–73 for reserved semantic
predictions. These are two folio groups, not twelve independent page samples;
all panels were inventoried, so the reservation is prospective for semantic
fitting only. Reserve the complete folded folio, not alternating adjacent panels.

1. Align the 22 cross-panel recurring label types to image regions, recording
   coordinates, complete transcription alternatives and uncertain attachment.
   Have image categories assigned without seeing proposed plaintext. Start with
   observable features (central versus peripheral, star held/not held, container,
   clothing and relative position), not invented plant/species identifications.
2. Compare explicit referent hypotheses: object/class name, person or star name,
   ordinal/calendar position, and no shared illustrated referent. No assertion
   that any is true. Different pictures do not refute a word code if its labels
   describe attributes, actions, dates or names we cannot identify.
3. Freeze at most eight development anchor types and at most three documented
   Latin/Italian lexical alternatives per type. Only include anchors independently
   supported by the illustration or an external contemporaneous source. If eight
   defensible anchors cannot be found, stop at a nonsemantic recurrence test;
   do not fill the list with speculative words. Freeze spelling and inflection
   alternatives before fitting. The current inventory does NOT supply eight
   validated semantic anchors.
4. Primary cheap test: does an unchanged label-to-category association learned on
   development predict the annotated reserved figures? Require at least five
   recurring anchor types crossing the split, otherwise report insufficient
   identifiability. Use whole-label assignment permutations within panel and
   radial role, with the same alternative-selection procedure applied to every
   control (999 permutations, three declared seeds). Count types/folios as
   dependent clusters; no token-level pseudoreplication.

This tests a very narrow label-as-illustrated-category model. A negative result
would not refute nomenclators or unknown star/person/calendar names. A positive
result is a crib candidate, not a reading of the running text.

## What could make a codebook decipherable

An arbitrary word-to-codeword table has no predictive rule for an unseen entry.
Eight cribs recover at most eight entries; naming more fitted labels is not
independent validation. Exact recurrence is useful but alone only propagates an
assumed meaning. We need either independent predictions of those entries'
referents, or a bounded compositional rule that predicts new codewords.

After defensible anchors exist, compare a fixed whole-word mapping with one
explicit compositional model (shared syllabic/affix parts), plus a bounded mixed
word/letter model. Charge dictionary entries, exceptions and alternative choices.
Calibrate on fixtures with the observed sparse recurrence and uncertain label
attachments before searching. Reserve entire lexical types and folios; record
predictions before revealing independent annotations. No Latin-likeness score can
validate its own trained guesses. No per-page key changes may be added after a
failure without a new protocol.

## Recommendation for the next actual study

Complete image/label alignment and test the recurrence model before launching a
large crib search. In parallel with this future stage's design, define a small
medicinal-content dictionary rather than the top-frequency function-word lists
that failed to retain much association in experiment 27. Compare content-selected
word codes, whole-word codes and syllable codes jointly on association, vocabulary
shape and layout; every output codeword must remain recoverable. Do not spend
another round increasing the grouped letter solver's budget.
