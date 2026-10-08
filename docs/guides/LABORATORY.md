# Cipher laboratory: operating guide

The first benchmark and follow-up studies are complete. Review the
[8 October operating report](../../results/laboratory_2026-10-08/report.html)
and its [machine-readable evidence](../../results/laboratory_2026-10-08/evidence.json).
Infrastructure tests are engineering checks, not evidence about the Voynich manuscript.

The execution comprises 1,200 exact known-key cases across four works in three
languages, plus 216 persisted searches and 586,672 candidate evaluations.
All 12 shift keys and all 40 page-choice paths were recovered; page tables were
known. The original 32 blind positive cases passed no full gates. A longer
substitution follow-up recovered development text exactly for all four works,
with full frozen-transfer/control gates passing for Alfonsi and Dante only.
Caesar and Homer had unseen reserved symbols; partial post-search diagnostics
do not overturn their failed complete-decode gates. Generic proposals also
succeeded at the higher budget, so success cannot be attributed to injectivity.

These are within-work tests with few keys, not calibrated language-wide recovery
rates. No Voynich ciphertext was searched. A structural audit corrected six
mixed-code reachability labels; original labels and results remain in the export.

The accepted design is [ARCHITECTURE.md](../ARCHITECTURE.md). The original
[OO API](CIPHER_API.md) and September pilot commands remain compatible. New
tracked runs use the laboratory runner; historical CLI invocations do not
silently acquire database side effects.

## Components

| Component | Implementation | Responsibility |
|---|---|---|
| Concrete method | `ciphers.units.UnitCipher` | Generate/validate keys; encrypt; independently decode prefix-free codes |
| Page method | `ciphers.pages.PageSubstitution` | Execute explicit table choices and return state |
| Choice policy | `UniformPageChoices` | Sample, enumerate and assign choice probabilities |
| Fixtures | `laboratory.fixtures.FixtureBuilder` | Prepare Latin/Italian source spans; retain provenance and private truth |
| Public input | `PublicInput` | Ciphertext, method identifier, spacing and dataset role |
| Search | `AnnealingSearch`, `PageChoiceSearch` | Propose candidates, consume feedback and serialize strategy state |
| Evaluation | `KeyEvaluator`, `PageEvaluator` | Decode public inputs and report named costs |
| Execution | `ExperimentRunner` | Budgets, synchronous workers, retention and checkpoints |
| Persistence | `storage.registry.Registry` | PostgreSQL specifications, runs and optional compact attempts |

One cipher execution receives a concrete key and explicit randomness seed.
A search explores candidate keys/choices; it never receives a fixture object.
Reserved evaluation inputs are rejected by the adaptive search constructor.
Fixture truth is loaded explicitly with `SyntheticFixture.load_private()`;
public inputs have a separate `PublicInput.load()` entry point.

The reference decoder is a trie traversal, independent of the explorer's
language model and beam decoder. The fast matrix covers 80 configurations:
two languages, one/two homophones, glyph/group/mixed families, supported
fixed/variable code lengths, preserved/encoded spaces and two seeds. These
tests demonstrate reversibility, not unknown-key recovery.

| Family | Code lengths | Plaintext units | Homophones | Spacing |
|---|---|---|---|---|
| Glyph | One character | Letters | 1 or 2 | Preserved or encoded |
| Groups | Fixed two characters or prefix-free variable 1/2 | Letters and configured pairs | 1 or 2 | Preserved or encoded |
| Mixed | Fixed two characters or prefix-free variable 1/2 | Letters, configured pairs and whole words | 1 or 2 | Preserved or encoded |

Encoded spacing means spaces have their own cipher codes, allowing exact
reconstruction. Dropping spaces irreversibly is not silently treated as an exact
round trip. Variable glyph codes, unsupported languages and non-prefix-free
reference keys fail explicitly.

When adding a supported method, add it to the matrix in
`tests/test_laboratory_ciphers.py`, check both independent reference and explorer
decoding, add an invalid-key case, and update this table. Unknown-key success
requires separate opt-in benchmark evidence.

## Set up PostgreSQL

From the repository root:

