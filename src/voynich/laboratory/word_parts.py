"""Two-part (prefix x suffix) product model of word forms, against a glyph chain (stage 38).

A Naibbe-shaped cipher writes most words as prefix(letter 1) + suffix(letter 2),
the two parts drawn independently given the letters. The product model here
treats every word of two or more glyphs as one prefix and one suffix drawn
independently, with the split point latent, and is fitted by EM. It has no
whole-word memory, so it can only predict a word through its parts.
"""
from __future__ import annotations

from collections import Counter
from functools import lru_cache
import math

import numpy as np

from voynich.laboratory.word_shapes import NGramModel
from voynich.voynich_core import eva_glyphs


@lru_cache(maxsize=None)
def glyphs(word):
    return tuple(eva_glyphs(word))


@lru_cache(maxsize=None)
def splits(word):
    g = glyphs(word)
    return tuple((''.join(g[:k]), ''.join(g[k:])) for k in range(1, len(g)))


class ProductModel:
    """P(word) = sum over split points of P_prefix(left) * P_suffix(right)."""

    def __init__(self, words, iterations=30):
        counts = Counter(w for w in words if len(glyphs(w)) >= 2)
        self.types = sorted(counts)
        self.n = sum(counts.values())
        resp = {w: np.full(len(splits(w)), 1/len(splits(w))) for w in self.types}
        for _ in range(iterations):
            prefix, suffix = Counter(), Counter()
            for w in self.types:
                for (p, s), r in zip(splits(w), resp[w]):
                    prefix[p] += counts[w]*r
                    suffix[s] += counts[w]*r
            self.prefix = {p: v/self.n for p, v in prefix.items() if v > 0}
            self.suffix = {s: v/self.n for s, v in suffix.items() if v > 0}
            for w in self.types:
                joint = np.array([self.prefix.get(p, 0.)*self.suffix.get(s, 0.) for p, s in splits(w)])
                resp[w] = joint/joint.sum()
        self.responsibility = resp

    def probability(self, word):
        return sum(self.prefix.get(p, 0.)*self.suffix.get(s, 0.) for p, s in splits(word))

    def best_split(self, word):
        options = splits(word)
        scores = [self.prefix.get(p, 0.)*self.suffix.get(s, 0.) for p, s in options]
        return options[int(np.argmax(scores))] if max(scores, default=0) > 0 else None

    def inventory(self):
        def effective(dist):
            return 2**(-sum(p*math.log2(p) for p in dist.values() if p > 0))
        return dict(prefixes=len(self.prefix), suffixes=len(self.suffix),
                    effective_prefixes=effective(self.prefix), effective_suffixes=effective(self.suffix),
                    top_prefixes=sorted(self.prefix.items(), key=lambda kv: -kv[1])[:25],
                    top_suffixes=sorted(self.suffix.items(), key=lambda kv: -kv[1])[:25])


def contrast(train, held, *, epsilon=.1, iterations=30):
    """Held-out comparison of the product model (with a small chain backoff) against the chain alone.

    Returns T, the mean log2 ratio per held-out token of two or more glyphs:
    positive when predicting a word through independent parts beats the chain.
    """
    product = ProductModel(train, iterations)
    chain = NGramModel(train, 2)
    seen = set(train)
    rows = []
    for w in held:
        if len(glyphs(w)) < 2:
            continue
        chain_p = 2**chain.logprob(w)
        prod_p = product.probability(w)
        rows.append((w in seen, math.log2(((1-epsilon)*prod_p + epsilon*chain_p)/chain_p), prod_p > 0))
    new = [r for r in rows if not r[0]]
    return dict(held_tokens=len(rows), new_type_tokens=len(new),
                T=float(np.mean([r[1] for r in rows])),
                T_new=float(np.mean([r[1] for r in new])) if new else None,
                coverage=float(np.mean([r[2] for r in rows])),
                coverage_new=float(np.mean([r[2] for r in new])) if new else None,
                inventory=product.inventory()), product, chain


def folds(groups, k=5):
    """Assign ordered group labels to k folds by alternation."""
    order = list(dict.fromkeys(groups))
    return {g: i % k for i, g in enumerate(order)}
