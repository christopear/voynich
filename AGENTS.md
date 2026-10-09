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

1. **The constitution's first study** (§7): which unit size (letters, pairs,
   syllables, words, mixed) can carry Voynich's page-specific vocabulary,
   using the data-processing bound and matched layouts.
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
