"""Glyph-variant test on v101 (V101_PROTOCOL.md, Part A).

For each eligible set of v101 symbols that EVA merges, asks whether the variant
choice is explained by position, scribe, location or neighbouring glyphs, or
carries residual word-level information. Calibrated first on synthetic
variants imposed on single-symbol classes.

Run: OPENBLAS_NUM_THREADS=1 uv run --locked python code/20_v101_variant_test.py [--workers 4]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import warnings
from collections import Counter, defaultdict
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from scipy import sparse
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression

import v101_data as vd

OUT = vd.OUT
SEED = 20260926
BOOT = 2000
EPS = 1e-3
FAMILIES = ("POS", "SCRIBE", "LOC", "NB")
MIN_MEMBER, MIN_SECOND, MIN_PURITY, MIN_ALIGNED = 20, 30, 0.80, 10
CAL_BASES = ("o", "a", "c", "1", "e")
CAL_SIZES = (300, 1000, 5000)
CAL_SEEDS = (1, 2, 3, 4)
CONTROLS = ("NULL", "POS", "SCRIBE", "NB", "WIDE", "LETTER")
EXPECTED = {"POS": "positional", "SCRIBE": "scribal", "NB": "contextual", "NULL": "unexplained"}


# ---------------------------------------------------------------------------
# Occurrences and features
# ---------------------------------------------------------------------------

def occurrences(lines_full, lines_coll, symbols: set[str] | None, classes: set[str] | None = None):
    """One row per occurrence of a target symbol (or of a canonical class) in a clean word."""
    rows = []
    for lf, lc in zip(lines_full, lines_coll):
        n = len(lf["words"])
        for wi, (wf, wc) in enumerate(zip(lf["words"], lc["words"])):
            if not wf["clean"]:
                continue
            for k, (sf, sc) in enumerate(zip(wf["word"], wc["word"])):
                if (symbols is not None and sf in symbols) or (classes is not None and sc in classes):
                    rows.append(dict(sym=sf, cls=sc, full=wf["word"], coll=wc["word"], k=k, wi=wi, nw=n,
                                     pfl=lf["paragraph_start"], pll=lf["paragraph_end"],
                                     folio=lf["folio"], fold=lf["fold"],
                                     hand=lf["meta"].get("H", "?"), lang=lf["meta"].get("L", "?"),
                                     quire=lf["meta"].get("Q", "?"), section=lf["meta"].get("I", "?")))
    return rows


def ctx(row, arm):
    w = row["full"] if arm == "full" else row["coll"]
    k = row["k"]
    w = w[:k] + "_" + w[k + 1:]
    at = lambda i, lo, hi: w[i] if 0 <= i < len(w) else (lo if i < 0 else hi)
    return w, at(k - 1, "^", "$"), at(k + 1, "^", "$"), at(k - 2, "^^", "$$"), at(k + 2, "^^", "$$")


def family_features(row, fam, arm):
    if fam == "POS":
        wi, nw, k, L = row["wi"], row["nw"], row["k"], len(row["full"])
        wpos = "only" if nw == 1 else "first" if wi == 0 else "last" if wi == nw - 1 else "mid"
        gpos = "sole" if L == 1 else "init" if k == 0 else "final" if k == L - 1 else "med"
        pfw = row["pfl"] and wi == 0
        return {"wpos": wpos, "gpos": gpos, "wg": wpos + "/" + gpos, "pfl": float(row["pfl"]),
                "pll": float(row["pll"]), "pfw": float(pfw), "cap_line": float(wi == 0 and k == 0),
                "cap_para": float(pfw and k == 0)}
    if fam == "SCRIBE":
        return {"hand": row["hand"], "lang": row["lang"], "hl": row["hand"] + "/" + row["lang"]}
    if fam == "LOC":
        return {"quire": row["quire"], "section": row["section"]}
    _, p1, n1, p2, n2 = ctx(row, arm)
    if fam == "NB":
        return {"prev": p1, "next": n1, "pn": p1 + "|" + n1}
    if fam == "WIDE":
        return {"prev2": p2, "next2": n2}
    raise ValueError(fam)


def res_key(row, arm):
    return ctx(row, arm)[0] + "#" + str(row["k"])


def target_encode(train_keys, train_y, apply_keys, K, prior):
    cnt = defaultdict(lambda: np.zeros(K))
    for key, y in zip(train_keys, train_y):
        cnt[key][y] += 1
    out = np.zeros((len(apply_keys), K + 1))
    for i, key in enumerate(apply_keys):
        c = cnt.get(key)
        c = np.zeros(K) if c is None else c
        n = c.sum()
        out[i, :K] = np.log((c + 2 * prior) / (n + 2))
        out[i, K] = np.log1p(n)
    return out


def res_matrix(keys, y, folio, train_idx, test_idx, K):
    """Out-of-fold target encoding: inner folio folds for training rows."""
    prior = np.bincount(y[train_idx], minlength=K) / len(train_idx)
    prior = np.maximum(prior, 1e-6); prior = prior / prior.sum()
    folios = sorted({folio[i] for i in train_idx})
    random.Random(SEED).shuffle(folios)
    inner = {f: j % 5 for j, f in enumerate(folios)}
    Xtr = np.zeros((len(train_idx), K + 1))
    tr_inner = np.array([inner[folio[i]] for i in train_idx])
    for f in range(5):
        a = train_idx[tr_inner != f]; b = np.where(tr_inner == f)[0]
        if len(b):
            Xtr[b] = target_encode([keys[i] for i in a], y[a], [keys[train_idx[j]] for j in b], K, prior)
    Xte = target_encode([keys[i] for i in train_idx], y[train_idx], [keys[i] for i in test_idx], K, prior)
    return Xtr, Xte


# ---------------------------------------------------------------------------
# Cross-validated models
# ---------------------------------------------------------------------------

MODELS = {
    "M0": (), "POS": ("POS",), "SCRIBE": ("SCRIBE",), "LOC": ("LOC",), "NB": ("NB",),
    "CTRL": FAMILIES, **{f"CTRL-{f}": tuple(x for x in FAMILIES if x != f) for f in FAMILIES},
    "CTRL+RES": FAMILIES + ("RES",), "CTRL+WIDE": FAMILIES + ("WIDE",),
    "CTRL+WIDE+RES": FAMILIES + ("WIDE", "RES"),
}


def cv_losses(rows, y, K, arm):
    """Held-out log-loss (bits) per occurrence for every model."""
    n = len(rows)
    fold = np.array([r["fold"] for r in rows])
    folio = [r["folio"] for r in rows]
    fam = {f: [family_features(r, f, arm) for r in rows] for f in FAMILIES + ("WIDE",)}
    keys = [res_key(r, arm) for r in rows]
    losses = {m: np.full(n, np.nan) for m in MODELS}
    for f in range(5):
        tr = np.where(fold != f)[0]; te = np.where(fold == f)[0]
        if not len(te) or len(set(y[tr])) < 2:
            continue
        Rtr = Rte = None
        for name, fams in MODELS.items():
            if not fams:
                prior = (np.bincount(y[tr], minlength=K) + 0.5) / (len(tr) + 0.5 * K)
                p = np.tile(prior, (len(te), 1))
            else:
                dfams = [x for x in fams if x != "RES"]
                if dfams:
                    dv = DictVectorizer()
                    Xtr = dv.fit_transform([{f"{g}:{a}": b for g in dfams for a, b in fam[g][i].items()} for i in tr])
                    Xte = dv.transform([{f"{g}:{a}": b for g in dfams for a, b in fam[g][i].items()} for i in te])
                else:
                    Xtr = sparse.csr_matrix((len(tr), 0)); Xte = sparse.csr_matrix((len(te), 0))
                if "RES" in fams:
                    if Rtr is None:
                        Rtr, Rte = res_matrix(keys, y, folio, tr, te, K)
                    Xtr = sparse.hstack([Xtr, sparse.csr_matrix(Rtr)]).tocsr()
                    Xte = sparse.hstack([Xte, sparse.csr_matrix(Rte)]).tocsr()
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    model = LogisticRegression(C=1, max_iter=2000).fit(Xtr, y[tr])
                pp = model.predict_proba(Xte)
                p = np.zeros((len(te), K))
                p[:, model.classes_] = pp
            p = (1 - EPS) * p + EPS / K
            losses[name][te] = -np.log2(p[np.arange(len(te)), y[te]])
    return losses


def boot_ci(diff, clusters, rng_seed=SEED):
    ok = ~np.isnan(diff)
    diff = diff[ok]; clusters = np.asarray(clusters)[ok]
    ids = sorted(set(clusters)); idx = {c: i for i, c in enumerate(ids)}
    ci = np.array([idx[c] for c in clusters])
    s = np.bincount(ci, weights=diff, minlength=len(ids)); m = np.bincount(ci, minlength=len(ids))
    rng = np.random.default_rng(rng_seed)
    draw = rng.integers(len(ids), size=(BOOT, len(ids)))
    est = s[draw].sum(1) / np.maximum(m[draw].sum(1), 1)
    return float(diff.mean()), [float(x) for x in np.quantile(est, [0.025, 0.975])]


def evaluate(rows, y, K, arm):
    L = cv_losses(rows, y, K, arm)
    folio = [r["folio"] for r in rows]
    mean = {m: float(np.nanmean(v)) for m, v in L.items()}
    out = {"n": len(rows), "loss": mean}
    out["unique"] = {f: boot_ci(L[f"CTRL-{f}"] - L["CTRL"], folio) for f in FAMILIES}
    out["alone"] = {f: boot_ci(L["M0"] - L[f], folio) for f in FAMILIES}
    out["R"] = boot_ci(L["CTRL"] - L["CTRL+RES"], folio)
    out["R_w"] = boot_ci(L["CTRL+WIDE"] - L["CTRL+WIDE+RES"], folio)
    out["E"] = (mean["M0"] - mean["CTRL"]) / mean["M0"] if mean["M0"] > 0 else None
    out["label"] = label(out)
    return out, L


def label(res):
    R, Rw = res["R"], res["R_w"]
    letter = R[0] >= 0.01 and R[1][0] > 0 and Rw[0] >= 0.01 and Rw[1][0] > 0
    contrib = {f: g for f, (g, ci) in res["unique"].items() if g >= 0.005 and ci[0] > 0}
    top = max(contrib, key=contrib.get) if contrib else None
    name = {"POS": "positional", "SCRIBE": "scribal", "NB": "contextual", "LOC": "codicological", None: "unexplained"}[top]
    return {"letter_like": letter, "primary": "letter-like" if letter else name,
            "attribution": name, "contributing": sorted(contrib)}


# ---------------------------------------------------------------------------
# Calibration
# ---------------------------------------------------------------------------

def synthetic_labels(rows, control, seed, commons):
    rng = random.Random(seed * 7919 + CONTROLS.index(control))
    out = []
    key_prop = {}
    for r in rows:
        _, p1, n1, p2, n2 = ctx(r, "collapsed")
        if control == "NULL":
            p = 0.2
        elif control == "POS":
            p = 0.5 if r["wi"] == 0 else 0.15
        elif control == "SCRIBE":
            p = 0.3 if r["hand"] == "1" else 0.1
        elif control == "NB":
            p = 0.4 if n1 == commons["next"] else 0.1
        elif control == "WIDE":
            p = 0.4 if n2 == commons["next2"] else 0.1
        else:
            key = res_key(r, "collapsed")
            if key not in key_prop:
                key_prop[key] = 0.6 if rng.random() < 0.25 else 0.05
            p = key_prop[key]
        out.append(int(rng.random() < p))
    return np.array(out)


def cal_job(args):
    base, control, size, seed = args
    rows = CAL_ROWS[base]
    rng = random.Random(1000 * seed + size)
    sub = rows if len(rows) <= size else rng.sample(rows, size)
    # Most common real glyph (word-edge markers excluded) one and two positions to the right.
    edge = {"^", "$", "^^", "$$"}
    common = lambda j: Counter(x for x in (ctx(r, "collapsed")[j] for r in rows) if x not in edge).most_common(1)[0][0]
    commons = {"next": common(2), "next2": common(4)}
    y = synthetic_labels(sub, control, seed, commons)
    res, _ = evaluate(sub, y, 2, "collapsed")
    return dict(base=base, control=control, size=size, seed=seed, minority=float(y.mean()), **res)


def gates(cal):
    out = {}
    for size in CAL_SIZES:
        rate = lambda c, f: float(np.mean([f(r) for r in cal if r["control"] == c and r["size"] == size]))
        ll = lambda r: r["label"]["letter_like"]
        g = {"letter_like_rate": {c: rate(c, ll) for c in CONTROLS},
             "correct_attribution": {c: rate(c, lambda r, c=c: r["label"]["attribution"] == EXPECTED[c])
                                     for c in EXPECTED}}
        g["G1"] = all(g["letter_like_rate"][c] <= 0.10 for c in ("NULL", "POS", "SCRIBE", "NB"))
        g["G2"] = g["letter_like_rate"]["LETTER"] >= 0.80
        g["G3"] = all(g["correct_attribution"][c] >= 0.80 for c in ("POS", "SCRIBE", "NB"))
        g["G4"] = g["letter_like_rate"]["WIDE"] <= 0.20
        g["G5"] = g["correct_attribution"]["NULL"] >= 0.80
        g["residual_interpretable"] = g["G1"] and g["G2"] and g["G4"]
        g["attribution_interpretable"] = g["G3"] and g["G5"]
        out[str(size)] = g
    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def eligible_sets(mapping):
    S = mapping["symbols"]
    sets = {}
    for cls, members in mapping["merged_sets"].items():
        ok = [c for c in members if S[c]["count_text"] >= MIN_MEMBER and (S[c]["purity"] or 0) >= MIN_PURITY
              and S[c]["aligned"] >= MIN_ALIGNED]
        ok.sort(key=lambda c: -S[c]["count_text"])
        if len(ok) >= 2 and S[ok[1]]["count_text"] >= MIN_SECOND:
            sets[cls] = ok
    return sets


CAL_ROWS = {}


def init_worker(cal_rows):
    global CAL_ROWS
    CAL_ROWS = cal_rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    lines, mapping = vd.load_corpus()
    coll = vd.represent(lines, mapping["collapse_table"])
    sets = eligible_sets(mapping)
    print("eligible sets:", sets, flush=True)

    # Calibration.
    cal_rows = {b: occurrences(lines, coll, None, {b}) for b in CAL_BASES}
    jobs = [(b, c, n, s) for c in CONTROLS for n in CAL_SIZES for s in CAL_SEEDS for b in CAL_BASES]
    with Pool(args.workers, initializer=init_worker, initargs=(cal_rows,)) as pool:
        cal = []
        for i, r in enumerate(pool.imap_unordered(cal_job, jobs)):
            cal.append(r)
            if (i + 1) % 30 == 0:
                print(f"calibration {i + 1}/{len(jobs)}", flush=True)
    cal.sort(key=lambda r: (r["control"], r["size"], r["base"], r["seed"]))
    g = gates(cal)
    (OUT / "variant_calibration.json").write_text(json.dumps({"gates": g, "replicates": cal}, indent=1))
    print(json.dumps(g, indent=1), flush=True)

    # Voynich sets, both arms.
    results = {}
    for cls, members in sets.items():
        rows = occurrences(lines, coll, set(members))
        idx = {c: i for i, c in enumerate(members)}
        y = np.array([idx[r["sym"]] for r in rows])
        d = {"members": members, "counts": {c: int((y == i).sum()) for c, i in idx.items()}}
        Ls = {}
        for arm in ("collapsed", "full"):
            d[arm], Ls[arm] = evaluate(rows, y, len(members), arm)
        folio = [r["folio"] for r in rows]
        d["paired_full_vs_collapsed"] = {
            m: boot_ci(Ls["collapsed"][m] - Ls["full"][m], folio) for m in ("CTRL", "CTRL+RES", "CTRL+WIDE+RES")}
        size = max([s for s in CAL_SIZES if s <= len(rows)] or [CAL_SIZES[0]])
        d["calibration_size"] = size
        d["extrapolated"] = len(rows) < CAL_SIZES[0]
        d["residual_interpretable"] = g[str(size)]["residual_interpretable"]
        d["attribution_interpretable"] = g[str(size)]["attribution_interpretable"]
        results[cls] = d
        print(cls, len(rows), d["collapsed"]["label"], "R", d["collapsed"]["R"], flush=True)
    manifest = {"script": "code/20_v101_variant_test.py", "protocol": "V101_PROTOCOL.md", "seed": SEED,
                "bootstrap": BOOT, "eps": EPS,
                "sha256": {str(p.relative_to(vd.ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in [vd.ROOT / "V101_PROTOCOL.md", Path(__file__).resolve(),
                                     OUT / "mapping.json", vd.ROOT / "data/mechanisms/voyn_101.txt"]}}
    (OUT / "variant_test.json").write_text(json.dumps({"manifest": manifest, "sets": results}, indent=1))


if __name__ == "__main__":
    main()
