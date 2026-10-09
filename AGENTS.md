# Working on this repository (agents and humans)

Read this before proposing or running any Voynich study. It records what the
project has already learned the hard way, and the workflow every new stage
follows. The scientific rules live in
[docs/RESEARCH_CONSTITUTION.md](docs/RESEARCH_CONSTITUTION.md); what has been
tested, and with what verdict, lives in
[docs/CANDIDATE_LEDGER.md](docs/CANDIDATE_LEDGER.md).

## Where things stand (9 October 2026)

* **Robust structural findings.** In Currier B, a word's n/l/r ending is
  coupled to the next word's first glyph. That coupling also appears at hidden
  boundaries inside written words, and it holds across three transcriptions.
  It is strongest where spaces are doubtful. A message-free generator also
  produces it, so it is not evidence of meaning by itself.
* **Tested cipher families.** Seven cipher families available around 1420
  (as simulated) and two message-free generators failed the Voynich
  fingerprints. The strongest constraint is page-specific vocabulary: Voynich
  "words" are associated with pages; topic, layout and state can all contribute.
* **Length-preserving decoding is strongly disfavoured relative to the tested
  reference profiles**, not universally excluded. A fixed decoder cannot add
  information. For changing state the same unconditional comparison requires
  plaintext-window independence from state; observable layout alone does not
  establish it. Expansion estimates are heuristics, not minimum code lengths.
* **Not settled:** which larger-unit family (glyph groups, syllables, word
  codes, mixed coding), what the spaces are, and whether a changing table
  explains page-specific vocabulary.

## Latest grouped-unit pilot

See [the grouped/boundary report](results/grouped_boundary_2026-10-09/README.md).
The <=3-prefix, 1/2-glyph model at expansion 1.35–2 has no admissible original
f26r parser under hard line/drawing/omission boundaries. This does not exclude
other grouped models. Its unigram shortlist dropped the true policy in all eight
synthetic cases: do not use that heuristic to justify pruning a cipher family.
No original-page decryption or unchanged-key transfer occurred. Before another
blind grouped search, demonstrate adequate key recovery and justify boundary assumptions.
The [all-survivor repair](results/parser_retention_2026-10-09/README.md) now
selects the true parser in all eight fixtures, but blind recovery is 28.5–75.0%
(0/8 at 90%). This is a key-optimisation limitation under the fixed budget.

## Latest unit/page-association study

[Stage 27 report](results/unit_association_2026-10-09/README.md): 16 distinct
Currier B folios, 64 tokens each, five source texts including Italian recipes.
All-type within-section excess MI is 0.115–0.124 bits across spacing arms;
role-conditioned values are 0.092–0.105. Word shuffles approach zero.
Whole-word profiles sometimes overlap; source choice and joint shape/layout
mismatches matter. Small mixed dictionaries selected by frequency fall short;
content-selected dictionaries remain untested. No decipherment or universal
family exclusion follows.

**Pooling trap:** first-occurrence tie-breaking at a top-200 vocabulary cutoff
can introduce page association among rare types. The post hoc diagnostic gives
0.205 spurious bits even with all-unique tokens. Use all-type measurements or
calibrated position-independent pooling. The historical ZL grid verdicts now
have a [sufficient audit](results/historical_pooling_audit_2026-10-09/README.md):
434/456 cells fail unaffected shape measures, and the remaining 22 fail audited
page MI under both identity ties and no cap (132 reproduced simulations).
This clears the old ZL verdict concern, not every historical capped statistic
or the IT/v101 full grids. Do not overwrite old results.

Next: [recurring-label/crib scope](docs/protocols/CRIB_SCOPE_2026-10-09.md), with
image/label alignment and independent referents before semantic fitting. The
299-label inventory is not 299 plaintext words or verified crib pairs.

## Word-code alternatives follow-up (stage 28)

[Report](results/word_homophones_2026-10-09/README.md): 504 forward panels test
one/two/three disjoint codewords per whole word with fixed IID choice, three
sources and chapter-disjoint validation. Recipe alternatives improve vocabulary
shape, but no development configuration/draw jointly matches shape and page
association within the frozen descriptive scales. This is not a rejection of
word codes, and no plaintext words were recovered. Disjoint page-independent
homophones preserve population word/page MI; finite-sample excess MI changes.

IT2a replicates page association on the original pages (0.123 vs ZL 0.115).
Sixteen additional herbal/starred-text folios give 0.097/0.104 (IT/ZL). The new
section mix is explicit; sources and genre cannot be identified from these fits.
Next compare a bounded context-persistent choice model with IID choices at the
same codebook size/marginal frequencies, or a separately specified content lexicon.

