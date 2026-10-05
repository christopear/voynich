# Decipherment search framework

Implemented 30 September 2026. This is an engineering framework and calibration
pilot, not a preregistered Voynich decipherment experiment. It follows the
[research constitution](RESEARCH_CONSTITUTION.md) and
[operation catalogue](OPERATION_FAMILY_PRIORITIES.md).

## Implemented

- Interpolated character n-gram language scoring, orders 1–6, trained from an
  explicitly supplied Latin or Italian source. No external model download.
- Simulated annealing over globally consistent code assignments, with swaps,
  reassignment, and bounded addition/deletion of multi-character cipher codes.
- Multiple deterministic restarts, optionally in separate worker processes.
- Beam search over ambiguous variable-length cipher-code boundaries.
- Preserved input spaces, or an experimental inferred-space arm where the key
  must emit the plaintext spaces. No free dictionary word insertion.
- Three model families: `glyph`, `groups`, `mixed` (definitions below).
- Explicit paths consuming every input symbol, key dictionaries, language costs,
  encoding-choice costs, complexity costs and optimization traces.
- Frozen-key evaluation of a separate passage. Unknown symbols cause an explicit
  failure, never a silently fitted new assignment.
- Known-key synthetic fixtures plus equally budgeted shuffled, message-free
  assembly and deliberately mismatched cipher controls.
- JSON results, input/code hashes, settings, seeds, Python/git provenance and
  atomic checkpoints after completed restarts.

The implementation uses only the Python standard library. The existing uv
environment works without dependency changes.

## Model definitions and scope

| CLI family | Cipher codes | Plaintext emissions |
|---|---|---|
| `glyph` | One input character | One Latin-alphabet character; space additionally allowed in infer mode |
| `groups` | Single characters plus a bounded inventory of recurrent strings | Letters plus frequent letter pairs selected from LM training text |
| `mixed` | Same as groups | Additionally a bounded list of frequent training-source whole words |

`glyph` currently means a literal transcription character, **not an inferred
palaeographic glyph**. It does not automatically merge EVA `ch`, `sh` or gallows
sequences. Explicit glyph-unit support is a future extension. The grouped model
can combine characters, but this does not replace a transcription sensitivity
analysis.

Several cipher codes may share one plaintext emission. The reverse mapping is
globally consistent. Singleton codes remain available as a coverage fallback.
Additional codes must recur at least twice in development text and belong to the
bounded frequent-substring inventory. The defaults are not an exhaustive search
of all variable-length codebooks.

Under preserved spacing, codes cannot cross visible spaces. Whole-word emissions
in `mixed` must occupy a complete visible word. Under inferred spacing, input
spaces are removed, whole-word emissions carry explicit surrounding spaces, and
other spaces must be emitted by an assigned code. This is a restricted spacing
model; it is not arbitrary free word segmentation.

No nulls, deleted glyphs, per-occurrence exceptions, changing tables, transposition
decoder or neural language model are implemented yet. These are extension points,
not hidden degrees of freedom in the present search.

## Objective

The minimized exploratory score, in bits, is:

    character-language cost of plaintext
    + uniform homophone-choice cost along the decoding path
    + key_weight * description-length surrogate for the key.

The language model uses recursively smoothed conditional probabilities with
pseudocount strength 5 and a 27-character alphabet. It does not yet model a
complete distribution over plaintext lengths or an end-of-message symbol.

For each emitted unit, the choice term is log2(number of codes in the key that
emit that unit). The key surrogate charges its entry count, cipher-code lengths,
cipher alphabet and the size of the declared plaintext-unit inventory. Empty
emissions are prohibited. Explicit non-space plaintext/ciphertext length-ratio
bounds default to 0.2–3.0.

This is a **best-path search objective**, not a normalized generative likelihood,
Bayes factor, posterior probability or calibrated family-comparison statistic.
It omits marginalization over paths and plaintext-unit segmentation. Raw scores
across different spacing/model/language settings cannot establish which family
is correct. Length bias remains a reason to calibrate each architecture before
using it for inference.

Beam pruning is approximate. Annealing can miss a good key, and increasing the
budget can overfit. A high-scoring reading is only a candidate. Agreement across
restart keys is descriptive stability, not a confidence interval.

## Inputs and normalization

Language training input is UTF-8. Normalization lowercases, expands ae/oe
ligatures, folds combining accents, maps nonletters to spaces and collapses
spaces; i/j and u/v remain distinct. This loses accents and punctuation and is
not a diplomatic transcription. The language flag records the claimed source
language; it does not detect or enforce it.

Cipher input must be a deliberately prepared plain ASCII letter/digit text file.
Case is preserved. Whitespace is collapsed (including line breaks), or removed
in infer mode. IVTFF, uncertainty marks and punctuation are rejected rather than
silently stripped. A future manuscript adapter must preserve provenance and
missingness; do not concatenate clean fragments across damaged material.

