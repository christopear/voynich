# Synthetic-cipher API: architecture and contracts

For the accepted target architecture, see [ARCHITECTURE.md](../ARCHITECTURE.md).
This guide documents the current API; its solver wrapper will migrate behind
the search/experiment interfaces described there.

5 October 2026. Framework groundwork for CHR-374/CHR-375; this does not complete
their full configuration matrix or establish solver recovery power.

## Architectural decision

Three approaches were considered before implementation:

1. One large class that loads text, encrypts, decrypts, fits a language model and
   scores recovery. Convenient initially, but it mixes oracle keys with blind
   search and makes independent testing difficult.
2. Separate encryption/decryption classes with different metadata and implicit
   conversions. Better separation, but easy to lose source and normalization
   information between them.
3. **Two small role interfaces sharing immutable value objects.** This is the
   chosen approach. Cipher construction and decoding can evolve independently,
   while tests use the same public contracts for every implementation.

Known-key decryption and unknown-key recovery are different operations. The
reference decoder needs no language model and must not consume stored truth or
alignment. A solver may need a training source and search configuration, but
its recovery call accepts only a public ciphertext object.

## Required methods

| Interface/method | Responsibility | Return |
|---|---|---|
| `Encryption.prepare(source)` | Normalize explicitly, retain original text and provenance | `PreparedText` |
| `Encryption.generate_key(seed=...)` | Construct a key independently of the test passage | `CipherKey` |
| `Encryption.encrypt(source, key=..., key_seed=..., encryption_seed=...)` | Encrypt with supplied or generated key and reproducible choice randomness | `EncryptedFixture` |
| `Decryption.decrypt(ciphertext, key=...)` | Known-key decoding, without key fitting or silently filling missing entries | `DecryptionResult` |
| `Decryption.recover(ciphertext)` | Optional unknown-key search with configuration supplied at construction | `RecoveryResult` |

Encryption methods and `decrypt` are abstract and contain `raise
NotImplementedError`. Incomplete subclasses cannot be instantiated. The optional
`recover` method raises `NotImplementedError` unless an implementation supplies
it. Unsupported languages/configurations raise explicitly; no no-op stubs return
success. Malformed supported inputs raise `ValueError`, and passing a fixture
instead of public ciphertext to the decoder raises `TypeError`.

Do not add fetching, benchmark selection, experiment registration or CI logic to
these interfaces. Those are orchestration concerns using the library.

## Data objects and provenance

- `TextSource`: text, a tuple of declared language identifiers, stable source ID,
  optional URI and a SHA-256 property of the loaded text's UTF-8 encoding. Use
  `from_file(...)` for explicit local loading. No downloading or language
  detection occurs. Multilingual labels are provenance, not inferred spans.
- `PreparedText`: normalized text, original `TextSource`, normalization version.
- `CipherKey`: scheme/version ID and immutable code-to-unit entries. Repeated
  codes are rejected; different codes may represent the same plaintext unit.
- `Ciphertext`: text and declared scheme ID only. It contains no original
  plaintext, source passage, key, random seeds or alignment.
- `EncryptedFixture`: ciphertext plus private experimental truth, normalization,
  key, method and seeds. Call `public_ciphertext()` to obtain solver input.
- `DecryptionResult`: plaintext, method and full-coverage flag. Full coverage is
  not a correctness claim about a recovered key.
- `RecoveryResult`: ranked candidates, training-source provenance, settings and
  evaluation count. Candidate scores are not correctness probabilities.

The separation prevents accidental API coupling, not malicious access inside a
Python process. A future blind benchmark runner must keep fixture truth out of
the search process/files it exposes. `dataclasses.asdict` can serialize these
objects for a future manifest layer; serializing a whole fixture is **not** a
safe way to construct public solver input. Versioned artifact import/export and
formal manifest validation remain separate work.

## Implemented reference and adapter

`SubstitutionEncryption(homophones=1|2)` supports the existing ASCII-folding
normalization for declared Latin/Italian text, preserved spaces and a full
26-letter key. It expands ae/oe ligatures, folds accents, and keeps i/j and u/v
distinct. Round trips recover **normalized plaintext**, not original punctuation,
capitalization or accents. Key generation does not inspect source text. Separate
seeds control key generation and homophone selection; supplied keys record no
invented key-generation seed.

`ReferenceDecryption` independently maps characters through the supplied key.
It does not call the explorer, consult language probabilities or inspect fixture
truth. Missing symbols and scheme mismatches fail explicitly.

`AnnealingDecryption(training, config=...)` adapts the existing explorer's
known-key decoder and annealing search. Its initial OO contract deliberately
supports only character substitution/homophones with preserved spaces. Grouped
codes, inferred spacing and mixed word-code settings raise `NotImplementedError`
here, even though the procedural explorer contains experimental implementations
of those families. Their public contracts need independent decodability tests
before being exposed as reliable round-trip implementations.

Recovery currently runs sequential restarts and reuses existing scoring/search
code. It does not introduce a new optimizer, parallel orchestration or an
accuracy guarantee. A language label cannot verify that a supplied corpus is
actually in that language. Dataset separation remains the benchmark runner's
responsibility.

## Example: both sides through the same interface

```python
from voynich.ciphers import (
    AnnealingDecryption, ReferenceDecryption, SubstitutionEncryption, TextSource,
)
from voynich.decipher_search.core import Config

source = TextSource("Aqua est bona.", ("latin",), "example:reserved-passage")
encryption = SubstitutionEncryption(homophones=2)
fixture = encryption.encrypt(source, key_seed=11, encryption_seed=12)
public = fixture.public_ciphertext()

reference = ReferenceDecryption()
assert reference.decrypt(public, key=fixture.key).plaintext == fixture.plaintext.text

# Supply a separate training corpus, not the passage under test.
training = TextSource.from_file(
    "data/latin_alfonsi.txt", languages=("latin",), source_id="alfonsi:training",
)
explorer = AnnealingDecryption(training, config=Config(steps=100, restarts=2))
assert explorer.decrypt(public, key=fixture.key).plaintext == fixture.plaintext.text

# No oracle key or original plaintext is an argument to recovery.
candidates = explorer.recover(public)
best = candidates.candidates[0]
print(best.result.plaintext, best.score)  # A hypothesis, not a claimed reading.
```

For benchmark runs, reserve disjoint sources/passages before constructing these
objects. This short example demonstrates the API rather than solver accuracy.

## Tests and the next CHR-375 increment

```bash
uv run --locked python -m unittest tests.test_cipher_api -v
uv run --locked python -m unittest discover -s tests -t . -v
```

The initial contract matrix covers two languages, three sample forms each, two
homophone settings and two key seeds, through both reference and explorer
known-key decoders. Additional tests cover immutable metadata, separate seeds,
supplied-key reuse on another passage, unknown codes, normalization, deterministic
search, public/truth separation and explicit unsupported operations.

For CHR-375, add implementations incrementally behind these interfaces: first
fixed-width groups, then uniquely decodable variable-width codes, then bounded
word codes. Each needs an independent reference decoder and the same round-trip
tests. Non-uniquely decodable systems need an explicit ambiguity result; never
silently convert an LM-preferred hypothesis into an exact decryption guarantee.
Keep unknown-key recovery benchmarks separate from these contract tests.

The existing procedural synthetic helpers/CLI and their recorded pilots are
unchanged. Migrating their fixture storage and orchestration onto this API is a
subsequent change, avoiding unannounced changes to historical generated keys.
