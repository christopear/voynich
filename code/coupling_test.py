"""Coupling-aware test for same-stem terminal alternations (COUPLING_TEST_PROTOCOL.md).

For a pair A = stem+x, B = stem+y, T marks which member occurred. Under
edge-conditioned homophony, T is independent of the neighbouring token
identities once the adjacent boundary glyphs Z are fixed. The statistic
S = I(T; X_left | Z) + I(T; X_right | Z) is compared with a null that permutes T
within Z strata.
"""
from __future__ import annotations

import random
from collections import Counter, defaultdict

import numpy as np

from voynich_core import eva_glyphs

TOP_K = 30
REPS = 300
SEED = 20260925


class Occurrences:
    """Per-type occurrence records from token lines (None = unreadable gap)."""

    def __init__(self, lines, top_k: int = TOP_K):
        freq = Counter(w for ln in lines for w in ln if w)
        top = {w for w, _ in freq.most_common(top_k)}
        self.records: dict[str, list[tuple]] = defaultdict(list)
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
                self.records[w].append((
                    gp[-1], gn[0], "".join(gn[:2]),
                    prev if prev in top or prev == "^" else "*",
                    nxt if nxt in top or nxt == "$" else "*"))
        self.freq = {w: len(r) for w, r in self.records.items()}


def stem_final(word: str):
    g = eva_glyphs(word)
    return ("".join(g[:-1]), g[-1]) if len(g) >= 2 else (None, None)


def same_stem_pairs(occ: Occurrences, finals, min_occ: int = 20):
    by_stem = defaultdict(list)
    for w, n in occ.freq.items():
        stem, fin = stem_final(w)
        if stem and fin in finals and n >= min_occ:
            by_stem[stem].append(w)
    return sorted((a, b) for ws in by_stem.values() for i, a in enumerate(sorted(ws)) for b in sorted(ws)[i + 1:])


def _codes(values):
    index = {}
    return np.array([index.setdefault(v, len(index)) for v in values]), len(index)


def _cmi(t, x, z, nx, nz):
    """Plug-in I(T; X | Z) in bits for binary t."""
    n = len(t)
    key = (z * 2 + t) * nx + x
    nzxt = np.bincount(key, minlength=nz * 2 * nx).reshape(nz, 2, nx)
    nzt = nzxt.sum(2); nzx = nzxt.sum(1); nzz = nzt.sum(1)
    nz_i, t_i, x_i = np.nonzero(nzxt)
    c = nzxt[nz_i, t_i, x_i]
    return float((c * np.log2(c * nzz[nz_i] / (nzt[nz_i, t_i] * nzx[nz_i, x_i]))).sum() / n)


def _permute_within(t, z, rng):
    order = np.lexsort((rng.random(len(t)), z))
    out = t.copy()
    by = np.argsort(z, kind="stable")
    out[by] = t[order]
    return out


def residual_test(rec_a, rec_b, *, z_mode="one", sides="both", reps=REPS, seed=SEED) -> dict:
    recs = rec_a + rec_b
    t = np.array([0] * len(rec_a) + [1] * len(rec_b))
    zi = (lambda r: (r[0], r[1])) if z_mode == "one" else (lambda r: (r[0], r[2]))
    z, nz = _codes([zi(r) for r in recs])
    xl, nl = _codes([r[3] for r in recs]); xr, nr = _codes([r[4] for r in recs])

    def stat(tt):
        s = 0.0
        if sides in ("both", "left"):
            s += _cmi(tt, xl, z, nl, nz)
        if sides in ("both", "right"):
            s += _cmi(tt, xr, z, nr, nz)
        return s
    obs = stat(t)
    rng = np.random.default_rng(seed)
    null = np.array([stat(_permute_within(t, z, rng)) for _ in range(reps)])
    sd = float(null.std())
    return {"n_a": len(rec_a), "n_b": len(rec_b), "obs": obs, "null_mean": float(null.mean()),
            "excess": obs - float(null.mean()), "z": (obs - float(null.mean())) / sd if sd > 0 else 0.0,
            "p": float((1 + (null >= obs - 1e-12).sum()) / (reps + 1))}


def naive_test(rec_a, rec_b, reps=REPS, seed=SEED) -> dict:
    """I(T; next initial glyph), unconditional permutation: the handoff's r/l logic."""
    t = np.array([0] * len(rec_a) + [1] * len(rec_b))
    x, nx = _codes([r[1] for r in rec_a + rec_b]); z = np.zeros(len(t), dtype=int)
    obs = _cmi(t, x, z, nx, 1)
    rng = np.random.default_rng(seed)
    null = np.array([_cmi(rng.permutation(t), x, z, nx, 1) for _ in range(reps)])
    return {"obs": obs, "excess": obs - float(null.mean()), "p": float((1 + (null >= obs - 1e-12).sum()) / (reps + 1))}


def matched_reference(occ: Occurrences, a: str, b: str, *, n_ref=20, seed=SEED, min_occ=20, **kw) -> list[dict]:
    """Random pairs of distinct-stem types matched to A and B on frequency and final glyph."""
    stem_ab = stem_final(a)[0]
    fa, fb = occ.freq[a], occ.freq[b]
    fin_a, fin_b = stem_final(a)[1], stem_final(b)[1]

    def pool(f, fin):
        return sorted(w for w, n in occ.freq.items()
                      if n >= min_occ and 0.8 * f <= n <= 1.25 * f and stem_final(w)[1] == fin
                      and stem_final(w)[0] not in (None, stem_ab))
    pa, pb = pool(fa, fin_a), pool(fb, fin_b)
    rng = random.Random(f"{seed}:{a}:{b}")
    out, tries = [], 0
    while len(out) < n_ref and pa and pb and tries < 50 * n_ref:
        tries += 1
        x, y = rng.choice(pa), rng.choice(pb)
        if x == y or stem_final(x)[0] == stem_final(y)[0]:
            continue
        out.append({"x": x, "y": y, **residual_test(occ.records[x], occ.records[y], seed=seed, **kw)})
    return out


def percentile(excess: float, reference: list[dict]):
    if not reference:
        return None
    return 100.0 * sum(r["excess"] <= excess for r in reference) / len(reference)


def score_pair(occ: Occurrences, a: str, b: str, *, n_ref=20, **kw) -> dict:
    res = residual_test(occ.records[a], occ.records[b], **kw)
    ref = matched_reference(occ, a, b, n_ref=n_ref, **kw) if n_ref else []
    return {"a": a, "b": b, **res, "naive": naive_test(occ.records[a], occ.records[b]),
            "n_ref": len(ref), "ref_median_excess": float(np.median([r["excess"] for r in ref])) if ref else None,
            "ref_percentile": percentile(res["excess"], ref)}


def category(r: dict):
    if r["ref_percentile"] is None:
        return "no_reference"
    if r["p"] >= 0.05 and r["ref_percentile"] <= 25:
        return "coupled_compatible"
    if r["p"] < 0.05 and r["ref_percentile"] >= 50:
        return "distinct_like"
    return "undetermined"