For a real manuscript study, document page/locus selection and the conversion to
this representation. Source files in the current project are useful engineering
controls but include narrative/poetic material and transcription artefacts;
they are not the planned genre-matched historical source panel.

## Run synthetic controls

From the repository root:

```bash
uv run --locked python -m voynich.experiments.e26_decipherment_search controls \
  --train data/latin_alfonsi.txt --language latin \
  --family glyph --words 100 --steps 2000 --restarts 4 --workers 2 \
  --output results/my_decipher_run/latin_controls.json
```

By default this runs positive, shuffled, assembly and mismatched controls with
identical search budgets. `--homophones 2` creates two alternatives per unit.
`--replicates N` repeats with different synthetic keys; it does not add independent
source passages. `--control-kinds positive` is useful for an engineering smoke
test, but cannot calibrate false readings.

Controls train the LM on the first 70% of normalized source words. After a
50-word gap, two disjoint passages provide development and evaluation text.
They share a source, so this is within-source transfer, not cross-author or
cross-genre validation. Repeated content elsewhere in the source is not deduplicated.

The synthetic codebook is generated jointly for the two passages, then hidden
from the optimizer. Ground-truth keys and accuracy are attached only after
search. Generated group/mixed fixture codes are fixed-width two-character
strings; more difficult variable-width calibration still needs to be added.
Their plaintext pair/word emissions are restricted to the training-derived
inventory. Nevertheless, the generating key may exceed the configured number
of extra codes or contain codes too rare for the candidate inventory. The
`truth_search_space_check` flags this: such a run exercises the pipeline but
cannot measure recovery power for an in-family key. This distinction is
especially important for the small-budget group/mixed smoke tests.
Known-key decoding must reproduce the fixture exactly before a search runs.

Controls currently support preserved spacing only. The assembly control is iid
sampling from development cipher-symbol frequencies, with the same word slots;
it is not the project's earlier, more elaborate assembly generator. The mismatch
is a reversible seven-symbol block reversal outside the implemented decoder.

## Search prepared ciphertext

```bash
uv run --locked python -m voynich.experiments.e26_decipherment_search search \
  --train data/latin_alfonsi.txt --language latin \
  --cipher /absolute/path/development.txt \
  --evaluation /absolute/path/reserved.txt \
  --family groups --spacing preserve \
  --steps 5000 --restarts 8 --workers 4 --beam 16 \
  --output results/my_decipher_run/group_candidates.json
```

Use `--family mixed --word-units 8` for the bounded word-code arm.
`--spacing infer` is implemented but not recovery-calibrated. Full options are
available with `--help`.

Candidate selection and ordering use development scores only. Evaluation runs
after fitting with the same keys, language model, unit inventory and beam width.
Do not select a winner by inspecting evaluation outputs and still call that
passage a holdout. Missing key coverage is reported as invalid, not given an
optimistically scored partial reading.

The output retains up to `--keep` candidates and per-restart archives. A sibling
`.checkpoint` file saves completed restarts; automatic resume is not implemented.
Existing output/checkpoint files are protected unless `--overwrite` is explicit.
Worker completion order does not change random seeds or final ranking.

The search accepts large step budgets, but this version rescans the passage for
each proposal. Millions of evaluations are not yet a performance guarantee.
Profile on the intended architecture and passage before scheduling a long run;
variable-boundary beams have a different cost from character substitution.

## Verification and initial results

```bash
uv run --locked python -m unittest discover -s tests -t . -p 'test_decipher_search.py' -v
```

Tests cover normalized conditional probabilities, incremental scoring,
known-key round trips, ambiguous segmentation against exhaustive enumeration,
homophone costs, full cipher coverage, word-boundary restrictions, deterministic
search, mutation limits, frozen-key behavior, control splits and the CLI.

Recorded pilots are in `results/decipher_framework_2026-09-30/`; the accompanying
`SUMMARY.md` distinguishes recovery demonstrations from execution-only checks.
These were development runs without predeclared success thresholds. No Voynich
page was searched, no family was excluded and no decipherment was claimed.

## Next engineering gate

1. Improve recovery on two-homophone and variable-group controls, including rare
   codes and passages with symbols absent from development. Any partial-coverage
   scoring must explicitly account for uncertainty rather than omit failures.
2. Add variable-width and ambiguous segmentation fixtures; measure recovery over
   multiple sources, keys, passage lengths and genuinely separate source texts.
3. Calibrate inferred spacing and complexity/length preferences using identical
   full search budgets for positives and negative/misspecified controls.
4. Profile and optimize proposals before a million-evaluation run. Incremental
   rescoring and better initial keys are likely useful extensions.
5. Freeze page selection, source panel, model bounds and interpretation criteria
   before treating any Voynich output as evidence. Apply the frozen candidates
   to additional pages without fitting new exceptions.

Only then use direct decipherment outcomes to update the candidate-family ledger.
