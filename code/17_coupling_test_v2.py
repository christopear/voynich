"""Coupling-aware terminal-alternation test, version 2 (overnight run).

Specification: COUPLING_TEST_V2_PROTOCOL.md. CPU-parallel over calibration tasks.

Run (full):  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --locked python code/17_coupling_test_v2.py
Run (smoke): ... code/17_coupling_test_v2.py --smoke --out /tmp/smoke   (development check only)
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
import mechanism_models as mm
import slot_cipher as sc

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DEFAULT_OUT = ROOT / "results" / "coupling_test_v2_2026-09-25"
ARMS = ("k100", "k50", "k200", "top30")
PRIMARY = "k100"
CIPHER_FINALS = set("ynlrm")
VOYNICH_FINALS = set("nlr")
SUBSET = 30
N_SUBSETS = 200

_G: dict = {}


def _load_m13():
    spec = importlib.util.spec_from_file_location("m13", Path(__file__).with_name("13_equivalence_classes.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def _init():
    m13 = _load_m13()
    template = m13.frontier.load_lines(DATA / "ZL3b-n.txt")
    n = sum(len(ln["words"]) for ln in template)
    _G.update(m13=m13, template=template, training=mm.Training(template),
              syllables=sc.syllable_stream((DATA / "latin_alfonsi.txt").read_text(encoding="utf-8", errors="replace"))[:n])


def xmap_for(arm, lines):
    if arm == "top30":
        return v2.identity_map(lines), "*"
    return v2.neighbour_classes(lines, int(arm[1:])), "rare"


def calibration_task(arm, beta, seed, smoke):
    if not _G:
        _init()
    cfg = sc.Config(10, 1.0, beta)
    book = sc.SharedCoreCodeBook(Counter(_G["syllables"]), _G["training"], cfg, seed)
    words = sc.encipher(_G["syllables"], book, _G["training"].edge, cfg, seed + 5000)
    lines = [[w["word"] if w["clean"] else None for w in ln["words"]] for ln in mm.apply_template(_G["template"], words)]
    xmap, default = xmap_for(arm, lines)
    occ = v2.Occurrences(lines)
    pairs = ct.same_stem_pairs(occ, CIPHER_FINALS)
    kinds = {"same_unit": [p for p in pairs if book.decode[p[0]] == book.decode[p[1]]],
             "distinct_unit": [p for p in pairs if book.decode[p[0]] != book.decode[p[1]]]}
    rows = []
    for kind, ps in kinds.items():
        if smoke:
            ps = ps[:5]
        for a, b in ps:
            r = v2.score_pair(occ, xmap, default, a, b, n_ref=3 if smoke else 20, reps=50 if smoke else v2.REPS)
            r.pop("refs")
            rows.append({"arm": arm, "beta": beta, "seed": seed, "kind": kind, **r})
    return rows


def voynich_task(name, smoke):
    if not _G:
        _init()
    m13 = _G["m13"]
    path = DATA / "ZL3b-n.txt" if name == "zl" else DATA / "mechanisms" / "IT2a-n.txt"
    lines = m13.ivtff_lines(path)
    xmap, default = xmap_for(PRIMARY, lines)
    occ = v2.Occurrences(lines)
    pairs = ct.same_stem_pairs(occ, VOYNICH_FINALS)
    if smoke:
        pairs = pairs[:4]
    return name, [v2.score_pair(occ, xmap, default, a, b, n_ref=3 if smoke else 20,
                                reps=50 if smoke else v2.REPS, keep_ref_null=True) for a, b in pairs]


def summarize(rows):
    same = [r for r in rows if r["kind"] == "same_unit"]; dist = [r for r in rows if r["kind"] == "distinct_unit"]
    pct = lambda rs: float(np.median([r["ref_percentile"] for r in rs if r["ref_percentile"] is not None])) if rs else None
    auc = lambda key: float(roc_auc_score([0] * len(same) + [1] * len(dist), [key(r) for r in same + dist])) if same and dist else None
    rng = random.Random(v2.SEED)
    def subset_rate(rs):
        if len(rs) < SUBSET:
            return None
        return float(np.mean([v2.pooled(rng.sample(rs, SUBSET))["p"] < 0.05 for _ in range(N_SUBSETS)]))
    s = {"n_same": len(same), "n_distinct": len(dist),
         "same_sig_rate": float(np.mean([r["p"] < 0.05 for r in same])) if same else None,
         "distinct_sig_rate": float(np.mean([r["p"] < 0.05 for r in dist])) if dist else None,
         "auc_excess_distinct_vs_same": auc(lambda r: r["excess"]),
         "median_ref_percentile_same": pct(same), "median_ref_percentile_distinct": pct(dist),
         "naive_same_sig_rate": float(np.mean([r["naive"]["p"] < 0.05 for r in same])) if same else None,
         "naive_distinct_sig_rate": float(np.mean([r["naive"]["p"] < 0.05 for r in dist])) if dist else None,
         "pooled_subset_sig_rate_same": subset_rate(same), "pooled_subset_sig_rate_distinct": subset_rate(dist)}
    ok = lambda v, f: v is not None and f(v)
    s["C1"] = ok(s["same_sig_rate"], lambda v: v <= 0.10)
    s["C2"] = ok(s["distinct_sig_rate"], lambda v: v >= 0.50) and ok(s["auc_excess_distinct_vs_same"], lambda v: v >= 0.80)
    s["C3"] = ok(s["median_ref_percentile_same"], lambda v: v <= 25) and ok(s["median_ref_percentile_distinct"], lambda v: v >= 40)
    s["P1"] = ok(s["pooled_subset_sig_rate_same"], lambda v: v <= 0.10)
    s["P2"] = ok(s["pooled_subset_sig_rate_distinct"], lambda v: v >= 0.80)
    return s


def voynich_summary(rows):
    for r in rows:
        r["category"] = ct.category(r)
    pooled = v2.pooled(rows) if rows else None
    rng = random.Random(v2.SEED)
    with_refs = [r for r in rows if r["refs"]]
    pseudo = [v2.pooled([rng.choice(r["refs"]) for r in with_refs])["p"] < 0.05 for _ in range(N_SUBSETS)] if with_refs else []
    return {"pairs": len(rows), "pooled": pooled, "V_internal_power": float(np.mean(pseudo)) if pseudo else None,
            "median_ref_percentile": float(np.median([r["ref_percentile"] for r in rows if r["ref_percentile"] is not None])) if with_refs else None,
            "category_counts": Counter(r["category"] for r in rows),
            "sig_rate": float(np.mean([r["p"] < 0.05 for r in rows])) if rows else None,
            "naive_sig_rate": float(np.mean([r["naive"]["p"] < 0.05 for r in rows])) if rows else None}


def strip(r):
    out = {k: v for k, v in r.items() if k not in ("null_z", "refs")}
    if "refs" in r:
        out["refs"] = [{k: v for k, v in x.items() if k != "null_z"} for x in r["refs"]]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()
    seeds = (9001,) if args.smoke else tuple(range(301, 311))
    arms = ("k100", "top30") if args.smoke else ARMS
    args.out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    tasks = [(arm, beta, seed) for arm in arms for beta in (2.0, 0.0) for seed in seeds]
    rows = []
    with ProcessPoolExecutor(max_workers=args.workers, initializer=_init) as ex:
        futs = {ex.submit(calibration_task, *t, args.smoke): t for t in tasks}
        vfuts = {ex.submit(voynich_task, name, args.smoke): name for name in ("zl", "it")}
        for i, f in enumerate(as_completed(futs), 1):
            rows.extend(f.result())
            print(f"[{time.time() - t0:7.0f}s] calibration {futs[f]} done ({i}/{len(tasks)})", flush=True)
        vres = dict(f.result() for f in as_completed(vfuts))
    print(f"[{time.time() - t0:7.0f}s] voynich done", flush=True)

    rows.sort(key=lambda r: (r["arm"], r["beta"], r["seed"], r["kind"], r["a"], r["b"]))
    cal = {}
    for arm in arms:
        for beta in (2.0, 0.0):
            sel = [r for r in rows if r["arm"] == arm and r["beta"] == beta]
            cal[f"{arm}_beta{beta:g}"] = summarize(sel)
    prim = cal[f"{PRIMARY}_beta2"]
    gates = {"per_pair_calibration_passed": prim["C1"] and prim["C2"] and prim["C3"],
             "pooled_calibration_passed": prim["P1"] and prim["P2"]}
    (args.out / "calibration.json").write_text(json.dumps(
        {"gates": gates, "summaries": cal, "pairs": [strip(r) for r in rows]}, indent=1, default=str))

    vs = {name: voynich_summary(r) for name, r in vres.items()}
    zl, it = vs.get("zl"), vs.get("it")
    if not gates["pooled_calibration_passed"]:
        interp = "not interpreted: pooled calibration (P1-P2) failed"
    elif zl["pooled"]["p"] < 0.05:
        interp = "class carries residual context beyond boundary glyphs (against pure edge-conditioned homophony)"
    elif zl["V_internal_power"] is not None and zl["V_internal_power"] >= 0.80 and it["pooled"]["p"] >= 0.05:
        interp = "class behaves like edge-conditioned variants (compatible with homophony, not proof)"
    elif zl["V_internal_power"] is None or zl["V_internal_power"] < 0.80:
        interp = "underpowered: no conclusion"
    else:
        interp = "ZL and IT disagree: transcription-sensitive, no conclusion"
    if (zl["pooled"]["p"] < 0.05) != (it["pooled"]["p"] < 0.05) and gates["pooled_calibration_passed"]:
        interp = "ZL and IT disagree: transcription-sensitive, no conclusion"
    (args.out / "voynich.json").write_text(json.dumps(
        {"gates": gates, "interpretation": interp,
         "per_pair_categories_interpretable": gates["per_pair_calibration_passed"],
         "summary": vs, "pairs": {k: [strip(r) for r in v] for k, v in vres.items()}}, indent=1, default=str))

    manifest = {"script": "code/17_coupling_test_v2.py", "protocol": "COUPLING_TEST_V2_PROTOCOL.md",
                "smoke": args.smoke, "workers": args.workers, "cpu_count": os.cpu_count(),
                "platform": platform.platform(), "python": platform.python_version(),
                "numpy": np.__version__, "scipy": scipy.__version__, "sklearn": sklearn.__version__,
                "seeds": seeds, "arms": arms, "reps": 50 if args.smoke else v2.REPS,
                "elapsed_seconds": round(time.time() - t0),
                "inputs_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in [
                    DATA / "ZL3b-n.txt", DATA / "mechanisms/IT2a-n.txt", DATA / "latin_alfonsi.txt"]}}
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps({"gates": gates, "interpretation": interp}, indent=2), flush=True)


if __name__ == "__main__":
    main()
