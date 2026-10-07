# Cipher laboratory architecture

**Status:** accepted design for subsequent implementation.
**Decided:** 5 October 2026.
**Scope:** synthetic cipher construction, known-key decoding, unknown-key search,
and reproducible experiment execution.

This is the architectural source of truth. The [research constitution](RESEARCH_CONSTITUTION.md)
governs scientific interpretation. The [existing API guide](guides/CIPHER_API.md)
describes the current implementation; where it differs, this document defines
the migration target. Acceptance of this design does not mean the infrastructure
below is already implemented.

## 1. Main decisions

1. Keep one Python package, `voynich`, with separate cipher, search, evaluation
   and experiment modules. Use composition and small typed interfaces.
2. Separate a **cipher method**, a **key**, concrete **choices**, and evolving
   **execution state**. A random page-table choice is not a new cipher method.
3. Cipher methods execute operations. Search strategies explore hypotheses.
   Experiment runners control budgets, provenance and persistence.
4. Public inputs and synthetic ground truth are separate objects and artefacts.
   A blind search must not receive the truth package.
5. Return structured scores, ambiguity and coverage. A plaintext string alone
   is not a sufficient decoding result.
6. Use versioned JSON manifests, PostgreSQL for indexed records, and separate
   files for retained larger artefacts. Start with a single coordinator/writer.
7. Default to bounded retention and deterministic synchronous search. Record
   replay guarantees explicitly; never imply a hash alone can recreate a key.
8. Implement in small end-to-end increments. No distributed service, general
   cipher programming language, plugin discovery system or dashboard initially.

## 2. Components and ownership

| Component | Owns | Does not own |
|---|---|---|
| `CipherMethod` | Rule specification, capabilities, key validation/generation, concrete encryption/decryption | Search budgets, source downloads, databases |
| `ChoicePolicy` | Distribution over choices, sampling/enumeration, declared state transitions | Language scoring or plaintext truth |
| `SearchStrategy` | Candidate proposals, feedback, population/beam and search checkpoint state | Ground truth, filesystem layout or direct worker writes |
| `Evaluator` | Constraint checks, decoding policy, named score components and coverage | Candidate proposal or changing the experiment specification |
| `ExperimentRunner` | Inputs, preflight, execution order, budgets, lifecycle and orchestration | Cipher-specific rules or arbitrary rescue assumptions |
| `ResultStore` | Transactional attempt records, retained artefacts, checkpoints and queries | Deciding whether a cipher hypothesis is scientifically supported |
| `FixtureBuilder` | Synthetic source selection, construction and private truth package | Passing oracle information into solver requests |

Implement the stateless extension interfaces as Python `Protocol`s where
practical. Use concrete classes for policies, runners and stores. Retain current
`Encryption`/`Decryption` facades through adapters while migrating; do not make
every cipher implement an optimizer or inherit a large framework base class.

Suggested package boundaries:

```text
voynich/ciphers/       Cipher methods, keys, choices, state and reference decoders
voynich/search/        Candidate spaces, search strategies and search state
voynich/evaluation/    Scorers, validity checks, recovery metrics and calibration
voynich/laboratory/    Sources, synthetic fixtures and private truth
voynich/experiments/   Runner, specifications and existing numbered entry points
voynich/storage/      Registry, PostgreSQL records and artefact retention
```

Create each boundary when its first implementation is needed, not as empty
scaffolding. Shared value types must not depend on the runner or PostgreSQL. The
existing `decipher_search` code is adapted incrementally rather than rewritten
wholesale.

## 3. What is an experiment?

Use these distinct concepts and identifiers:

| Object | Meaning |
|---|---|
| `ExperimentSpec` / specification fingerprint | Immutable scientific/computational setup, reusable across executions |
| `Run` / unique run ID | One execution of that specification, including an intentional rerun |
| `Candidate` / candidate fingerprint | A concrete key/choice/state hypothesis under a method version and declared scope |
| `EvaluationRequest` / request ID | Candidate plus dataset slice, scorer, decoding policy, budget/fidelity and replicate |
| `Attempt` / attempt ID | One execution of a request; retries have distinct attempt IDs |
| `Artifact` / content hash | A stored payload such as a key, plaintext, path or model |

The specification records method versions, source languages, works and available
genre/date provenance; raw/prepared input hashes; normalization and segmentation;
data roles; reset/state rules; search/scorer settings; seeds; budgets; retention;
and the implementation/environment fingerprint.

