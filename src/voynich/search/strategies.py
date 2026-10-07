"""Resumable synchronous annealing and finite enumeration."""
from dataclasses import asdict, dataclass
import math
import random
from typing import Protocol
from voynich.decipher_search.core import (Config, LanguageModel, candidate_codes, initial_key,
                                         inventory, mutate)
from voynich.laboratory.fixtures import PublicInput
from voynich.laboratory.manifest import canonical, fingerprint, stream_seed


@dataclass(frozen=True)
class Candidate:
    recipe: str

    def __post_init__(self):
        import json
        data = json.loads(self.recipe)
        if data.get("schema") != 1 or not data.get("method"):
            raise ValueError("unsupported candidate recipe")
        object.__setattr__(self, "recipe", canonical(data))

    @classmethod
    def create(cls, method: str, **parameters):
        return cls(canonical({"schema": 1, "method": method, **parameters}))

    @property
    def data(self):
        import json
        return json.loads(self.recipe)

    @property
    def id(self):
        return fingerprint(self.data)


class SearchStrategy(Protocol):
    def propose(self, limit: int) -> list[Candidate]: ...
    def observe(self, results: list) -> None: ...
    def snapshot(self) -> dict: ...
    def restore(self, state: dict) -> None: ...
    def identity(self) -> dict: ...


def tuples(value):
    return tuple(tuples(v) for v in value) if isinstance(value, (list, tuple)) else value


class AnnealingSearch:
    """Reuse legacy mutations/objective; new synchronized per-chain scheduling.

    One proposal per chain per round. Worker count changes execution only,
    never proposal order or RNG streams. Initialization consumes an evaluation.
    """
    def __init__(self, public: PublicInput, training: str, config: Config):
        if not isinstance(public, PublicInput):
            raise TypeError("search accepts public input only")
        if public.role != "development":
            raise ValueError("reserved evaluation input cannot drive search")
        config.validate()
        if (config.spacing == "preserve") != (public.spacing == "preserve"):
            raise ValueError("search/input spacing mismatch")
        self.public, self.training, self.config = public, training, config
        lm = LanguageModel(training, config.order)
        self.units = inventory(lm, config)
        self.codes = candidate_codes(public.ciphertext, config) if config.family != "glyph" else []
        self.rngs, self.chains = [], []
        for i in range(config.restarts):
            rng = random.Random(stream_seed(config.seed, str(i), "search"))
            self.chains.append({"key": initial_key(public.ciphertext, lm, rng, i),
                                "loss": None, "step": 0})
            self.rngs.append(rng)
        self.cursor = 0
        self.pending = []

    def identity(self):
        return {"strategy": "synchronous-annealing-v1", "config": asdict(self.config),
                "public": asdict(self.public), "training_hash": fingerprint(self.training)}

    def propose(self, limit):
        if self.pending:
            raise RuntimeError("observe the pending batch first")
        if limit < 1:
            return []
        for _ in range(len(self.chains)):
            if len(self.pending) >= limit:
                break
            index = self.cursor
            self.cursor = (self.cursor + 1) % len(self.chains)
            chain = self.chains[index]
            if chain["step"] > self.config.steps:
                continue
            key = chain["key"] if chain["step"] == 0 else mutate(
                chain["key"], self.codes, self.units, self.config, self.rngs[index])
            candidate = Candidate.create("search-key-v1", key=key)
            self.pending.append((index, candidate))
        return [candidate for _, candidate in self.pending]

    def observe(self, results):
        if len(results) != len(self.pending):
            raise ValueError("feedback batch mismatch")
        for (index, candidate), result in zip(self.pending, results):
            chain = self.chains[index]
            loss = result.loss
            temperature = self.config.temperature_start * (
                self.config.temperature_end / self.config.temperature_start) ** (
                    max(0, chain["step"] - 1) / max(1, self.config.steps - 1))
            # Legacy acceptance is in total bits, not normalized loss.
            score = loss * result.denominator if loss is not None else None
            accept = score is not None and (chain["loss"] is None or score <= chain["loss"] or
                self.rngs[index].random() < 2 ** (-(score - chain["loss"]) / temperature))
            if accept:
                chain["key"], chain["loss"] = candidate.data["key"], score
            chain["step"] += 1
        self.pending = []

    def diagnostics(self):
        return {"chain_final_total_costs": [chain["loss"] for chain in self.chains],
                "note": "Final states, not per-chain optima or calibrated evidence."}

    def snapshot(self):
        if self.pending:
            raise RuntimeError("checkpoint only after feedback")
        import json
        return json.loads(canonical({"schema": 1, "identity": fingerprint(self.identity()),
            "chains": self.chains, "rngs": [rng.getstate() for rng in self.rngs],
            "cursor": self.cursor}))

    def restore(self, state):
        if state.get("schema") != 1 or state.get("identity") != fingerprint(self.identity()):
            raise ValueError("incompatible search checkpoint")
        if len(state["chains"]) != len(self.chains) or len(state["rngs"]) != len(self.rngs):
            raise ValueError("invalid chain count")
        self.chains, self.cursor = state["chains"], state["cursor"]
        self.pending = []
        for rng, saved in zip(self.rngs, state["rngs"]):
            rng.setstate(tuples(saved))


class PageChoiceSearch:
    """Lazy mixed-radix enumeration; no allocation of the exponential space."""
    def __init__(self, page_ids: tuple[str, ...], table_count=6):
        if not page_ids or len(set(page_ids)) != len(page_ids) or table_count < 1:
            raise ValueError("invalid page choice space")
        self.page_ids, self.table_count = page_ids, table_count
        self.cursor = 0

    def identity(self):
        return {"strategy": "page-enumeration-v1", "pages": self.page_ids,
                "table_count": self.table_count}

    def propose(self, limit):
        result = []
        for index in range(self.cursor, min(self.cursor + limit, self.table_count ** len(self.page_ids))):
            value, choices = index, []
            for _ in self.page_ids:
                choices.append(value % self.table_count)
                value //= self.table_count
            result.append(Candidate.create("page-choice-v1", choices=list(reversed(choices))))
        self.cursor += len(result)
        return result

    def observe(self, results):
        pass

    def snapshot(self):
        return {"schema": 1, "identity": fingerprint(self.identity()), "cursor": self.cursor}

    def restore(self, state):
        if state.get("schema") != 1 or state["identity"] != fingerprint(self.identity()):
            raise ValueError("incompatible enumeration checkpoint")
        if not 0 <= state["cursor"] <= self.table_count ** len(self.page_ids):
            raise ValueError("invalid enumeration cursor")
        self.cursor = state["cursor"]
