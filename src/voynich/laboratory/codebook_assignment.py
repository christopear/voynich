"""Codeword assignment and variant-choice mechanisms on a fixed word-shape model (stages 32 onward)."""
from __future__ import annotations

import numpy as np

from voynich.laboratory.structured_codes import WordCodebook
from voynich.laboratory.word_shapes import model_codebook


def ranked_codebook(vocabulary, frequencies, model, seed):
    """Stage-31 string set for this seed, assigned by rank: frequent words get probable strings."""
    base, draws = model_codebook(vocabulary, model, seed)
    strings = sorted((c for codes in base.encode.values() for c in codes), key=lambda s: (-model.logprob(s), s))
    words = sorted(set(vocabulary), key=lambda w: (-frequencies[w], w))
    rng = np.random.default_rng(seed + 5000)
    mapping = {}
    for j, word in enumerate(words):
        pair = [strings[2*j], strings[2*j+1]]
        if rng.integers(2):
            pair.reverse()
        mapping[word] = pair
    return WordCodebook(mapping), draws


def page_encrypt(book, words, rows, rule, seed):
    """Stage 30/31 encryption: the rule sees only page boundaries."""
    return book.encrypt(words, [r['page'] for r in rows], rule, seed)