```bash
uv sync --locked
uv run --env-file .env --locked python -m voynich.storage.database
uv run --env-file .env --locked alembic upgrade head
```

The local URL is `POSTGRES_URL="postgresql:///voynich"`. Remove stale PGHOST
or PGUSER settings if you want libpq's OS-user/local-socket defaults: URL fields
that are absent can still inherit libpq environment defaults.

The explicit migration creates `lab_specifications`, `lab_runs`,
`lab_attempts` and `lab_alembic_version`. Imports and engine construction
never migrate the database. Destructive downgrade is intentionally unsupported;
future schema changes require forward migrations.

Index historical evidence without rerunning it:

```bash
uv run --env-file .env --locked voynich-lab import-pilots results/decipher_framework_2026-09-30
uv run --env-file .env --locked voynich-lab list --family glyph
```

Imports are idempotent and retain original source/configuration/provenance,
artifact hashes and explicit missing metadata. Their status is
`historical-engineering-pilot`, not family rejection or newly calibrated success.

## Prepare the first benchmark without executing it

A frozen plan is checked in at
[configs/benchmarks/initial.json](../../configs/benchmarks/initial.json).

```bash
uv run --locked voynich-benchmark preflight configs/benchmarks/initial.json
```

This validates source hashes, passage availability, settings and success criteria.
It does not generate fixtures, encrypt passages or search keys. To prepare an
alternative plan at a new path:

```bash
uv run --locked voynich-benchmark plan /tmp/alternative-plan.json
```

The initial matrix contains 128 searches (32 positive cases and 96 matched
controls), capped at 256,512 scored candidates in total. It spans Latin/Italian,
four methods, two keys and two passage lengths. Each search has four chains and
500 proposals per chain; initial keys count in the budget. Source spans use raw
character offsets and explicit gaps, and are labelled same-work validation.
The current sources do not represent whole languages or historical genres.

Success criteria were chosen before execution: at least 95% non-space development
accuracy, at least 90% frozen-key accuracy with full coverage, and a lower
development loss than every matched negative. A failure is an engineering
result, not evidence excluding a Voynich cipher family. Group/mixed fixtures
outside the bounded code/unit inventory are labelled challenge controls.

## Execute an independent benchmark run

```bash
uv run --env-file .env --locked voynich-benchmark run configs/benchmarks/initial.json \
  --output results/runs/initial-benchmark --workers 4
```

This command performs real synthetic encryption, blind recovery and subsequent
truth evaluation. It refuses an existing output directory and changed source
hashes. Each search registers automatically; exact repeats require an explicit
rerun reason through the lower-level runner. Benchmark-wide automatic resume
and rerun orchestration are not implemented. A failed benchmark preserves
completed cases and per-run IDs for diagnosis/resume through the Python API.

Each case finishes all development searches before evaluating the frozen
positive key. Shuffled, iid message-free and block-order-mismatched controls
use the same budget, model and selection rule. Unseen held-out codes remain
invalid/incomplete: the evaluator does not fit new mappings. Negative-control
truth accuracy is not treated as meaningful.

## Registry and scope queries

```bash
uv run --locked voynich-lab validate path/to/manifest.json
uv run --env-file .env --locked voynich-lab scope path/to/proposed-manifest.json
uv run --locked voynich-lab compare old-manifest.json proposed-manifest.json
```

Fingerprints include language/source spans, normalization, code/environment,
model, scorer, method, seeds, budget and retention. Scope queries report changed
paths and matching registrations. A matching registration alone does not imply
a completed experiment or a scientific conclusion. Reruns have unique run IDs.

## Retention, resume and current limits

The default runner retains 100 distinct best candidates and a seeded reservoir
of 100 attempts. The benchmark uses 10 of each. Retained candidates have complete
key/choice payloads; compact-only records have identification and scores, not
reconstruction guarantees. Full compact storage is opt-in. No every-candidate
plaintext archive is produced.

The PostgreSQL checkpoint and compact batch commit atomically. Files are atomic,
checksummed mirrors; resume trusts the validated database checkpoint after an
interrupted mirror write. Resume requires the same specification, strategy,
scorer, input and batch size. Worker count may change. Incompatible changes,
including budget extensions, require a new run; amendments are not implemented.

