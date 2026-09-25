"""Syllabic slot cipher: a labelled, non-Naibbe verbose homophonic test object.

Specification: COUPLED_CIPHER_PROTOCOL.md. One plaintext syllable becomes one
token `prefix + core + terminal`. Cores are unique per syllable and drawn from a
Voynich glyph Markov model. Homophones vary prefix and terminal. With beta > 0
the terminal is chosen by its affinity with the NEXT token's first glyph, using
Voynich end->initial ratios learned at ordinary spaces. The code book is
invertible by construction and every run is round-trip checked.

This is a designed test object for the §19 classifier, not a proposed Voynich
mechanism.
"""
from __future__ import annotations

import random
import re
import unicodedata
from dataclasses import dataclass

from voynich_core import eva_glyphs

PREFIXES = ("", "o", "qo", "y")
TERMINALS = ("", "y", "n", "l", "r", "m")
VOWELS = set("aeiouy")
BAD_START = ("q", "o", "y")
BAD_END = set("nlrmy")


def latin_words(text: str) -> list[str]:
    text = unicodedata.normalize("NFKD", text.lower()).replace("æ", "ae").replace("œ", "oe")
    return [w.replace("j", "i").replace("k", "c").replace("w", "uu") for w in re.findall(r"[a-z]+", text)]


def syllabify(word: str) -> list[str]:
    """Onset-maximizing split: the last consonant before a vowel opens the next syllable."""
    out, cur, i = [], "", 0
    while i < len(word):
        cur += word[i]
        if word[i] in VOWELS:
            j = i + 1
            while j < len(word) and word[j] not in VOWELS:
                j += 1
            if j < len(word):
                k = max(j - 1, i + 1)
                cur += word[i + 1:k]
                out.append(cur); cur = ""; i = k
                continue
        i += 1
    if cur:
        if out and not any(c in VOWELS for c in cur):
            out[-1] += cur
        else:
            out.append(cur)
    assert "".join(out) == word
    return out


def syllable_stream(text: str) -> list[str]:
    return [s for w in latin_words(text) for s in syllabify(w)]


@dataclass(frozen=True)
class Config:
    h: int          # homophone variants per syllable
    s: float        # variant weight skew: weight of rank r is r**-s
    beta: float     # edge-coupling strength on the terminal choice


class CodeBook:
    def __init__(self, units, training, config: Config, seed: int):
        rng = random.Random(seed)
        combos = [(p, t) for p in PREFIXES for t in TERMINALS]
        used, cores = set(), {}
        self.variants: dict[str, list[tuple[str, str, float]]] = {}
        self.decode: dict[str, str] = {}
        for unit in sorted(units):
            for _ in range(10000):
                core = training.fresh(rng)
                if (core and not core.startswith(BAD_START) and core[-1] not in BAD_END
                        and core not in cores.values()):
                    strings = {p + core + t for p, t in combos}
                    if not strings & used:
                        break
            else:
                raise RuntimeError(f"no core for {unit}")
            cores[unit] = core
            chosen = rng.sample(combos, config.h)
            weights = [(r + 1) ** -config.s for r in range(config.h)]
            self.variants[unit] = [(p, t, w) for (p, t), w in zip(chosen, weights)]
            for p, t, _ in self.variants[unit]:
                word = p + core + t
                assert word not in self.decode
                self.decode[word] = unit
            used |= {p + core + t for p, t in combos}   # reserve all combos: no cross-unit collisions
        self.cores = cores

    def word(self, unit, p, t):
        return p + self.cores[unit] + t


def encipher(units_seq, book: CodeBook, edge: dict, config: Config, seed: int) -> list[str]:
    """Two-pass choice: prefixes (hence initials) first, then coupled terminals."""
    rng = random.Random(seed)
    prefixes = []
    for u in units_seq:
        opts = book.variants[u]
        p = rng.choices(opts, weights=[w for *_, w in opts], k=1)[0][0]
        prefixes.append(p)
    firsts = [eva_glyphs(book.word(u, p, ""))[0] for u, p in zip(units_seq, prefixes)]
    out = []
    for i, (u, p) in enumerate(zip(units_seq, prefixes)):
        opts = [(t, w) for pp, t, w in book.variants[u] if pp == p]
        if config.beta and i + 1 < len(units_seq):
            nxt = firsts[i + 1]
            weights = [w * edge.get((eva_glyphs(book.word(u, p, t))[-1], nxt), 1.0) ** config.beta for t, w in opts]
        else:
            weights = [w for _, w in opts]
        t = rng.choices([t for t, _ in opts], weights=weights, k=1)[0]
        out.append(book.word(u, p, t))
    assert [book.decode[w] for w in out] == list(units_seq)
    return out
