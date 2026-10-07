"""Explicit page choices. Coupled transitions invalidate pagewise optimization."""
from dataclasses import dataclass
import itertools
import math
import random
from .contracts import CipherState, Document, Segment, PageOutcome, MethodCapabilities
from .models import CipherKey
from .units import UnitCipher


@dataclass(frozen=True)
class UniformPageChoices:
    table_count: int = 6

    def __post_init__(self):
        if type(self.table_count) is not int or self.table_count < 1:
            raise ValueError("positive table count required")

    def sample(self, page_ids: tuple[str, ...], *, seed: int) -> tuple[int, ...]:
        rng = random.Random(seed)
        return tuple(rng.randrange(self.table_count) for _ in page_ids)

    def enumerate(self, page_ids: tuple[str, ...]):
        return itertools.product(range(self.table_count), repeat=len(page_ids))

    def log_probability(self, choices: tuple[int, ...]) -> float:
        if any(type(c) is not int or not 0 <= c < self.table_count for c in choices):
            return -math.inf
        return -len(choices) * math.log(self.table_count)


@dataclass(frozen=True)
class PageSubstitution:
    method: UnitCipher = UnitCipher()
    coupled: bool = False

    def generate_tables(self, *, seed: int, count: int = 6):
        if count < 1:
            raise ValueError("positive table count required")
        from voynich.laboratory.manifest import stream_seed
        base = self.method.generate_key(seed=seed)
        codes, emissions = zip(*base.entries)
        tables = []
        for index in range(count):
            values = list(emissions)
            random.Random(stream_seed(seed, str(index), "table-key")).shuffle(values)
            tables.append(CipherKey(base.cipher_id, tuple(zip(codes, values))))
        return tuple(tables)

    def capabilities(self):
        return MethodCapabilities(independent_pages=not self.coupled)

    def initial_state(self):
        return CipherState()

    def execute(self, document: Document, tables: tuple[CipherKey, ...],
                choices: tuple[int, ...], *, decrypt: bool, state: CipherState | None = None,
                seed: int = 0) -> PageOutcome:
        if len(choices) != len(document.pages) or not tables:
            raise ValueError("one concrete choice per page and nonempty tables required")
        for table in tables:
            self.method.validate_key(table)
        state = state or self.initial_state()
        if state.position < 0 or not 0 <= state.active_table < len(tables):
            raise ValueError("invalid execution state")
        pages, actual = [], []
        from voynich.laboratory.manifest import stream_seed
        for page, choice in zip(document.pages, choices):
            if type(choice) is not int or not 0 <= choice < len(tables):
                raise ValueError("choice outside table range")
            table = (state.active_table + choice) % len(tables) if self.coupled else choice
            if decrypt:
                outcome = self.method.decrypt_text(page.text, tables[table])
                if outcome.status != "unique-plaintext":
                    raise ValueError("table cannot decode this page")
                content = outcome.plaintexts[0]
            else:
                content, _ = self.method.encrypt_text(page.text, tables[table],
                    seed=stream_seed(seed, page.id, "encryption"))
            pages.append(Segment(page.id, content, page.source_start, page.source_stop))
            actual.append(table)
            state = CipherState(state.position + 1, table)
        return PageOutcome(Document(tuple(pages)), state, tuple(actual))
