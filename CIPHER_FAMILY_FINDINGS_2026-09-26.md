# Which kinds of cipher could have produced the Voynich text? — findings

26 September 2026. Protocol: `CIPHER_FAMILY_PROTOCOL.md` (commit `968655a`,
written before any code or computation). Results are in
`results/cipher_families_2026-09-26/`. Code: `code/cipher_families.py`,
`code/24_cipher_family_benchmark.py`, `code/25_homophone_recovery.py`.

## Summary

* **No tested family survives.** None of the seven cipher families available
  around 1420 (plain/simple substitution, homophonic, nomenclator,
  abbreviation, and three verbose ciphers), and neither message-free reference
  (assembly, copy-and-modify), reproduces the Voynich fingerprints.
* **The exclusions are robust.** They hold in both Currier B windows and in all
  three transcriptions (ZL3b, IT2a, v101). The self-consistency gate passed at
  100% for every family, so the rule is not simply too strict: a family's own
  held-out runs are always recognised.
* **Three properties do the excluding**, and they are the useful result:
  1. **Page-specific vocabulary.** Voynich pages have much more page-specific
     vocabulary than any cipher. Verbose "word = letter" ciphers
     (Naibbe-type) fail worst, because letters don't change with topic. Plain
     language gets closest, but only about half-way with our plaintexts.
  2. **Vocabulary shape.** Voynich has *fewer* distinct words and more
     dominant frequent words than homophonic ciphers or plain Latin, yet more
     than a syllabic code.
  3. **Line-start and line-end effects.** No family produces them unaided. A
     simple scribal layout convention (line-initial and line-final signs) brings
     every family to Voynich's level.
* **Step B, homophone recovery:** not applied to Voynich, because no homophonic
  family survived. Calibration shows recovery depends strongly on cipher
  design: syllabic-slot homophones are trivially recoverable (AUC 0.9997), and
  Naibbe-table homophones are not (AUC 0.81, gate failed).
* **Main limitation.** Our plaintexts are tales and poetry. A herbal or recipe
  book changes topic on almost every page, so the page-specificity test is
  harsher on plain language and word-level codes than a matching plaintext
  would be. It is *not* harsher on letter-level ciphers, which wash topic out
  regardless (see below).

## Setup

* **Targets.** Currier B paragraph text of ZL3b, split into two windows of
  whole pages in file order:
  * **W1:** 32 pages, 5,122 slots: the Currier B herbal pages plus the start
    of the biological ("bathing") section and some text-only pages;
  * **W2:** 18 pages, 5,454 slots: the rest of the biological section, with a
    few text-only and cosmological pages.

  The stars and recipe pages (f103 onwards) fell outside both windows and
  were used only for training the Voynich-trained generator parts.

  IT2a and v101 on the same pages are secondary targets. Voynich-trained parts
  of the generators used Currier B pages outside both windows.
* **Grid.** 114 configurations × 2 layout conditions (L0 none, L1 scribal
  line and paragraph signs) × 6 seeds, plus 2 held-out seeds per
  configuration, run on both windows: 3,648 runs. Every configuration could be
  filled from its plaintext; none was skipped.
* **Rule.** A configuration is compatible if all nine token-level
  fingerprints are within |z| ≤ 3. The z uses the configuration's seed SD plus
  the Voynich page-bootstrap SD. A family is compatible if any configuration
  is.

## Step A results

### Verdicts

