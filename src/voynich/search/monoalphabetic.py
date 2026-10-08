"""Family-constrained search: injective character substitutions only."""
from dataclasses import asdict
from voynich.search.strategies import AnnealingSearch, Candidate
from voynich.laboratory.manifest import fingerprint


class MonoalphabeticSearch(AnnealingSearch):
    def __init__(self, public, training, config):
        if config.family != "glyph" or config.spacing != "preserve":
            raise ValueError("injective search supports preserved-space glyph substitution")
        if len(set(public.ciphertext) - {" "}) > 26:
            raise ValueError("more than 26 observed symbols cannot be injective onto a-z")
        super().__init__(public, training, config)

    def identity(self):
        return {**super().identity(), "strategy": "injective-annealing-v1"}

    def propose(self, limit):
        if self.pending:
            raise RuntimeError("feedback required before proposing")
        if limit < 1:
            return []
        for _ in self.chains:
            if len(self.pending) >= limit:
                break
            index = self.cursor
            self.cursor = (self.cursor + 1) % len(self.chains)
            chain = self.chains[index]
            if chain["step"] > self.config.steps:
                continue
            key = dict(chain["key"])
            if chain["step"]:
                rng = self.rngs[index]
                unused = sorted(set(self.units) - set(key.values()))
                if unused and (len(key) < 2 or rng.random() < .2):
                    key[rng.choice(list(key))] = rng.choice(unused)
                elif len(key) > 1:
                    a,b = rng.sample(list(key),2)
                    key[a],key[b] = key[b],key[a]
            candidate = Candidate.create("search-key-v1",key=key)
            self.pending.append((index,candidate))
        return [c for _,c in self.pending]
