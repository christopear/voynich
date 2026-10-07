"""Small execution contracts, independent of optimizers and persistence."""
from dataclasses import dataclass
from typing import Protocol
from .models import CipherKey


@dataclass(frozen=True)
class MethodCapabilities:
    known_key: bool = True
    known_choices: bool = True
    exact_reference: bool = True
    independent_pages: bool = True


@dataclass(frozen=True)
class Segment:
    id: str
    text: str
    source_start: int
    source_stop: int

    def __post_init__(self):
        if not self.id or not self.text or not 0 <= self.source_start < self.source_stop:
            raise ValueError("segment needs stable ID, content and valid source span")


@dataclass(frozen=True)
class Document:
    pages: tuple[Segment, ...]

    def __post_init__(self):
        if not isinstance(self.pages, tuple) or not self.pages:
            raise ValueError("document needs a tuple of pages")
        if len({p.id for p in self.pages}) != len(self.pages):
            raise ValueError("duplicate page IDs")
        if any(a.source_stop > b.source_start for a, b in zip(self.pages, self.pages[1:])):
            raise ValueError("page source spans overlap or are out of order")


@dataclass(frozen=True)
class CipherState:
    position: int = 0
    active_table: int = 0


@dataclass(frozen=True)
class DecodingOutcome:
    plaintexts: tuple[str, ...]
    status: str  # no-valid-path, unique-plaintext, multiple-plaintexts, unresolved
    coverage: float
    path_count: int
    complete: bool
    pruned: bool = False
    path_multiplicity: str = "exact"
    # Coverage never implies correctness; paths may share a plaintext.


@dataclass(frozen=True)
class PageOutcome:
    document: Document
    state: CipherState
    decisions: tuple[int, ...]


class CipherMethod(Protocol):
    def capabilities(self) -> MethodCapabilities: ...
    def validate_key(self, key: CipherKey) -> None: ...
    def generate_key(self, *, seed: int) -> CipherKey: ...
    def initial_state(self) -> CipherState: ...
    def encrypt_text(self, text: str, key: CipherKey, *, seed: int) -> tuple[str, tuple]: ...
    def decrypt_text(self, text: str, key: CipherKey) -> DecodingOutcome: ...