| Family | ZL3b W1 | ZL3b W2 | IT2a, v101 | Least-bad max |z| (W1 / W2) | Binding fingerprints, least-bad configuration (W1; W2) |
|---|---|---|---|---|---|
| F1 plain / simple substitution | excluded | excluded | excluded | 6.6 / 4.3 | vocab. size, top-10 share, repeats, line-start; repeats, page-specificity |
| F2 homophonic | excluded | excluded | excluded | 10.7 / 15.7 | vocab. size, top-10, page-specificity, line effects |
| F3 nomenclator | excluded | excluded | excluded | 6.6 / 4.4 | vocab. size, top-10, repeats, page-specificity, line effects |
| F4 abbreviation | excluded | excluded | excluded | 7.3 / 4.2 | vocab. size, top-10, repeats, page-specificity |
| F5 verbose (Naibbe tables) | excluded | excluded | excluded | 6.4 / 6.4 | **page-specificity**, vocab. size, repeats (+ top-10, line effects in W2) |
| F6 verbose syllabic | excluded | excluded | excluded | 4.8 / 4.2 | **page-specificity**, repeats; top-10 |
| F7 verbose + nulls | excluded | excluded | excluded | 6.4 / 6.5 | **page-specificity** (+ vocab. size, top-10, line effects in W2) |
| R1 assembly (no message) | excluded | excluded | excluded | 6.5 / 6.8 | page-specificity, top-10, line effects |
| R2 copy-and-modify (no message) | excluded | excluded | excluded | 7.4 / 10.0 | vocab. size, top-10, line effects |

**Gate G1** (self-consistency) passed for all nine families: 100% of held-out
runs were compatible with their own family. **G2** (discrimination) flags
these confusable pairs, whose verdicts do not separate them: plain vs
abbreviation, nomenclator vs abbreviation, Naibbe vs nulls, Naibbe vs
assembly, nulls vs assembly.

### Where Voynich sits (ranges of configuration means, W1)

| Fingerprint | Voynich W1 (W2) | Plain (F1, L0) | Homophonic (F2) | Naibbe (F5) | Syllabic (F6) | Copy (R2) |
|---|---|---|---|---|---|---|
| P1 types/tokens | 0.30 (0.25) | 0.22–0.46 | 0.54–0.93 | 0.23–0.49 | 0.14–0.32 | 0.20–0.49 |
| P3 top-10 share | 0.17 (0.22) | 0.13–0.23 | 0.02–0.10 | 0.09–0.31 | 0.06–0.26 | 0.07–0.12 |
| P4 adjacent repeats | +0.002 (−0.002) | −0.009 to −0.005 | −0.002 to 0.000 | −0.008 to −0.001 | −0.006 to +0.018 | 0.000 to +0.19 |
| **P6 page-specificity** | **0.21 (0.19)** | 0.06–0.12 | 0.00–0.03 | **0.00–0.01** | 0.01–0.07 | 0.25–1.57 |
| P7 line-start, no layout rule | 0.070 (0.073) | ≈ 0 | ≈ 0 | ≈ 0 | ≈ 0 | ≈ 0 |
| P7 line-start, with layout rule L1 | | 0.02–0.05 | 0.00–0.02 | 0.02–0.08 | 0.01–0.06 | 0.01–0.02 |

### Reading

**1. Page-specific vocabulary is the strongest constraint, and it counts
against letter-level verbose ciphers.** Voynich word types are strongly tied to
particular pages (P6 ≈ 0.2 bits). In a verbose cipher where each "word" is a
letter or letter pair, word choice cannot follow topic, because letters don't.
Naibbe-type text shows essentially no page-specificity (≤ 0.013), whatever
plaintext goes in. The same holds for the null-padded version and the
homophonic cipher. This is the clearest "rule out" in the study: **the Voynich
tokens behave like units that carry topic, like words or word-codes, not like
spelled-out letters**, at least for ciphers of this design.

Only two things reach Voynich's level:
* plain language, which gets about half-way with our tales and poetry;
* copy-and-modify text, which overshoots at most settings, because copying
  nearby words makes vocabulary cluster by page. It then fails on vocabulary
  size and line effects.

**2. Vocabulary shape sits between language and code.** Voynich has fewer
distinct word types than plain Latin at the same length, and its 10 most
common words take a larger share. Homophonic ciphers go the wrong way, with far
too many types. Syllabic codes overshoot in the other direction. Voynich also
has slightly *more* exact adjacent repetition than chance in W1, which natural
languages avoid (they come out negative).

**3. Line and paragraph effects look like a writing convention, not the
cipher.** No family produces them unaided, and a simple "mark the first and
last word of a line" rule brings every family into range. So the line effects
don't discriminate between families. They say that whatever produced the text
also followed a layout convention, like the capitals and line-fillers of
ordinary manuscripts.