The [label alignment packet](results/label_alignment_2026-10-09/README.md)
contains coordinate candidates for 53 occurrences of 22 recurring label types.
Only four types cross the original folio split; its five-type semantic-test gate
fails. Do not lower the threshold or change the split after seeing this count.
Exact coordinate spelling matches are not confirmed image/label alignments.

## Stage 29: frequency decomposition and Currier A

[Stage 29](results/frequency_currier_a_2026-10-09/README.md) finds positive page
association in matched herbal A and B panels and both disjoint eight-folio
halves, across ZL/IT and spacing arms. A is weaker in these samples. Most B
association comes from types occurring at least five times, not the 2–4 group.
Frequency groups are not semantic classes; singleton zero reflects the estimator.
Before a page-persistent word-code test, follow the
[slot/state/R2 guardrails](docs/guides/CONTEXT_CODEBOOK_GUARDRAILS.md): charge
codebook and state, model glyph structure, compare R2 on frozen pages. R2 can
also be order-sensitive; known-key round trips do not distinguish meaning.
Large (1,500–4,500-entry) codebooks around 1420 remain historically unverified.
No new cipher fit or decipherment was established by this diagnostic.

## Stage 30: structured word codes versus R2

[Stage 30](results/structured_word_codes_2026-10-09/README.md) tested a bounded
first-glyph/middle/final-glyph construction with four two-variant policies and
same-training R2 controls. All 168 panels replay; 16/16 synthetic profile targets
pass calibration. Neither selected family fits the joint reserved-page profile.
Persistence can raise page association, but glyph entropy remains too high.
The fitted grammar covers only 54.9% of reserved B tokens despite 14,336 unique
outputs. This is a narrow representational failure, not exclusion of word codes.
Next examine dependencies between codeword parts and unseen-type coverage;
do not merely retune persistence or increase seeds in this grammar. Known-key
round trips and shuffle sensitivity still do not establish manuscript meaning.

## Stage 31: scribe control, dependent word shapes, codebooks

[Stage 31](results/word_shapes_2026-10-09/README.md) (protocol committed first).
**Scribe:** within Davis hands (ZL `$H`), 16-folio B keeps 71% of its page
association (0.096 of 0.135 bits). That is below all twelve plaintext
references (77–103%), so part of the target is scribal. Score models against
both values; A (one hand) keeps 0.078. **Shapes:** an order-2 glyph chain with
start/end symbols matches glyph entropy, the nearly fixed last glyph and length.
Its 2,968 most probable strings cover 83% of reserved B tokens. Do not build
more independent-slot grammars. **Codebook:** with random assignment it still
fails. Codewords are too long (common Voynich words are short; random
assignment ignores that), and neighbour coupling is zero, as predicted. R2 also
fails. Next: frequency-ranked assignment and context-conditioned variant choice,
each preregistered separately. Stolfi/Zattera baselines remain deferred.

## Stage 32: frequency-ranked assignment

[Stage 32](results/ranked_assignment_2026-10-09/README.md): giving common plaintext
words the most probable codewords fixes length (4.41 vs 4.34–4.52) and the
negative frequency/length relation; page association is unchanged by
construction. Coupling (0 vs 0.12–0.25) is now B's only binding failure. A
marginal, unreplicated 4/12 neighbourhood result on Currier A is not a fit.

## Stage 33: context-conditioned variant choice

[Stage 33](results/context_choice_2026-10-09/README.md): choosing the alternative
whose ending suits the next word raises coupling to 0.09–0.10 bits (B:
0.12–0.25). This is the closest development fit yet (max residual 1.16), but no
joint hits. Page-persistent choice restores page association and destroys
coupling; do not try to tune the two against each other in this grammar.

## Mistakes we have already made — do not repeat them

1. **Repeating a weakly supported family.** The three manuscript searches
   improved fitted scores but established no readings. Use
   `uv run --locked python -m voynich.evaluation.capacity --sensitivity`
   to assess reference-profile gaps before another search. This sets priorities;
   it is not a mandatory rejection rule. State the sampling, language and state
   assumptions. Prefer a different representational hypothesis now.
2. **Treating a better score as progress.** Any flexible decoder makes text
   more "Latin-like" under the model it is optimised against. A medical word
   such as `febris` turning up proves nothing.
   * Evidence needs all of: matched controls that get the same freedom and
     budget (symbol shuffle, **whole-word shuffle**, and layout controls that
     keep paragraph and line roles); unchanged-key transfer to other pages;
     mappings that are stable across seeds; and readings checkable
     independently of the scorer.
   * Use the constitution's evidence labels. Only "Decipherment supported"
     means decipherment.
3. **Escalating instead of rethinking.** More budget, more tables, more seeds
   or a new initializer for the same family is not a new hypothesis. If a
   family gives no manuscript evidence, the next step is to revisit glyphs,
   spaces, units, language or content, not to spend more on it. Every stage
   must name the [ledger](docs/CANDIDATE_LEDGER.md) entry it is meant to move.
