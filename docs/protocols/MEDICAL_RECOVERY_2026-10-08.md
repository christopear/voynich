# Medical recovery diagnosis and search comparison

Status: frozen exploratory screen before execution, 8 October 2026.
Plan: `configs/benchmarks/medical-recovery-2026-10-08.json`.

## Purpose and connection to Voynich

Working hypothesis: a manually enciphered medicinal manuscript around the
fifteenth century, with Latin or Italian source language. This study improves
our ability to recognize recoverable instances of that hypothesis. It does not
assume the hypothesis is established, nor fit any Voynich ciphertext.

Previous work established exact known-key reversibility, but arbitrary key
recovery was uneven. The next useful distinction is between an inadequate
objective, an inadequate search, an unreachable representation, and incomplete
coverage on reserved text. Medical vocabulary and independent authors matter
more here than additional demonstrations on literary texts from the same work.

## Sources

Use pinned Perseus Celsus *De Medicina* (Spencer edition) and Pliny *Naturalis
Historia* books 20–27 (Mayhoff edition). These are ancient Latin medical/herbal
calibration texts, not transcriptions of fifteenth-century recipes. Their edition
and digital-text noise are limitations. Provenance and CC BY-SA attribution are
retained in `data/laboratory_sources/`. The explicit extraction command removes
editorial notes/headings, gaps and foreign-language spans before normalization.

Train on 60,000 prepared characters starting 30% into the other author's source.
Development starts 65% into the target; reserved text starts 85% into the target.
Each is 600 prepared characters, trimmed at the edges. The second seed uses a
passage 1,500 characters later. No target-author passage enters model training.
These are two authors with two paired passage/key instances each, not four
independent historical sources. Key and passage effects cannot be separated.

## Representation and algorithms

The emission inventory is explicit: 26 letters, plus eight frequent pairs from
the training author for grouped families. This is deliberately easier than an
unknown historical inventory; no true target units are used to select it.
Word spaces are preserved in this increment. Exact lower-case normalized text
is the recovery target; punctuation and original orthography are not restored.

1. Glyph substitution: one code per unit; known one-character codes.
2. Homophonic substitution: up to two codes per letter, with two in generation.
3. Fixed groups: two-character codes; letter/pair emissions; at most one code
   per unit. Group boundaries follow the known width, not oracle alignment.
4. Variable groups: the first cipher character determines length one or two;
   search infers this prefix policy as well as mappings. Generation uses one
   code per unit, but search permits up to two. This is a declared superset that
   permits a character-wise initialization; it is not a fair isolation of
   segmentation cost alone. It does not cover every variable-length codebook.

The new candidate contains exactly its active code inventory. Group codes need
no single-character fallback. This removes the previous representational defect
within the declared family. Invalid segmentations, inventory/capacity failures
and word-boundary violations consume evaluations and are counted explicitly.

Compare annealing and a diversity-filtered beam over **complete keys/prefix
policies**, using eight initial states, identical initial candidates/mutation
rules, and 8,000 scored candidates each. The beam keeps its best candidate and
prefers candidates differing in at least two assignments before filling remaining
slots by score. This is an initial bounded beam design, not a claim to optimal
beam search. Neither method receives private fixture truth. Both use character
4-gram cost plus code-choice, codebook and (where applicable) prefix-policy costs.
These are description-length surrogates, not calibrated posterior probabilities.

Two authors × two passage/key instances × four families × two algorithms ×
positive/shuffled = 64 searches, 512,000 scored candidates maximum.

## Diagnostics and gates

Shuffle whole cipher codes among equal-length slots, preserving code counts,
character counts and word-space positions. Generator alignment constructs the
control but is never given to the optimizer. There is only one negative-control
type in this screen, so its gate is not interchangeable with the earlier
three-control benchmark gate.

After **both algorithms and their controls finish** for a case:

- Score the active true key with exactly the same objective. Assert it yields
  the true development plaintext and is valid under the new representation.
- If development accuracy is below 95% and truth scores better, label a
  demonstrated search gap. If a found wrong answer scores at least as well,
  label an objective failure/tie for that case. Both problems can coexist;
  this comparison does not certify a global optimum.
- Report normalized edit and non-space edit accuracy, code-boundary F1,
  invalid counts and selected-vs-truth cost gap.
- Freeze the selected key/prefix policy. Decode reserved text with `?` for
  unknown codes; report code-token and cipher-character coverage separately
  from whole-text accuracy. Do not infer missing mappings from reserved text.
- Screening pass requires ≥95% development non-space accuracy, ≥90% reserved
  non-space accuracy, complete reserved-code coverage and lower cost than the
  matched shuffled control. Partial successes remain visible.
- Compare truth-text per-character n-gram costs under the independent medical
  author and existing Alfonsi prose as a post-search domain diagnostic only.
  This does not select the search model retrospectively.

The earlier 32 cases receive a separately labelled post-search oracle audit;
original outcomes and labels remain unchanged. Active and full true codebooks
have different complexity/choice costs, so both are retained in that audit.

## Stopping/review

Complete the fixed screen without tuning on its results. Do not enlarge beam
widths, change temperatures or swap objectives to rescue individual cases.
If objective failure or variable-boundary search dominates, stop at a reviewable
report recommending the next specific intervention. If recovery is broad and
stable, the next independently frozen study should add medieval recipe sources,
spacing uncertainty and transcription-aware Voynich tests, with further negative
controls. Synthetic recovery alone never establishes a manuscript reading.