Canonical fingerprints use validated, schema-versioned JSON and SHA-256. Sort
object keys; preserve order where it has meaning; reject NaN and infinity as
configuration values. Record input encoding and normalization explicitly. Source
URIs are provenance, not a substitute for content hashes.

Capture Git commit and dirty state plus hashes of relevant source/model files:
uncommitted code must be distinguishable. Record Python, dependency lock and RNG
versions. Changed scientific settings create a new specification. Intentional
identical reruns create new runs with a reason, not overwritten histories.

## 4. Method, choices and state

The initial method contract will provide:

```text
capabilities() -> MethodCapabilities
validate_key(key) -> ValidationResult
generate_key(key_spec, random_stream) -> Key
initial_state(scope_spec) -> CipherState
encrypt(prepared_input, key, choices, state) -> EncryptionOutcome
decrypt(cipher_input, key, choices, state) -> DecodingOutcome
```

`choices` describes one concrete realization when execution requires it.
Unknown choices belong in a `CandidateSpace`, not an implicit random selection
inside decryption. A `ChoicePolicy` supplies `sample`, optionally `enumerate`,
and `log_probability`; each operation declares whether it is implemented.
Unsupported operations raise `NotImplementedError`, and runner preflight checks
capabilities before spending the budget.

Represent document/page/line boundaries explicitly, using stable IDs and source
offsets. Never infer reset rules from whitespace collapsing. State includes
things such as active table, remaining deck and stream position; it is returned
explicitly, not hidden in a mutable method singleton. Specifications declare
where state resets and what the legitimate reader knows.

For the six-table example, the method is page-selected substitution, the key is
the set of six tables, and choices are page-ID-to-table assignments. If tables
and assignments are known, decoding is deterministic. If assignments are unknown,
search explores them. Independent page choices and additive scores permit
separate page optimization; shared state, unknown shared tables or cross-page
scoring invalidate that shortcut. Independence must be declared and tested.

A choice trace retained by a synthetic fixture is private ground truth. A decoder
may receive it only in an explicitly labelled known-choice experiment. Stochastic
homophone spelling may require no choice trace to decode at all.

## 5. Randomness and repeatability

Use independent deterministic streams for key generation, encryption choices,
search proposals, evaluation replicates and diagnostic sampling. Derive seeds
with a versioned SHA-256 scheme from the master seed, stable task identifier and
stream purpose; never use Python's process-randomized `hash()` or worker number.

The initial runner uses synchronous batches: generate candidates in stable order,
assign IDs before dispatch, and incorporate completed results in that same order.
This prevents worker completion timing from changing adaptive search trajectories.
Do not promise bitwise floating-point agreement across hardware; distinguish
same-environment replay from cross-environment tolerance checks.

An attempt records which randomness applies. If evaluation is stochastic,
replicates are separate requests with recorded seeds. Aggregate count, mean,
dispersion and the prespecified comparison rule. Do not treat one noisy score as
a deterministic candidate property or mix fidelities in one leaderboard.

## 6. Decoding and score contracts

`DecodingOutcome` must distinguish invalid input, no valid path, a unique
plaintext, multiple plaintexts, and unresolved uniqueness after approximation.
Separately report path multiplicity, symbol coverage, completeness and pruning.
Multiple paths may yield the same plaintext. A unique surviving beam item is not
proof of unique decoding.

Expose best-path, candidate-list and probability-summing operations separately.
Exact enumeration/dynamic programming reports exactness only under its declared
model and limits. Beam search reports width, pruning and retained support. If
probabilities are available, sum mass for paths yielding the same plaintext.
Call that sum exact only if all relevant paths were accounted for. Do not
normalize retained beam scores and label them calibrated plaintext probabilities.

`ScoreReport` contains scorer/version, direction, named components, units,
denominators, configuration/weights, validity, coverage and diagnostics. Initial
components are language cost, encoding-choice cost and key/rule complexity;
the current sum remains an exploratory objective, not model evidence. Hard
constraint failures are structured invalid results, not invented finite losses.

Persist execution status, computational validity, ground-truth accuracy and
scientific verdict separately. Only a prespecified analysis can assign a scoped
rejection/support verdict. Budget exhaustion or an optimizer failure cannot.

## 7. Data and leakage boundaries

Dataset references declare role: language-model training, solver development,
reserved evaluation or synthetic truth. Record work/source identity, spans,
transcription, segmentation and normalization versions. Check exact overlap and
span overlap before a run; report that these checks cannot certify absence of
repeated content across different works.