`retention.max_bytes` is a **soft serialized-checkpoint threshold**, checked at
batch boundaries. It stops the run and removes optional retained payloads when
exceeded, but preserves essential strategy/RNG state. It is not a hard disk
quota and excludes PostgreSQL physical overhead, compact rows and manifests.
Do not use it to protect a nearly full filesystem. Exact disk/memory quotas
remain future work.

Evaluation is deterministic in this increment. Unsupported stochastic scoring
raises `NotImplementedError`; synthetic spelling and page choices already have
separate seeded streams. Evaluation caching is disabled (reported as zero cache
hits), so every scored proposal counts, including duplicates. Unique-candidate
totals are reported as unavailable. Synchronous batches checkpoint after every
batch (at most 1,000 candidates), not during an individual long evaluation.

The ambiguity oracle distinguishes multiple paths from multiple plaintexts and
reports incomplete exploration honestly. Its summed path weights are not
calibrated probabilities. The production explorer remains a bounded best-path
decoder and makes no uniqueness or probability-mass claim.

## Engineering validation

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --locked python -m unittest discover -s tests -t .
POSTGRES_TEST_URL=postgresql:///voynich_test OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  uv run --locked python -m unittest discover -s tests -t .
uv build
```

The first command skips live PostgreSQL tests unless a test URL is set. The
second uses a separately provisioned test database; each integration test creates
and drops only its own random schema. CI supplies an isolated PostgreSQL service
and runs all tests. No production research benchmark runs in CI. Tiny generated
nonsense fixtures exercise the full coordinator in the fast suite without
drawing research conclusions.

## Medical cross-author recovery and explicit codebooks

The next frozen screen is documented in
[the medical protocol](../protocols/MEDICAL_RECOVERY_2026-10-08.md). It compares a
key-search beam with annealing under equal candidate budgets, trains on the other
medical author, and separates oracle scoring, recovery, boundary and reserved-code
diagnostics. It uses the existing registry and requires the migrated database.

```bash
uv run --env-file .env --locked python -m voynich.laboratory.medical_recovery \
  --plan configs/benchmarks/medical-recovery-2026-10-08.json \
  --output results/runs/medical-new
```

`CodebookProblem` specifies public ciphertext, training text, allowed emissions,
code width (one/two, or a searched prefix policy), and maximum codes per unit.
`CodebookSearch` proposes complete codebook/prefix candidates with either
`algorithm="annealing"` or `algorithm="beam"`; `CodebookEvaluator` scores them.
Unlike the legacy search, a two-character code needs no forced single-character
fallback entries. Search constructors reject reserved evaluation inputs.
`partial_transfer()` freezes the selected mapping and reports `?` for unseen
codes, without fitting on reserved text.

For a separate next-stage fixture, the encoder can restrict its basic symbols:

```python
from voynich.ciphers.units import UnitCipher

method = UnitCipher("groups", homophones=2, lengths="variable",
                    extra_units=("er", "in"), alphabet="ABCDEFGHIJKLMNOPQRST")
key = method.generate_key(seed=7)
ciphertext, alignment = method.encrypt_text("in herba erat", key, seed=8)
assert method.decrypt_text(ciphertext, key).plaintexts == ("in herba erat",)
```

Default-alphabet keys retain their previous generation and method ID; custom
alphabets use `prefix-unit-alphabet-v1`. Capacity shortages fail explicitly.
The variable-code construction reserves half the alphabet for single-character
leaves and half for two-character prefixes; it is a restricted code family,
not every prefix-free table. Tests cover 12/20-symbol alphabets, both decoders,
spacing modes, homophones and serialization. These are engineering tests only;
the medical recovery screen uses the original alphabet. A synthetic alphabet
size is not a claim about the correct Voynich transcription or a historical key.

`count_mapping_completions()` counts possible assignments to distinct unseen
codes under the selected key's emission capacities and fixed segmentation. It
uses no reserved language scores, chooses no mapping, and supplies no calibrated
probability. It supports letter/pair emissions; word-position constraints require
additional state and currently raise `NotImplementedError`.
