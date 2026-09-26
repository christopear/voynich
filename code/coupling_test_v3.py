"""Coupling-aware terminal-alternation test, version 3: cross-fitted neighbour classes.

Specification: COUPLING_TEST_V3_PROTOCOL.md. Version 2 learned neighbour classes
from the same text that contains the tested pairs, which leaks T into X. Here
classes are learned on pages outside a fold and applied only to occurrences on
pages inside it, so X is independent of the tested T under H_coupled.
Statistic, null and references are reused from coupling_test_v2.
"""
from __future__ import annotations

import random
from collections import defaultdict

import coupling_test_v2 as v2
from voynich_core import eva_glyphs

SEED = 20260925
FOLDS = 5


def page_folds(pages, k: int = FOLDS, seed: int = SEED) -> dict:
    ps = sorted(set(pages))
    random.Random(seed).shuffle(ps)
    return {p: i % k for i, p in enumerate(ps)}


class CrossFitOccurrences:
    """Occurrences whose neighbour classes come from a model fitted without their own fold.

    `paged_lines` is a list of (page, tokens) with None for unreadable tokens.
    `arm` is "k<N>" (cross-fitted k-means classes) or "top30" (identity, no fitting).
    records(w) is call-compatible with coupling_test_v2 (extra arguments ignored).
    """

    def __init__(self, paged_lines, arm: str, folds: dict | None = None, *, k_folds: int = FOLDS, seed: int = SEED):
        self.folds = folds or page_folds([p for p, _ in paged_lines], k_folds, seed)
        self.raw: dict[str, list[tuple]] = defaultdict(list)
        for page, ln in paged_lines:
            fold = self.folds[page]
            for i, w in enumerate(ln):
                if not w:
                    continue
                prev = ln[i - 1] if i else "^"
                nxt = ln[i + 1] if i + 1 < len(ln) else "$"
                if prev is None or nxt is None:
                    continue
                gp = eva_glyphs(prev) if prev != "^" else ["^"]
                gn = eva_glyphs(nxt) if nxt != "$" else ["$"]
                self.raw[w].append((gp[-1], gn[0], "".join(gn[:2]), prev, nxt, fold))
        self.freq = {w: len(r) for w, r in self.raw.items()}
        lines = [ln for _, ln in paged_lines]
        if arm == "top30":
            ident = v2.identity_map(lines)
            self.maps = {f: ident for f in set(self.folds.values())}
            self.default = "*"
        else:
            k = int(arm[1:])
            self.maps = {f: v2.neighbour_classes([ln for p, ln in paged_lines if self.folds[p] != f], k, seed=seed)
                         for f in sorted(set(self.folds.values()))}
            self.default = "rare"

    def records(self, w: str, *_ignored) -> list[tuple]:
        out = []
        for pf, ni, ni2, p, n, fold in self.raw[w]:
            m = self.maps[fold]
            x = lambda t: t if t in ("^", "$") else m.get(t, self.default)
            out.append((pf, ni, ni2, x(p), x(n)))
        return out


def disjoint_subsets(rows, size: int, n_subsets: int, seed: int = SEED) -> list[list[dict]]:
    """Member-disjoint subsets of pairs, each drawn within a single seed (protocol §3)."""
    by_seed = defaultdict(list)
    for r in rows:
        by_seed[r["seed"]].append(r)
    rng = random.Random(seed)
    seeds = sorted(by_seed)
    out, attempts = [], 0
    while len(out) < n_subsets and attempts < 20 * n_subsets:
        attempts += 1
        pool = by_seed[rng.choice(seeds)][:]
        rng.shuffle(pool)
        used, sub = set(), []
        for r in pool:
            if r["a"] in used or r["b"] in used:
                continue
            sub.append(r); used |= {r["a"], r["b"]}
            if len(sub) == size:
                out.append(sub)
                break
    return out