**4. The message-free references fail too.** Assembly lacks
page-specificity; copy-and-modify has too much of it at most settings and
fails on vocabulary and line effects. So this benchmark does not show the text
is meaningless either.

## Step B results (calibration only)

No homophonic family survived step A, so, as pre-set, step B ran calibration
for F5 and F6 only and was **not applied to Voynich**.

| Family | Held-out evaluation | ROC-AUC | Precision at p ≥ 0.8 | Gate H1 |
|---|---|---|---|---|
| F6 syllabic | held-out seed | 0.9997 | 0.98 | pass |
| F6 syllabic | Latin → German | 0.9995 | 0.99 | pass |
| F6 syllabic | German → Latin | 0.9997 | 0.96 | pass |
| F5 Naibbe | held-out seed (Latin only) | **0.81** | 0.95 (100 pairs) | **fail** |

* F6 homophones share a visible core string, so a classifier finds them
  almost perfectly. If Voynich were this kind of cipher, its homophones would
  be easy to spot. That is consistent with F6 failing step A.
* F5 (Naibbe-table) homophones are much harder to recover from ciphertext
  alone. Its held-out-language test could not run: Italian and German are too
  short to fill a 10,000-token verbose layout without wrapping. That is a
  deviation in coverage, not in rules.

## What this means for "which cipher?"

* **Not supported:** a letter-by-letter verbose cipher of the Naibbe kind, with
  fixed tables, applied to ordinary prose. It cannot reproduce Voynich's
  page-bound vocabulary.
* **Also not supported:** simple or homophonic substitution of Latin, Italian or
  German, and scribal abbreviation. Their vocabulary shape and repetition are
  wrong, and homophonic substitution also lacks page-specificity.
* **Pointed to, not established:** something whose tokens carry *word-level*
  content (so vocabulary follows topic) but with a smaller, more repetitive
  vocabulary than natural Latin, written with a line-layout convention. Three
  candidates fit that description and were not tested here:
  * a **word-level code** or large nomenclator;
  * a **language with a small, repetitive vocabulary** (for example formulaic
    recipe or herbal writing);
  * **self-citation copying of topical text**, which would be meaningful and
    copy-like at once.

## Limitations

* **Plaintext genre.** Our texts (Alfonsi's tales, Dante, a Middle High German
  text) are not page-topical. A herbal with a plant per page would raise
  page-specificity for plain language, nomenclators and abbreviation, perhaps
  enough to reach Voynich. It would not rescue letter-level verbose ciphers,
  whose tokens don't carry topic. Only raw GitHub files were reachable from
  this environment, so no medieval herbal plaintext could be fetched.
* **Exclusions hold only for the grid tested.** For example:
  * a verbose cipher whose table preferences drift by page or session could
    create page-specificity without word content;
  * a nomenclator covering most of the vocabulary is outside the grid
    (N ≤ 300).
* **5,000-token windows** limit precision. W1 is mostly herbal and W2 mostly
  biological; P4 changes sign between them. The stars and recipe section was
  not a target.
* **The fingerprints are token-level by design.** Glyph-level secondary
  fingerprints are saved but carried no vote.

## Suggested next tests

1. **Page-topical plaintext.** Obtain a medieval Latin herbal or recipe text,
   run F1/F3/F4 again, and see whether page-specificity reaches Voynich's
   level.
2. **Drifting-table verbose cipher**, where table preferences change by page
   or scribe. This is the one way a letter-level cipher could fake page-bound
   vocabulary.
3. **Whole-word codebook**: a nomenclator with most words coded, and
   homophones built from shared parts.

## Deviations

* **Smoke test.** Before the full grid, a smoke test printed ZL3b W1's
  fingerprints and a handful of simulations to check that the code worked. The
  rules were already committed and were not changed.
* **Step B coverage.** For F5, only Latin could fill the 10,000-token layout,
  so there was no held-out-language evaluation.
* **Unit counts.** Simulated F5–F7, R1 and R2 tokens are EVA strings and were
  counted in EVA glyphs; F1–F4 tokens were counted in characters. Only the
  secondary fingerprints use units.