Do not download sources or choose train/test splits inside a cipher method.
`FixtureBuilder` stores public ciphertext/allowed assumptions separately from
truth, keys, hidden choices, alignment and original plaintext. The search process
receives only an explicit public request. Reserved evaluation is run after
development candidate selection and cannot feed the search strategy.

Truth-based metrics are computed afterwards in the evaluation coordinator. An
unseen symbol or uncovered region must remain visible in accuracy/coverage
reports; no optimistic omission or silent fitting of new assignments.

## 8. Storage, retention and replay

Use one dedicated PostgreSQL database for the workspace registry and run/attempt
records, accessed through SQLAlchemy 2.x with the psycopg 3 driver. Store larger
artefacts under `results/runs/<run-id>/`, with `manifest.json`, checkpoints and
summaries alongside them. Keep a single coordinator writer initially; workers
return results without writing directly. Use batched transactions, stable unique
request identifiers and indexes for scope/candidate queries. The user provisions
the database; importing the package never connects or creates a schema.

Manage schema changes through explicit versioned Alembic migrations when tables
are introduced; no implicit create/drop at startup. Connection settings live in
ignored `.env` or environment variables, with `.env.example` committed. Export
selected manifests/summaries for Git; credentials, database dumps and disposable
checkpoints are not committed. A future test database is separate from research
storage. See [PostgreSQL setup](guides/POSTGRESQL.md).

The registry indexes specification fingerprints, run IDs, cipher families,
scope and artefact locations. It can identify exact prior experiments and scope
gaps without treating a changed language/corpus/scorer as a duplicate. Earlier
pilots import with explicit unknown metadata; never manufacture provenance.

Two retention modes:

- **Default bounded mode:** exact aggregate counters; best 100 distinct candidate
  keys with full artefacts; a seeded reservoir of 100 diagnostic attempts;
  structured error counts plus bounded examples; compact progress every 1,000
  completed evaluations. These defaults are configuration, recorded in the spec.
- **Full compact mode:** additionally retain one compact row for every attempt,
  containing identifiers, reconstruction reference where available, score
  components, status and seed. Still do not store every plaintext.

Deduplicate the top set by candidate identity, not just plaintext. Record ties
with stable candidate-ID ordering. Keep total proposals, cache hits, completed
evaluations, failures and retained counts distinct. Report unique-candidate
counts as unavailable or approximate unless actually measured exactly.

Every retained record declares one replay level:

1. **Exact payload:** key/choices and required state are stored.
2. **Reconstructable:** a versioned deterministic recipe/checkpoint dependency
   is retained and verified.
3. **Summary only:** identifiers/scores remain but reconstruction is not promised.

A hash alone provides identification, not replay. A search seed alone is not a
reconstruction recipe for an arbitrary adaptive attempt. Retention garbage
collection must preserve referenced dependencies. Losing intermediate traces in
bounded mode is an explicit tradeoff, not silently claimed complete auditability.

## 9. Budgets, caching and checkpoints

Require a maximum evaluation count; allow time, storage and memory limits.
Reserve evaluation slots before dispatch so workers cannot overshoot the count.
On other limits, stop proposing, safely finish/cancel in-flight work and report
the outcome. Define whether initialization/oracle checks count in the budget;
the initial convention counts all scored search candidates including initial keys,
and reports fixture validation separately.

Run states: `created`, `running`, `completed`, `stopped`, `failed`. Record a
specific stop reason (exhaustive completion, evaluation/time/storage limit,
user cancellation, declared convergence or error). A stopped run can be resumed
only under its recorded compatibility rules.

Cache deterministic evaluation only. Cache identity includes candidate,
input/preprocessing, implementation, scorer/model and decoding policy/fidelity.
Stochastic requests include their replicate stream; aggregates are separate.
Invalid input may be cached if deterministic; transient infrastructure failures
must not become permanent scientific results. Start with a bounded in-memory
cache; persistent cross-run caching is deferred.

Checkpoint at completed synchronous batch boundaries, at least every 1,000
evaluations or 60 seconds, and on clean stop. Persist strategy state, RNG states,
candidate sequence number, incumbent set and counters after committing its
attempt batch. Link checkpoint to the durable database sequence. Use checksums
and atomic replacement; ignore orphaned temporary files after a crash.
Recovery selects the last consistent checkpoint; surplus later records must be
reconciled by stable request IDs rather than double-counted. A crash may lose
work since that checkpoint; do not call an interrupted batch exactly resumable.

