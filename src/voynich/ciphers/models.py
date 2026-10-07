"""Immutable API values; solver requests deliberately exclude fixture ground truth."""
from dataclasses import dataclass
from pathlib import Path

from voynich.decipher_search.core import digest


@dataclass(frozen=True)
class TextSource:
    text: str
    languages: tuple[str, ...]
    source_id: str
    uri: str | None = None

    def __post_init__(self):
        if not isinstance(self.languages, tuple) or not self.languages:
            raise ValueError("languages must be a nonempty tuple of declared language identifiers")
        if any(not isinstance(x, str) or not x.strip() for x in self.languages):
            raise ValueError("language identifiers cannot be empty")
        if not self.text.strip() or not self.source_id.strip():
            raise ValueError("text and source_id are required")

    @property
    def sha256(self) -> str:
        return digest(self.text)

    @classmethod
    def from_file(cls, path: str | Path, *, languages: tuple[str, ...],
                  source_id: str, encoding: str = "utf-8") -> "TextSource":
        file = Path(path).resolve()
        return cls(file.read_text(encoding=encoding), languages, source_id, file.as_uri())


@dataclass(frozen=True)
class PreparedText:
    text: str
    source: TextSource
    normalization: str


@dataclass(frozen=True)
class Ciphertext:
    text: str
    cipher_id: str

    def __post_init__(self):
        if not self.text.strip() or not self.cipher_id.strip():
            raise ValueError("ciphertext and cipher_id must be nonempty")


@dataclass(frozen=True)
class CipherKey:
    cipher_id: str
    entries: tuple[tuple[str, str], ...]  # cipher code -> plaintext unit

    def __post_init__(self):
        if not self.cipher_id.strip():
            raise ValueError("cipher_id is required")
        if not isinstance(self.entries, tuple) or not self.entries:
            raise ValueError("key entries must be a nonempty tuple")
        if any(not isinstance(p, tuple) or len(p) != 2 or
               any(not isinstance(x, str) or not x for x in p) for p in self.entries):
            raise ValueError("each key entry needs a nonempty code and plaintext unit")
        if len({c for c, _ in self.entries}) != len(self.entries):
            raise ValueError("duplicate cipher codes are ambiguous")

    def as_mapping(self) -> dict[str, str]:
        return dict(self.entries)


@dataclass(frozen=True)
class EncryptedFixture:
    ciphertext: Ciphertext
    plaintext: PreparedText
    key: CipherKey
    key_seed: int | None
    encryption_seed: int
    method: str

    def public_ciphertext(self) -> Ciphertext:
        """Return only ciphertext and its declared scheme identifier, never truth."""
        return self.ciphertext


@dataclass(frozen=True)
class DecryptionResult:
    plaintext: str
    method: str
    exact_coverage: bool
    # Exact coverage means every input symbol was consumed, not that a recovered
    # key or its plaintext is correct.


@dataclass(frozen=True)
class RecoveryCandidate:
    result: DecryptionResult
    key: CipherKey
    score: float
    path: tuple[str, ...]


@dataclass(frozen=True)
class RecoveryResult:
    candidates: tuple[RecoveryCandidate, ...]
    training: TextSource
    configuration: tuple[tuple[str, object], ...]
    evaluations: int
    score_interpretation: str = "Exploratory best-path cost; not a probability of correctness."
