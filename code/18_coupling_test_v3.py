"""Coupling-aware terminal-alternation test, version 3 (cross-fitted classes).

Specification: COUPLING_TEST_V3_PROTOCOL.md. CPU-parallel; intended for the
user's machine via overnight/run_v3.sh.

Run (full):  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --locked python code/18_coupling_test_v3.py --workers N
Run (smoke): ... code/18_coupling_test_v3.py --smoke --out /tmp/smoke   (development check only)
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import random
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import scipy
import sklearn
from sklearn.metrics import roc_auc_score

import coupling_test as ct
import coupling_test_v2 as v2
import coupling_test_v3 as v3
import mechanism_models as mm
import slot_cipher as sc

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DEFAULT_OUT = ROOT / "results" / "coupling_test_v3_2026-09-26"
ARMS = ("k100", "k50", "top30")
PRIMARY = "k100"
CIPHER_FINALS = set("ynlrm")
VOYNICH_FINALS = set("nlr")
SUBSET = 30
N_SUBSETS = 200
B0_LIMIT = 0.08

_G: dict = {}


def _init():
    spec = importlib.util.spec_from_file_location("m13", Path(__file__).with_name("13_equivalence_classes.py"))
    m13 = importlib.util.module_from_spec(spec); spec.loader.exec_module(m13)
    template = m13.frontier.load_lines(DATA / "ZL3b-n.txt")
    n = sum(len(ln["words"]) for ln in template)
    _G.update(frontier=m13.frontier, template=template, training=mm.Training(template),
              zl_folds=v3.page_folds([ln["page"] for ln in template]),
              syllables=sc.syllable_stream((DATA / "latin_alfonsi.txt").read_text(encoding="utf-8", errors="replace"))[:n])


def paged(laid):
    return [(ln["page"], [w["word"] if w["clean"] else None for w in ln["words"]]) for ln in laid]


def calibration_task(arm, beta, seed, smoke):
    if not _G:
        _init()
    cfg = sc.Config(10, 1.0, beta)
    book = sc.SharedCoreCodeBook(Counter(_G["syllables"]), _G["training"], cfg, seed)
    words = sc.encipher(_G["syllables"], book, _G["training"].edge, cfg, seed + 5000)
    occ = v3.CrossFitOccurrences(paged(mm.apply_template(_G["template"], words)), arm, _G["zl_folds"])
    pairs = ct.same_stem_pairs(occ, CIPHER_FINALS)
    kinds = {"same_unit": [p for p in pairs if book.decode[p[0]] == book.decode[p[1]]],
             "distinct_unit": [p for p in pairs if book.decode[p[0]] != book.decode[p[1]]]}
    rows = []
    for kind, ps in kinds.items():
        for a, b in (ps[:5] if smoke else ps):
            r = v2.score_pair(occ, None, None, a, b, n_ref=3 if smoke else 20, reps=50 if smoke else v2.REPS)
            r.pop("refs")
            rows.append({"arm": arm, "beta": beta, "seed": seed, "kind": kind, **r})
    return rows


def voynich_task(name, smoke):
    if not _G:
        _init()
    path = DATA / "ZL3b-n.txt" if name == "zl" else DATA / "mechanisms" / "IT2a-n.txt"
    occ = v3.CrossFitOccurrences(paged(_G["frontier"].load_lines(path)), PRIMARY)
    pairs = ct.same_stem_pairs(occ, VOYNICH_FINALS)
    if smoke:
        pairs = pairs[:4]
    return name, [v2.score_pair(occ, None, None, a, b, n_ref=3 if smoke else 20,
                                reps=50 if smoke else v2.REPS, keep_ref_null=True) for a, b in pairs]


def summarize(rows, smoke):
    same = [r for r in rows if r["kind"] == "same_unit"]; dist = [r for r in rows if r["kind"] == "distinct_unit"]
    mean = lambda xs: float(np.mean(xs)) if len(xs) else None
    pct = lambda rs: float(np.median([r["ref_percentile"] for r in rs if r["ref_percentile"] is not None])) if rs else None
    size = 5 if smoke else SUBSET
    def subset_rate(rs):
        subs = v3.disjoint_subsets(rs, size, N_SUBSETS)
        return (float(np.mean([v2.pooled(s)["p"] < 0.05 for s in subs])) if subs else None), len(subs)
    ps, ns = subset_rate(same); pd_, nd = subset_rate(dist)
    s = {"n_same": len(same), "n_distinct": len(dist),
         "same_mean_z": mean([r["z"] for r in same]), "same_z_se": float(np.std([r["z"] for r in same]) / np.sqrt(len(same))) if same else None,
         "same_sig_rate": mean([r["p"] < 0.05 for r in same]), "distinct_sig_rate": mean([r["p"] < 0.05 for r in dist]),
         "auc_excess_distinct_vs_same": float(roc_auc_score([0] * len(same) + [1] * len(dist), [r["excess"] for r in same + dist])) if same and dist else None,
         "median_ref_percentile_same": pct(same), "median_ref_percentile_distinct": pct(dist),
         "naive_same_sig_rate": mean([r["naive"]["p"] < 0.05 for r in same]),
         "naive_distinct_sig_rate": mean([r["naive"]["p"] < 0.05 for r in dist]),
         "pooled_disjoint_subset_sig_rate_same": ps, "pooled_disjoint_subsets_same": ns,
         "pooled_disjoint_subset_sig_rate_distinct": pd_, "pooled_disjoint_subsets_distinct": nd}
    ok = lambda v, f: v is not None and f(v)
    s["C1"] = ok(s["same_sig_rate"], lambda v: v <= 0.10)
    s["C2"] = ok(s["distinct_sig_rate"], lambda v: v >= 0.50) and ok(s["auc_excess_distinct_vs_same"], lambda v: v >= 0.80)
    s["C3"] = ok(s["median_ref_percentile_same"], lambda v: v <= 25) and ok(s["median_ref_percentile_distinct"], lambda v: v >= 40)
    s["P1"] = ok(ps, lambda v: v <= 0.10)
    s["P2"] = ok(pd_, lambda v: v >= 0.80)
    s["B0_this_regime"] = ok(s["same_mean_z"], lambda v: abs(v) <= B0_LIMIT)
    return s


def voynich_summary(rows):
    for r in rows:
        r["category"] = ct.category(r)
    rng = random.Random(v2.SEED)
    with_refs = [r for r in rows if r["refs"]]
    pseudo = [v2.pooled([rng.choice(r["refs"]) for r in with_refs])["p"] < 0.05 for _ in range(N_SUBSETS)] if with_refs else []
    return {"pairs": len(rows), "pooled": v2.pooled(rows) if rows else None,
            "V_internal_power": float(np.mean(pseudo)) if pseudo else None,
            "median_ref_percentile": float(np.median([r["ref_percentile"] for r in rows if r["ref_percentile"] is not None])) if with_refs else None,
            "mean_z": float(np.mean([r["z"] for r in rows])) if rows else None,
            "category_counts": Counter(r["category"] for r in rows),
            "sig_rate": float(np.mean([r["p"] < 0.05 for r in rows])) if rows else None,
            "naive_sig_rate": float(np.mean([r["naive"]["p"] < 0.05 for r in rows])) if rows else None}


def strip(r):
    out = {k: v for k, v in r.items() if k not in ("null_z", "refs")}
    if "refs" in r:
        out["refs"] = [{k: v for k, v in x.items() if k != "null_z"} for x in r["refs"]]
    return out


def interpret(gates, zl, it):
    if not gates["pooled_calibration_passed"]:
        return "not interpreted: pooled calibration (P1, P2, B0) failed"
    zsig, isig = zl["pooled"]["p"] < 0.05, it["pooled"]["p"] < 0.05
    if zsig != isig:
        return "ZL and IT disagree: transcription-sensitive, no conclusion"
    if zsig:
        return "class carries residual context beyond boundary glyphs (against pure edge-conditioned homophony)"
    if zl["V_internal_power"] is None or zl["V_internal_power"] < 0.80:
        return "underpowered: no conclusion"
    return "class behaves like edge-conditioned variants of one unit (compatible with homophony, not proof)"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()
    seeds = (9101,) if args.smoke else tuple(range(301, 311))
    arms = ("k100", "top30") if args.smoke else ARMS
    args.out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    tasks = [(arm, beta, seed) for arm in arms for beta in (2.0, 0.0) for seed in seeds]
    rows = []
    with ProcessPoolExecutor(max_workers=args.workers, initializer=_init) as ex:
        vfuts = {ex.submit(voynich_task, name, args.smoke): name for name in ("zl", "it")}
        futs = {ex.submit(calibration_task, *t, args.smoke): t for t in tasks}
        for i, f in enumerate(as_completed(futs), 1):
            rows.extend(f.result())
            print(f"[{time.time() - t0:7.0f}s] calibration {futs[f]} done ({i}/{len(tasks)})", flush=True)
        vres = dict(f.result() for f in as_completed(vfuts))
    print(f"[{time.time() - t0:7.0f}s] voynich done", flush=True)

    rows.sort(key=lambda r: (r["arm"], r["beta"], r["seed"], r["kind"], r["a"], r["b"]))
    cal = {f"{arm}_beta{beta:g}": summarize([r for r in rows if r["arm"] == arm and r["beta"] == beta], args.smoke)
           for arm in arms for beta in (2.0, 0.0)}
    p2, p0 = cal[f"{PRIMARY}_beta2"], cal[f"{PRIMARY}_beta0"]
    b0 = p2["B0_this_regime"] and p0["B0_this_regime"]
    gates = {"B0_leakage_check": b0,
             "per_pair_calibration_passed": p2["C1"] and p2["C2"] and p2["C3"] and b0,
             "pooled_calibration_passed": p2["P1"] and p2["P2"] and b0}
    (args.out / "calibration.json").write_text(json.dumps(
        {"gates": gates, "summaries": cal, "pairs": [strip(r) for r in rows]}, indent=1, default=str))

    vs = {name: voynich_summary(r) for name, r in vres.items()}
    interp = interpret(gates, vs["zl"], vs["it"])
    (args.out / "voynich.json").write_text(json.dumps(
        {"gates": gates, "interpretation": interp,
         "per_pair_categories_interpretable": gates["per_pair_calibration_passed"],
         "summary": vs, "pairs": {k: [strip(r) for r in v] for k, v in vres.items()}}, indent=1, default=str))

    manifest = {"script": "code/18_coupling_test_v3.py", "protocol": "COUPLING_TEST_V3_PROTOCOL.md",
                "smoke": args.smoke, "workers": args.workers, "cpu_count": os.cpu_count(),
                "platform": platform.platform(), "python": platform.python_version(),
                "numpy": np.__version__, "scipy": scipy.__version__, "sklearn": sklearn.__version__,
                "seeds": seeds, "arms": arms, "folds": v3.FOLDS, "reps": 50 if args.smoke else v2.REPS,
                "elapsed_seconds": round(time.time() - t0),
                "inputs_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in [
                    DATA / "ZL3b-n.txt", DATA / "mechanisms/IT2a-n.txt", DATA / "latin_alfonsi.txt"]}}
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps({"gates": gates, "interpretation": interp}, indent=2), flush=True)


if __name__ == "__main__":
    main()