Resume requires matching schemas, inputs, code/model hashes and scientific
settings. Extending the budget is an explicit continuation with an amendment
record. Incompatible changes create a new linked run. Do not serialize arbitrary
live Python objects with pickle as the durable public format.

## 10. Versioning and migration

Version method semantics, normalization, scorer, choice policy, seed derivation,
manifest and checkpoint schemas independently. Keep historical artefacts
read-only; migrations produce new versions with source references. Reject
unknown future schemas rather than interpreting them optimistically.

Current migration decisions:

- Retain existing OO known-key round-trip contracts as compatibility facades.
- Move the responsibility of `AnnealingDecryption.recover` behind a search
  strategy adapter; do not make cipher implementations own optimization.
- Replace flat-text-only experimental inputs with structured boundaries when
  page-state methods are introduced; keep the current flat adapter explicit.
- Expand result types to express ambiguity before exposing ambiguous reference
  decoders. Preserve `exact_coverage` as coverage, never uniqueness/correctness.
- Keep old CLI/pilot behavior available until equivalence tests pass. Do not
  reinterpret old results under new scoring or key-generation semantics.

## 11. Build order and acceptance gates

| Increment | Deliverable | Acceptance gate |
|---|---|---|
| 1: execution contracts | Method/key/choices/state and structured outcomes | Known-key, known-choice round trips through independent reference and explorer adapters; current tests stay green |
| 2: six-table experiment | Page structure, exhaustive choice strategy and evaluator | Recover/rank known alternatives; independent-page shortcut matches exhaustive search on a tiny document; coupled-state example disables the shortcut |
| 3: run/store foundation | Versioned manifest, registry, PostgreSQL attempts and bounded retention | Query prior scope; distinguish reruns; reconstruct retained candidates; top-k/reservoir limits and storage stop are tested |
| 4: adaptive search | Existing annealing adapter, synchronous workers and checkpoints | Same-environment sequential/parallel equivalence and crash/resume checks without duplicate accounting |
| 5: benchmark expansion | Fixture matrix, ambiguous toy method and matched controls | Exhaustive toy oracle verifies path aggregation/pruning claims; blind recovery evaluated separately from reversibility |

Fast CI covers contract validation, normalization, deterministic encryption,
independent decoding, truth separation, score bookkeeping, schema handling and
small runner/storage failures. Larger recovery/calibration matrices remain an
explicit command. Establish recovery thresholds before interpreting Voynich runs.

These increments connect to CHR-372/373 (registry/scope), CHR-374 (fixtures),
CHR-375 (round trips), CHR-376 (blind recovery), and CHR-377 (infrastructure tests).
They refine those issues rather than declaring them complete.

## 12. Changes to this decision

Amend this document when evidence or an implemented scenario reveals a problem.
Record date, changed decision, reason and compatibility impact. New complexity
must support a concrete experiment or a demonstrated reliability requirement.
The accepted design should guide implementation without freezing untested details.

### Amendment — 5 October 2026: PostgreSQL

At the user's request, PostgreSQL replaces SQLite for the registry and attempt
store. SQLAlchemy 2.x and psycopg 3 form the persistence boundary. No SQLite
schema has been implemented, so no data migration is required. File artefact
retention and the single-coordinator write model remain as specified. Track the
integration in [CHR-378](https://linear.app/christopear/issue/CHR-378).

### Implementation amendment — 7 October 2026: first executable increment

The [laboratory guide](guides/LABORATORY.md) documents the implemented contracts
and first benchmark gate. PostgreSQL is authoritative for checkpoints: strategy,
RNG, counters and optional compact attempts commit together. Atomic file copies
are mirrors, so a crash between database commit and file publication does not
require guessing which attempt rows to discard.

To keep the first research execution reviewable, this increment disables
evaluation caching and rejects stochastic scoring. It counts every scored
proposal, including duplicate proposals. Resume supports identical specifications;
budget extensions require a new run until continuation amendments are implemented.
These narrower capabilities avoid untested replay/cache semantics.

Storage budgeting is initially a soft serialized-checkpoint threshold, not a
physical database/disk or process-memory quota. Essential resumable state is
preserved even if it exceeds that threshold; optional payloads are dropped and
the run stops. Hard quotas, timed checkpoints within long batches, and
benchmark-wide automatic resume remain future implementation work. The original
requirements remain the target; these limitations must be visible in run guides
and must not be presented as completed guarantees.
