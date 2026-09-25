"""Coupling-aware terminal-alternation test, version 2 (COUPLING_TEST_V2_PROTOCOL.md).

Changes from coupling_test.py: neighbours are represented by distributional
classes (PPMI -> SVD -> k-means) that survive homophony, instead of top-30
identities; per-pair null draws are kept so that a pooled class-level test can
be formed. Version 1 is left untouched for reproducibility.
"""
from __future__ import annotations

import random
from collections import Counter, defaultdict

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import svds
from sklearn.cluster import KMeans

import coupling_test as ct
from voynich_core import eva_glyphs

SEED = 20260925
REPS = 300


# ---------------------------------------------------------------------------
# Neighbour representations
# ---------------------------------------------------------------------------

def neighbour_classes(lines, k: int, *, dim: int = 50, top_ctx: int = 2000, min_freq: int = 2, seed: int = SEED) -> dict:
    """Map word -> class label from its left/right neighbour distribution."""
    freq = Counter(w for ln in lines for w in ln if w)
    vocab = sorted(w for w, n in freq.items() if n >= min_freq)
    vidx = {w: i for i, w in enumerate(vocab)}
    ctx = [w for w, _ in freq.most_common(top_ctx)] + ["^", "$", "*"]
    cidx = {w: i for i, w in enumerate(ctx)}
    width = len(ctx)
    rows, cols = [], []
    for ln in lines:
        for i, w in enumerate(ln):
            r = vidx.get(w)
            if r is None:
                continue
            left = ln[i - 1] if i else "^"
            right = ln[i + 1] if i + 1 < len(ln) else "$"
            if left is not None:
                rows.append(r); cols.append(cidx.get(left, cidx["*"]))
            if right is not None:
                rows.append(r); cols.append(width + cidx.get(right, cidx["*"]))
    M = csr_matrix((np.ones(len(rows)), (rows, cols)), shape=(len(vocab), 2 * width))
    M.sum_duplicates()
    total = M.sum(); row = np.asarray(M.sum(1)).ravel(); col = np.asarray(M.sum(0)).ravel()
    coo = M.tocoo()
    pmi = np.log(coo.data * total / (row[coo.row] * col[coo.col]))
    keep = pmi > 0
    P = csr_matrix((pmi[keep], (coo.row[keep], coo.col[keep])), shape=M.shape)
    d = min(dim, min(P.shape) - 1)
    v0 = np.random.default_rng(seed).random(min(P.shape))
    U, S, _ = svds(P, k=d, v0=v0)
    E = U * S
    E /= np.maximum(np.linalg.norm(E, axis=1, keepdims=True), 1e-12)
    labels = KMeans(n_clusters=min(k, len(vocab)), n_init=10, random_state=seed).fit_predict(E)
    return {w: f"c{int(c)}" for w, c in zip(vocab, labels)}


def identity_map(lines, top: int = ct.TOP_K) -> dict:
    freq = Counter(w for ln in lines for w in ln if w)
    return {w: w for w, _ in freq.most_common(top)}


class Occurrences:
    """Raw per-type occurrences; neighbour words are mapped through an x-map later."""

    def __init__(self, lines):
        self.raw: dict[str, list[tuple]] = defaultdict(list)
        for ln in lines:
            for i, w in enumerate(ln):
                if not w:
                    continue
                prev = ln[i - 1] if i else "^"
                nxt = ln[i + 1] if i + 1 < len(ln) else "$"
                if prev is None or nxt is None:
                    continue
                gp = eva_glyphs(prev) if prev != "^" else ["^"]
                gn = eva_glyphs(nxt) if nxt != "$" else ["$"]
                self.raw[w].append((gp[-1], gn[0], "".join(gn[:2]), prev, nxt))
        self.freq = {w: len(r) for w, r in self.raw.items()}

    def records(self, w: str, xmap: dict, default: str) -> list[tuple]:
        def x(n):
            return n if n in ("^", "$") else xmap.get(n, default)
        return [(pf, ni, ni2, x(p), x(n)) for pf, ni, ni2, p, n in self.raw[w]]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def residual_test(rec_a, rec_b, *, z_mode="one", reps=REPS, seed=SEED) -> dict:
    """Version-1 statistic, additionally returning standardized null draws for pooling."""
    recs = rec_a + rec_b
    t = np.array([0] * len(rec_a) + [1] * len(rec_b))
    zi = (lambda r: (r[0], r[1])) if z_mode == "one" else (lambda r: (r[0], r[2]))
    z, nz = ct._codes([zi(r) for r in recs])
    xl, nl = ct._codes([r[3] for r in recs]); xr, nr = ct._codes([r[4] for r in recs])
    stat = lambda tt: ct._cmi(tt, xl, z, nl, nz) + ct._cmi(tt, xr, z, nr, nz)
    obs = stat(t)
    rng = np.random.default_rng(seed)
    null = np.array([stat(ct._permute_within(t, z, rng)) for _ in range(reps)])
    mean, sd = float(null.mean()), float(null.std())
    sd = sd if sd > 0 else 1.0
    return {"n_a": len(rec_a), "n_b": len(rec_b), "obs": obs, "null_mean": mean, "excess": obs - mean,
            "z": (obs - mean) / sd, "p": float((1 + (null >= obs - 1e-12).sum()) / (reps + 1)),
            "null_z": ((null - mean) / sd).astype(np.float32)}


def pooled(results: list[dict]) -> dict:
    """Mean-z pooled test; pairs permuted independently, draws aligned by index."""
    obs = float(np.mean([r["z"] for r in results]))
    null = np.mean(np.stack([r["null_z"] for r in results]), axis=0)
    return {"pairs": len(results), "mean_z": obs, "p": float((1 + (null >= obs - 1e-12).sum()) / (len(null) + 1))}


def matched_reference(occ: Occurrences, xmap, default, a, b, *, n_ref=20, min_occ=20, seed=SEED, reps=REPS, keep_null=False):
    stem_ab = ct.stem_final(a)[0]
    fin_a, fin_b = ct.stem_final(a)[1], ct.stem_final(b)[1]

    def pool(f, fin):
        return sorted(w for w, n in occ.freq.items()
                      if n >= min_occ and 0.8 * f <= n <= 1.25 * f and ct.stem_final(w)[1] == fin
                      and ct.stem_final(w)[0] not in (None, stem_ab))
    pa, pb = pool(occ.freq[a], fin_a), pool(occ.freq[b], fin_b)
    rng = random.Random(f"{seed}:{a}:{b}")
    out, tries = [], 0
    while len(out) < n_ref and pa and pb and tries < 50 * n_ref:
        tries += 1
        x, y = rng.choice(pa), rng.choice(pb)
        if x == y or ct.stem_final(x)[0] == ct.stem_final(y)[0]:
            continue
        r = residual_test(occ.records(x, xmap, default), occ.records(y, xmap, default), seed=seed, reps=reps)
        if not keep_null:
            r.pop("null_z")
        out.append({"x": x, "y": y, **r})
    return out


def score_pair(occ: Occurrences, xmap, default, a, b, *, n_ref=20, reps=REPS, keep_ref_null=False) -> dict:
    ra, rb = occ.records(a, xmap, default), occ.records(b, xmap, default)
    res = residual_test(ra, rb, reps=reps)
    refs = matched_reference(occ, xmap, default, a, b, n_ref=n_ref, reps=reps, keep_null=keep_ref_null) if n_ref else []
    return {"a": a, "b": b, **res, "naive": ct.naive_test(ra, rb, reps=reps),
            "n_ref": len(refs), "ref_percentile": ct.percentile(res["excess"], refs), "refs": refs}