4. **Calibrating on the wrong kind of synthetic text.** Recovering ciphers
   built from Latin with a Latin-sized alphabet says little about Voynich.
   Synthetic fixtures for a manuscript claim should match the Voynich
   conditions that matter: the ciphertext's own entropy, explicit glyph expansion
   per letter, page-specific vocabulary, uncertain spaces, and unclean tokens.
   Synthetic accuracy is reported separately from manuscript evidence.
5. **Trusting paired per-row comparisons between model representations.**
   Refitting a model after changing a few rows shifts predictions for
   thousands of unchanged rows. Split paired differences into changed and
   unchanged rows, and check a relabelling noise floor
   ([V101 follow-up findings](docs/reports/V101_FOLLOWUP_FINDINGS_2026-09-26.md)).
6. **Treating spaces as given.** Transcriptions disagree mainly about doubtful
   spaces, and the coupling is about six times stronger there. Spacing is a
   model variable, so state your spacing assumption.
7. **Losing code in a merge.** The October layout migration silently dropped
   the code behind the v101 and cipher-family results; it was restored on
   9 October. Every `results/` directory must have its producing code in
   `src/voynich/`. After any merge, run the full test suite and
   `uv run voynich list`.

## Approved workflow for a new stage

1. **Choose a candidate** from the ledger or
   [operation priorities](docs/OPERATION_FAMILY_PRIORITIES.md) with a clearly stated
   domain. Write down the result that would move it to "compatible" and the
   result that would reject it.
2. **Screen it cheaply.**
   * Capacity: can the family's units carry plaintext-level information?
   * Fingerprints from `voynich.cipher_families`: page-specific vocabulary,
     vocabulary size, top-word share, repetition, line effects. Can some
     setting of the family come close?

   Record mismatches and their scope; do not convert reference gaps or failed
   optimisation into a universal exclusion.
3. **Calibrate.** Build synthetic ciphertext of that family under
   Voynich-like conditions, and show the solver recovers it blind, with known
   keys held back. A method that cannot recover its own family cannot test it.
4. **Write a protocol** in `docs/protocols/` with fixed rules: data,
   pages, controls, budget (including initialisation), and decision rules.
   Commit it **before** running.
5. **Run on the manuscript.** Use bounded pages, matched controls,
   unchanged-key transfer, and several seeds reported separately.
6. **Report** in `docs/reports/` (or a results README) with an evidence
   label, deviations and post hoc analyses marked, then **update the ledger**.

## Recommended next studies (in order)

1. **Word/content units and independent label predictions.** Stage 27 completed
   the first bounded unit comparison. Align recurring zodiac labels to images,
   test observable referents with reserved folios, and define content-selected
   dictionaries. Preserve source/genre dependence and the pooling correction.
   A free codebook cannot predict unseen entries from a handful of cribs.
2. **Grouped-glyph and verbose decoding with the existing solver.** Use the
   `groups`/`mixed` families and inferred spaces, with a declared expansion range
   appropriate to the particular encoding. Calibrate first on Naibbe-type and grouped
   fixtures with a Voynich-sized alphabet.
3. **Word and mixed codes** (letters plus a bounded word-code list), which can
   keep page-specific vocabulary.
4. **Drifting or section-specific tables** for verbose codes: one possible source of
   page-specific vocabulary.

Stop working on: further budget, tables or initialisers for
one-glyph-to-one-letter decoding with spaces kept.

## Practicalities

* Setup: `uv sync --locked`. Tests:
  `uv run --locked python -m unittest discover -s tests -t . -v`. PostgreSQL
  tests skip unless `POSTGRES_TEST_URL` is set; CI runs them.
* **Numbered stages** are `src/voynich/experiments/eNN_*.py`, listed by
  `uv run voynich list`. Post hoc companions are
  `src/voynich/experiments/posthoc_eNN_*.py`, run with
  `python -m voynich.experiments.<name>`. Modules must be import-safe: do the
  work in `main()`.
* **Never overwrite historical results.** Use a new dated directory. To rerun
  an old stage, run it in a full copy of the checkout
  (`git archive HEAD | tar -x -C <dir>`), then compare with
  `scripts/compare_results.py NEW OLD`. Large run archives stay in the ignored
  `results/runs/`.
* **Docs:** protocols in `docs/protocols/`, findings in `docs/reports/`,
  current guides in `docs/guides/`. Historical documents keep their original
  wording and paths; add corrections as dated notes.
* **Network:** only some hosts are reachable from cloud sessions (raw GitHub
  files work; Gutenberg and The Latin Library did not). Record provenance
  under `data/` for every new source.
